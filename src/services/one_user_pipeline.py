from src.agents.role_agent import process_transcript
from src.agents.summary_agent import generate_summary_of_transcript_with_roles
from src.utils.file_saver import create_medical_md

async def generate_summary(transcript: list[str], client: str = "default"):
    role_output = await process_transcript(transcript)
    summary = await generate_summary_of_transcript_with_roles(role_output)
    create_medical_md(summary, "output", client=client)
    
    return summary