from src.schemas.agent_output import MessageToRoleAgent
from src.prompts.role_validator_agent import prompt
from src.core.settings import settings

from pydantic_ai import Agent, ModelSettings
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
import json
import asyncio
import random

model = OpenAIChatModel('gpt-4o-mini', provider=OpenAIProvider(api_key=settings.openai_api_key))

agent = Agent(
    model=model,
    instructions=prompt,
    retries=3,
    output_type=list[MessageToRoleAgent],
    model_settings=ModelSettings(temperature=0.2)
)

async def validate_enhance_role_messages(role_messages: list[MessageToRoleAgent]) -> list[MessageToRoleAgent]:
    chunk_size = 15
    results = []
    for i in range(0, len(role_messages), chunk_size):
        chunk = role_messages[i:i+chunk_size]
        result = await agent.run(json.dumps([msg.model_dump() for msg in chunk], ensure_ascii=False))
        results.extend(result.output)
        if i + chunk_size < len(role_messages):
            await asyncio.sleep(random.uniform(0.5, 2.0))
    return results