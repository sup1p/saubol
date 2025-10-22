from src.agents.role_agent import process_transcript
from src.agents.summary_agent import generate_summary_of_transcript_with_roles
from src.utils.file_saver import create_medical_md
from src.schemas.agent_output import MessageToRoleAgent

async def generate_summary(transcript: list[MessageToRoleAgent],  header_data: dict, client: str = "default"):
    summary = await generate_summary_of_transcript_with_roles(transcript)
    create_medical_md(summary, "output", client=client, header_data=header_data)

    return summary