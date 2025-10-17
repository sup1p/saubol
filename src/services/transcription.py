"""
Real-time transcription service for LiveKit audio streams using LiveKit Agents framework
"""
from src.core.settings import settings
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
from livekit import agents, rtc
from livekit.plugins import openai
from datetime import datetime
import asyncio
import logging
import os

logger = logging.getLogger("transcription-agent")

# Global dictionary to store active agent workers
active_agents = {}


class TranscriptionAgentManager:
    """
    Manager for LiveKit Transcription Agents.
    Handles starting and stopping agents for specific rooms.
    """
    
    @staticmethod
    async def start_agent_for_room(room_name: str) -> bool:
        """
        Start a transcription agent for a specific room using Worker API.
        
        Args:
            room_name: Name of the room to start transcription for
            
        Returns:
            True if agent started successfully, False otherwise
        """
        if room_name in active_agents:
            logger.warning(f"Agent already running for room: {room_name}")
            return False
        
        try:
            # Set up environment variables for LiveKit Agents
            os.environ["LIVEKIT_URL"] = settings.livekit_url
            os.environ["LIVEKIT_API_KEY"] = settings.livekit_api_key
            os.environ["LIVEKIT_API_SECRET"] = settings.livekit_api_secret
            os.environ["OPENAI_API_KEY"] = settings.openai_api_key
            
            # Create worker task
            async def run_worker():
                try:
                    worker = WorkerOptions(
                        entrypoint_fnc=create_entrypoint(room_name),
                        api_key=settings.livekit_api_key,
                        api_secret=settings.livekit_api_secret,
                        ws_url=settings.livekit_url,
                    )
                    
                    # Import the worker runner
                    from livekit.agents import Worker
                    
                    # Create and run the worker
                    w = Worker(worker)
                    await w.run()
                    
                except asyncio.CancelledError:
                    logger.info(f"Worker cancelled for room: {room_name}")
                    raise
                except Exception as e:
                    logger.error(f"Worker error for room {room_name}: {e}")
                    if room_name in active_agents:
                        del active_agents[room_name]
            
            task = asyncio.create_task(run_worker())
            
            # Store the task and context reference
            active_agents[room_name] = {
                'task': task,
                'room_context': None,  # Will be set when the agent connects
                'stop_event': asyncio.Event()  # Event to signal agent to stop
            }
            
            logger.info(f"Started transcription worker for room: {room_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start agent for room {room_name}: {e}")
            return False
    
    @staticmethod
    async def stop_agent_for_room(room_name: str) -> bool:
        """
        Stop the transcription agent for a specific room.
        
        Args:
            room_name: Name of the room to stop transcription for
            
        Returns:
            True if agent stopped successfully, False otherwise
        """
        if room_name not in active_agents:
            logger.warning(f"No agent running for room: {room_name}")
            return False
        
        try:
            agent_info = active_agents[room_name]
            task = agent_info['task']
            stop_event = agent_info['stop_event']
            
            # Signal the agent to stop
            logger.info(f"Signalling agent to stop for room: {room_name}")
            stop_event.set()
            
            # Wait a moment for the agent to process the stop signal
            await asyncio.sleep(0.1)
            
            # Cancel the worker task
            logger.info(f"Cancelling transcription task for room: {room_name}")
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                logger.info(f"Task cancelled successfully for room: {room_name}")
            except Exception as e:
                logger.error(f"Error while stopping task for room {room_name}: {e}")
            
            # Remove from active agents
            if room_name in active_agents:
                del active_agents[room_name]
            
            logger.info(f"Stopped transcription agent for room: {room_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop agent for room {room_name}: {e}")
            return False
    
    @staticmethod
    def get_active_rooms() -> list:
        """Get list of rooms with active transcription agents."""
        return list(active_agents.keys())


def create_entrypoint(target_room: str):
    """
    Create a room-specific entrypoint function.
    
    Args:
        target_room: The specific room this agent should handle
        
    Returns:
        Entrypoint function for the worker
    """
    async def entrypoint(ctx: JobContext):
        """
        Room-specific entrypoint that only processes if the context room matches target room.
        """
        # Only process if this is the target room
        if ctx.room.name != target_room:
            logger.info(f"Agent for room '{target_room}' ignoring job for room '{ctx.room.name}'")
            return
        
        logger.info(f"Agent starting transcription for room: {target_room}")
        
        # Store the context in active_agents for shutdown capability
        if target_room in active_agents:
            active_agents[target_room]['room_context'] = ctx
        
        # Create transcription agent instance
        agent = TranscriptionAgent()
        
        # Start the transcription process
        await agent.start_transcription(ctx)
    
    return entrypoint


class TranscriptionAgent:
    """
    LiveKit Agent for real-time audio transcription using OpenAI Whisper.
    Uses the official LiveKit Agents framework with OpenAI STT plugin.
    """
    
    def __init__(self):
        """Initialize the transcription agent."""
        pass
    
    async def start_transcription(self, ctx: JobContext) -> None:
        """
        Main entrypoint for the transcription agent.
        Uses LiveKit Agents framework to handle audio streams.
        
        Args:
            ctx: Job context from LiveKit Worker API
        """
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        room = ctx.room
        
        logger.info(f"Agent connected to room: {room.name}")
        logger.info(f"Room participants count: {len(room.remote_participants)}")
        
        # Create STT instance - it will use the http session from job context
        stt = openai.STT(
            model="whisper-1",
            language="en",
        )
        
        # Dictionary to store active transcription tasks
        transcription_tasks = {}
        
        async def transcribe_track(track: rtc.Track, participant: rtc.RemoteParticipant):
            """Transcribe audio from a specific track"""
            logger.info(f"Starting transcription for track from participant: {participant.identity}")
            
            try:
                # Create audio stream from track
                audio_stream = rtc.AudioStream(track)
                stt_stream = stt.stream()
                
                # Start processing audio frames
                async def process_audio():
                    try:
                        async for event in audio_stream:
                            stt_stream.push_frame(event.frame)
                    except Exception as e:
                        logger.error(f"Error processing audio frames: {e}")
                        raise
                
                # Handle transcription results
                async def handle_transcription():
                    try:
                        async for event in stt_stream:
                            if event.type == agents.stt.SpeechEventType.FINAL_TRANSCRIPT:
                                text = event.alternatives[0].text if event.alternatives else ""
                                if text.strip():
                                    timestamp = datetime.now().strftime('%H:%M:%S')
                                    message = f"[{timestamp}] {participant.identity}: {text}"
                                    
                                    logger.info(f"Transcription: {text}")
                                    
                                    # Send transcription to the room
                                    await room.local_participant.publish_data(
                                        message.encode('utf-8'), 
                                        topic="transcription"
                                    )
                                    await room.local_participant.send_text(
                                        message, 
                                        topic="lk.chat"
                                    )
                                    
                                    print(f"Sent transcription message: {message}")
                    except Exception as e:
                        logger.error(f"Error handling transcription: {e}")
                        raise
                
                # Run both tasks concurrently
                await asyncio.gather(
                    process_audio(),
                    handle_transcription(),
                    return_exceptions=True
                )
                
            except asyncio.CancelledError:
                logger.info(f"Transcription cancelled for {participant.identity}")
                raise
            except Exception as e:
                logger.error(f"Transcription error for {participant.identity}: {e}")
            finally:
                # Close the STT stream properly
                try:
                    await stt_stream.aclose()
                except Exception as e:
                    logger.debug(f"Error closing STT stream for {participant.identity}: {e}")
        
        # Handle track subscriptions
        @room.on("track_subscribed")
        def on_track_subscribed(
            track: rtc.Track,
            publication: rtc.RemoteTrackPublication,
            participant: rtc.RemoteParticipant,
        ):
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                logger.info(f"Subscribed to audio track from {participant.identity}")
                
                # Start transcription for this track
                task_key = f"{participant.sid}_{track.sid}"
                transcription_tasks[task_key] = asyncio.create_task(
                    transcribe_track(track, participant)
                )
        
        # Handle track unsubscriptions
        @room.on("track_unsubscribed")
        def on_track_unsubscribed(
            track: rtc.Track,
            publication: rtc.RemoteTrackPublication,
            participant: rtc.RemoteParticipant,
        ):
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                logger.info(f"Unsubscribed from audio track from {participant.identity}")
                
                # Cancel transcription task for this track
                task_key = f"{participant.sid}_{track.sid}"
                if task_key in transcription_tasks:
                    transcription_tasks[task_key].cancel()
                    del transcription_tasks[task_key]
        
        # Handle participant connections
        @room.on("participant_connected")
        def on_participant_connected(participant: rtc.RemoteParticipant):
            logger.info(f"New participant connected: {participant.identity}")
        
        # Handle participant disconnections
        @room.on("participant_disconnected")
        def on_participant_disconnected(participant: rtc.RemoteParticipant):
            logger.info(f"Participant disconnected: {participant.identity}")
            
            # Cancel all transcription tasks for this participant
            to_cancel = []
            for task_key in transcription_tasks:
                if task_key.startswith(participant.sid):
                    to_cancel.append(task_key)
            
            for task_key in to_cancel:
                transcription_tasks[task_key].cancel()
                del transcription_tasks[task_key]
        
        # Process existing participants and their tracks
        for participant in room.remote_participants.values():
            logger.info(f"Found existing participant: {participant.identity}")
            for publication in participant.track_publications.values():
                if publication.track and publication.track.kind == rtc.TrackKind.KIND_AUDIO:
                    logger.info(f"Found existing audio track from {participant.identity}")
                    task_key = f"{participant.sid}_{publication.track.sid}"
                    transcription_tasks[task_key] = asyncio.create_task(
                        transcribe_track(publication.track, participant)
                    )
        
        # Keep the agent running
        logger.info("Transcription agent is ready and waiting for audio...")
        
        # Get stop event for this room
        stop_event = None
        room_name = room.name
        if room_name in active_agents:
            stop_event = active_agents[room_name]['stop_event']
        
        try:
            if stop_event:
                # Wait for either cancellation or stop signal
                await stop_event.wait()
                logger.info(f"Stop signal received for room: {room_name}")
            else:
                # Fallback to indefinite wait if no stop event
                await asyncio.Event().wait()
        except asyncio.CancelledError:
            logger.info("Transcription agent cancelled, cleaning up...")
            raise
        finally:
            # Cleanup transcription tasks
            for task in transcription_tasks.values():
                if not task.done():
                    task.cancel()
            
            # Wait for tasks to finish cancellation
            if transcription_tasks:
                try:
                    await asyncio.gather(*transcription_tasks.values(), return_exceptions=True)
                except Exception as e:
                    logger.error(f"Error waiting for tasks to cancel: {e}")
            
            # Perform proper shutdown
            try:
                logger.info(f"Performing shutdown for room: {room_name}")
                await ctx.shutdown()
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
            
            # Remove from active agents registry
            if room_name in active_agents:
                del active_agents[room_name]
                logger.info(f"Removed agent for room {room_name} from active registry")


# Default entrypoint for running the agent standalone
async def entrypoint(ctx: JobContext):
    """
    Main entrypoint for the LiveKit Agent.
    This function is called when the agent connects to a room.
    """
    logger.info(f"Agent starting for room: {ctx.room.name}")
    
    # Create transcription agent instance
    agent = TranscriptionAgent()
    
    # Start the transcription process
    await agent.start_transcription(ctx)


# For running as standalone worker
if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))