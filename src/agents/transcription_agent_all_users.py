import logging
import sys
import os
import asyncio
from datetime import datetime
import json

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.services.one_user_pipeline import generate_summary

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    WorkerOptions,
    cli,
    metrics,
    UserInputTranscribedEvent
)
from livekit.plugins import noise_cancellation, silero, openai
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit import rtc

logger = logging.getLogger("agent")

load_dotenv(".env")


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a helpful voice AI assistant. The user is interacting with you via voice, even if you perceive the conversation as text.
            You eagerly assist users with their questions by providing information from your extensive knowledge.
            Your responses are concise, to the point, and without any complex formatting or punctuation including emojis, asterisks, or other symbols.
            You are curious, friendly, and have a sense of humor.""",
        )

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=openai.STT(model="gpt-4o-transcribe"),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    sessions: dict[str, list[str]] = {}

    @session.on("user_input_transcribed")
    def _on_user_input_transcribed(ev: UserInputTranscribedEvent) -> None:
        try:
            participant = next(
                (p for p in ctx.room.remote_participants.values() if getattr(p, "sid", None) == getattr(ev, "participant_sid", None)),
                None
            )
            participant_name = getattr(participant, "name", None) or getattr(participant, "identity", None) or "Unknown"

            room_name = ctx.job.room.name
            sessions.setdefault(room_name, [])
            print(f"[STT] Session ID: {room_name}, is_final: {getattr(ev, 'is_final', 'unknown')}")
            if getattr(ev, "is_final", False):
                sessions[room_name].append(ev.transcript)
                print(f"[STT final] Added to session {room_name}: {ev.transcript}")
                print(f"[STT] Total messages in session {room_name}: {len(sessions[room_name])}")
                asyncio.create_task(send_text_to_channel(f"[Username: {participant_name}] {ev.transcript}", channel="lk.chat"))
            else:
                print(f"[STT intermediate] {ev.transcript}")
                asyncio.create_task(send_text_to_channel(f"[STT intermediate] {ev.transcript}", channel="lk.chat"))
        except Exception as e:
            print(f"[STT handler error] {e}")
            asyncio.create_task(send_text_to_channel(f"[STT handler error] {e}", channel="lk.chat"))


    async def send_text_to_channel(message: str, channel: str):
        await ctx.room.local_participant.send_text(message, topic=channel)

    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)
        
    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)
    
    async def summarize_and_generate():
        room_name = ctx.job.room.name
        print(f"Available sessions: {list(sessions.keys())}")
        print(f"Looking for session: {room_name}")

        if room_name in sessions and sessions[room_name]:
            data = sessions.pop(room_name)
            print(f"Found {len(data)} messages for session {room_name}")

            header_data = {
                "report_date": datetime.now().strftime("%Y-%m-%d"),
                "doctor_name": "Dr. John Smith",
                "doctor_position": "Cardiologist",
                "institution": "City Hospital"
            }

            summary = await generate_summary(data, client=room_name, header_data=header_data)
            print(f"Summary for session {room_name}: {summary}")
        else:
            print(f"No data found for session {room_name} or session is empty")
            
    ctx.add_shutdown_callback(summarize_and_generate)

    # start agent session
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    # --- listeners/tasks registry ---
    listeners_tasks: dict[str, asyncio.Task] = {}  # key: publication.sid -> task
    listeners_lock = asyncio.Lock()  # чтобы безопасно модифицировать listeners_tasks

    async def _process_publication(pub: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
        try:
            # subscribe request (API supports set_subscribed)
            try:
                pub.set_subscribed(True)
            except Exception:
                pass

            # wait for pub.track to appear (polling; можно заменить wait_for_track_publication helper)
            timeout = 10.0
            waited = 0.0
            while pub.track is None and waited < timeout:
                await asyncio.sleep(0.05)
                waited += 0.05

            if pub.track is None:
                print(f"[WARN] track not available for publication {pub.sid} (participant={participant.identity})")
                async with listeners_lock:
                    listeners_tasks.pop(pub.sid, None)
                return

            track = pub.track
            identity = participant.identity or getattr(participant, "name", None) or getattr(participant, "sid", None)

            audio_stream = rtc.AudioStream.from_track(
                track=track,
                sample_rate=16000,
                num_channels=1,
                noise_cancellation=noise_cancellation.BVC(),
            )

            # per-user VAD + per-user STT stream
            vad_stream = ctx.proc.userdata["vad"].stream()
            stt_plugin = openai.STT(model="gpt-4o-transcribe")
            stt_stream = stt_plugin.stream()

            async def _forward_input():
                try:
                    async for frame_event in audio_stream:
                        frame = frame_event.frame
                        try:
                            vad_stream.push_frame(frame)
                        except Exception:
                            pass
                        try:
                            stt_stream.push_frame(frame)
                        except Exception:
                            pass
                finally:
                    # graceful close
                    try:
                        await stt_stream.aclose()
                    except Exception:
                        pass
                    try:
                        vad_stream.close()
                    except Exception:
                        # VADStream may have close() or end_input(); use safe guard
                        try:
                            vad_stream.end_input()
                        except Exception:
                            pass
                    try:
                        await audio_stream.aclose()
                    except Exception:
                        pass

            async def _consume_stt():
                try:
                    async for ev in stt_stream:
                        etype = getattr(ev, "type", None)
                        is_final = getattr(ev, "is_final", None)
                        if is_final is None:
                            is_final = (etype and str(etype).lower().find("final") != -1)
                        text = None
                        if hasattr(ev, "alternatives") and ev.alternatives:
                            text = getattr(ev.alternatives[0], "text", None)
                        if text is None and hasattr(ev, "text"):
                            text = ev.text
                        if text is None:
                            continue

                        if is_final:
                            print(f"[TRANSCR FINAL] {identity}: {text}")
                            asyncio.create_task(send_text_to_channel(f"[{identity}] {text}", channel="lk.chat"))
                        else:
                            print(f"[TRANSCR PART] {identity}: {text}")
                except asyncio.CancelledError:
                    return
                except Exception as e:
                    logger.exception("STT consumer error for %s: %s", identity, e)

            forward_t = asyncio.create_task(_forward_input(), name=f"forward_{pub.sid}")
            consumer_t = asyncio.create_task(_consume_stt(), name=f"stt_consume_{pub.sid}")

            # keep them until finished/cancelled
            await asyncio.gather(forward_t, consumer_t)
        except asyncio.CancelledError:
            return
        except Exception:
            logger.exception("Error in processing publication %s for %s", getattr(pub, "sid", "<no-sid>"), getattr(participant, "identity", "<no-id>"))
        finally:
            async with listeners_lock:
                listeners_tasks.pop(getattr(pub, "sid", None), None)

    # --- room-level handlers: register ONCE ---
    @ctx.room.on("participant_connected")
    def _on_participant_connected(participant: rtc.RemoteParticipant):
        # start processing any existing audio publications for the participant
        for pub in participant.track_publications.values():
            if getattr(pub, "kind", None) == rtc.TrackKind.KIND_AUDIO:
                sid = getattr(pub, "sid", None)
                # prevent double-start
                if sid not in listeners_tasks:
                    listeners_tasks[sid] = asyncio.create_task(_process_publication(pub, participant))

    @ctx.room.on("participant_disconnected")
    def _on_participant_disconnected(participant: rtc.RemoteParticipant):
        # cancel tasks for this participant
        to_cancel = []
        for sid, task in list(listeners_tasks.items()):
            # if publication belongs to participant, cancel it
            # note: participant.track_publications keys are publication.sids
            if sid in participant.track_publications:
                to_cancel.append(sid)
        for sid in to_cancel:
            t = listeners_tasks.pop(sid, None)
            if t and not t.done():
                t.cancel()

    @ctx.room.on("track_published")
    def _on_track_published(publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
        if getattr(publication, "kind", None) == rtc.TrackKind.KIND_AUDIO:
            sid = getattr(publication, "sid", None)
            if sid not in listeners_tasks:
                listeners_tasks[sid] = asyncio.create_task(_process_publication(publication, participant))

    @ctx.room.on("track_subscribed")
    def _on_track_subscribed(track: rtc.Track, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
        # track available -> ensure we process publication if not already
        if getattr(publication, "kind", None) == rtc.TrackKind.KIND_AUDIO:
            sid = getattr(publication, "sid", None)
            if sid not in listeners_tasks:
                listeners_tasks[sid] = asyncio.create_task(_process_publication(publication, participant))

    # Handle already-present participants on start
    for participant in ctx.room.remote_participants.values():
        _on_participant_connected(participant)

    # session close event (instead of non-existent wait_closed())
    session_closed = asyncio.Event()

    @session.on("close")
    def _on_session_close(ev) -> None:
        try:
            session_closed.set()
        except Exception:
            pass

    try:
        await session_closed.wait()
    except asyncio.CancelledError:
        pass




if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm, drain_timeout=5))
