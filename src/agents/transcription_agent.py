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
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    session = AgentSession(
        stt=openai.STT(
            model="gpt-4o-transcribe"
        ),
        # llm="openai/gpt-4.1-mini",
        
        # tts="cartesia/sonic-2:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
 
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )
    
    # store session transcripts for summary
    sessions: dict[str, list[str]] = {} 
    
    @session.on("user_input_transcribed")
    def _on_user_input_transcribed(ev: UserInputTranscribedEvent) -> None:
        try:
            
            participant = ctx.room.participants.get(ev.participant_sid)
            participant_name = participant.name if participant else "Unknown"


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
            # защита от падения сессии из-за ошибки логирования
            print(f"[STT handler error] {e}")
            asyncio.create_task(send_text_to_channel(f"[STT handler error] {e}", channel="lk.chat"))
            
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
    
    async def send_text_to_channel(message: str, channel: str):
        await ctx.room.local_participant.send_text(
            message,
            topic=channel
        )
    
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm, drain_timeout=5))
