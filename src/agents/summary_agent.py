from src.schemas.agent_output import MessageToRoleAgent 
from src.schemas.protocol import MedicalProtocol
from src.prompts.summary_agent import prompt
from src.services.mkb_10 import (
    get_mkb_classes,
    get_mkb_class_blocks,
    get_mkb_class_block_elements,
    get_mkb_class_block_element_details,
)
from src.core.settings import settings

from output.mock_conversation import mock_conversation

from pydantic_ai import Agent, ModelSettings, Tool
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
import json
import asyncio

model = OpenAIChatModel('gpt-4o-mini', provider=OpenAIProvider(api_key=settings.openai_api_key))

agent = Agent(
    model=model,
    instructions=prompt,
    retries=3,
    tools=[
        Tool(get_mkb_classes, takes_ctx=False), 
        Tool(get_mkb_class_blocks, takes_ctx=False), 
        Tool(get_mkb_class_block_elements, takes_ctx=False), 
        Tool(get_mkb_class_block_element_details, takes_ctx=False)
    ],
    output_type=MedicalProtocol,
    model_settings=ModelSettings(temperature=0.2)
)

async def generate_summary_of_transcript_with_roles(transcript: list[MessageToRoleAgent]):
    joined = "\n".join([f"{msg.role}: {msg.content}" for msg in transcript])
    result = await agent.run(f"\nВот транскрибированный диалог врача и пациента:\n{joined}")
    with open("output/summary.txt", "w", encoding="utf-8") as f:
        f.write(json.dumps(result.output.model_dump(mode='json'), ensure_ascii=False, indent=2))
    return result.output

async def main():
    result = await generate_summary_of_transcript_with_roles(mock_conversation)
    print(result)
    
if __name__ == "__main__":
    asyncio.run(main())
