from src.agents.role_agent import process_transcript
from src.agents.summary_agent import generate_summary_of_transcript_with_roles
from src.utils.file_saver import save_protocol_as_txt
from src.schemas.agent_output import MessageToRoleAgent

async def generate_summary(transcript: list[MessageToRoleAgent],  header_data: dict, client: str = "default"):
    summary = await generate_summary_of_transcript_with_roles(transcript)
    save_protocol_as_txt(summary, "output", header_data=header_data, client=client)

    return summary