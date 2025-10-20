from src.schemas.agent_output import MessageToRoleAgent
from src.prompts.role_agent import prompt
from src.core.settings import settings

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
import json

model = OpenAIChatModel('gpt-4o-mini', provider=OpenAIProvider(api_key=settings.openai_api_key))

agent = Agent(
    model=model,
    system_prompt=prompt,
    output_type=list[MessageToRoleAgent]
)

async def process_transcript(raw_messages: list[str]) -> list[MessageToRoleAgent]:
    print(raw_messages)
    joined = "\n".join(raw_messages)
    with open("output/messages.txt", "w", encoding="utf-8") as f:
        f.write(joined)
    result = await agent.run(f"Here is the conversation:\n{joined}")
    with open("output/role_messages.txt", "w", encoding="utf-8") as f:
        f.write(json.dumps([msg.model_dump() for msg in result.output], ensure_ascii=False, indent=2))
    return result.output