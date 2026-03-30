import os
from typing import Any
from app.agents.base import BaseAgent
from app.config import settings


class CoordinatorAgent(BaseAgent):
    def __init__(self, agent_id: str = "coordinator"):
        super().__init__(agent_id, "coordinator")
        self.model = settings.openai_model
        self.temperature = settings.openai_temperature
        self.max_tokens = settings.openai_max_tokens

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        self.set_state("thinking", "Processing user request", 0.1)

        messages = input_data.get("messages", [])
        context = input_data.get("context", {})
        tools = input_data.get("tools", [])

        system_prompt = (
            "You are the Coordinator Agent in the Liminal Vibe Engineering platform. "
            "You help users accomplish tasks by delegating to specialized SubAgents and tools. "
            "You have access to the following tools: " + ", ".join(tools) + ". "
            "Always be helpful, concise, and action-oriented. "
            "When a user asks you to do something that requires file operations or bash commands, "
            "use the appropriate tool. "
            "The current session context is: " + str(context)
        )

        self.set_state("executing", "Calling LLM", 0.5)

        response = await self._call_llm(system_prompt, messages)

        self.set_state("idle", "Done", 1.0)

        return {
            "response": response,
            "tools_used": [],
            "artifacts": [],
        }

    async def _call_llm(self, system_prompt: str, messages: list[dict]) -> str:
        api_key = settings.openai_api_key
        if not api_key:
            return "Coordinator is running but no OpenAI API key is configured. Please set OPENAI_API_KEY in your environment."

        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key)
            all_messages = [{"role": "system", "content": system_prompt}] + messages
            completion = await client.chat.completions.create(
                model=self.model,
                messages=all_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return completion.choices[0].message.content or ""
        except Exception as e:
            return f"Error calling LLM: {str(e)}"
