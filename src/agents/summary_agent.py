from src.schemas.agent_output import PDFSummary, MessageToRoleAgent
from src.prompts.summary_agent import prompt
from src.core.settings import settings

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
import json

model = OpenAIChatModel('gpt-4o-mini', provider=OpenAIProvider(api_key=settings.openai_api_key))

agent = Agent(
    model=model,
    system_prompt=prompt,
    output_type=PDFSummary
)

async def generate_summary_of_transcript_with_roles(transcript: list[MessageToRoleAgent]):
    joined = "\n".join([f"{msg.role}: {msg.content}" for msg in transcript])
    result = await agent.run(f"Here is the conversation with roles:\n{joined}")
    with open("output/summary.txt", "w", encoding="utf-8") as f:
        f.write(json.dumps(result.output.model_dump(), ensure_ascii=False, indent=2))
    return result.output