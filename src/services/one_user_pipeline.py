from src.agents.role_agent import process_transcript
from src.agents.role_validator_agent import validate_enhance_role_messages
from src.agents.summary_agent import generate_summary_of_transcript_with_roles
from src.utils.file_saver import save_protocol_as_txt
from src.schemas.agent_output import MessageToRoleAgent

import json

async def generate_summary(transcript: list[MessageToRoleAgent],  header_data: dict, client: str = "default"):
    with open("output/transcript.json", "w", encoding="utf-8") as f:
        f.write(json.dumps([msg.model_dump() for msg in transcript], ensure_ascii=False, indent=2))
        
    # validated_transcript = await validate_enhance_role_messages(transcript)
    
    # with open("output/validated_transcript.json", "w", encoding="utf-8") as f:
    #     f.write(json.dumps([msg.model_dump() for msg in validated_transcript], ensure_ascii=False, indent=2))
        
    summary = await generate_summary_of_transcript_with_roles(transcript)
    save_protocol_as_txt(summary, "output", header_data=header_data, client=client)

    return summary