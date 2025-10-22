from src.schemas.agent_output import MessageToRoleAgent
from src.prompts.role_agent import prompt
from src.core.settings import settings

from pydantic_ai import Agent, ModelSettings
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
import json

model = OpenAIChatModel('gpt-4o-mini', provider=OpenAIProvider(api_key=settings.openai_api_key))

agent = Agent(
    model=model,
    instructions=prompt,
    retries=3,
    output_type=list[MessageToRoleAgent],
    model_settings=ModelSettings(temperature=0.2)
)

async def process_transcript(raw_message: str, role_messages: list[MessageToRoleAgent]):
    print(raw_message)
    with open("output/messages.txt", "a", encoding="utf-8") as f:
        f.write(raw_message + "\n")
        
    payload = (
        "NEW_MESSAGE:\n" + raw_message + "\n\n" +
        "CONTEXT_JSON:\n" + json.dumps([msg.model_dump() for msg in role_messages], ensure_ascii=False)
    )
    
    result = await agent.run(payload)
    return result.output