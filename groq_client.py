from groq import Groq

class GroqClient:
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)

    def chat(self, messages: list[dict]) -> str:
        """Non-streaming: get full response"""
        system_prompt = {
            "role": "system",
            "content": (
                "You are a conversational voice assistant. "
                "Respond naturally in plain text sentences. "
                "NOTHING above 3-4 sentences AT MAX. "
                "Never output tables, lists, or markdown formatting."
            )
        }
        completion = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[system_prompt] + messages,
            temperature=0.8,
            max_completion_tokens=512,
            top_p=1,
            stream=False
        )
        return completion.choices[0].message.content.strip()

    async def stream_chat(self, messages: list[dict]):
        """Streaming: yield tokens as they arrive"""
        system_prompt = {
            "role": "system",
            "content": (
                "You are a conversational voice assistant. "
                "Respond naturally in plain text sentences. "
                "NOTHING above 3-4 sentences AT MAX. "
                "Never output tables, lists, or markdown formatting."
            )
        }
        completion = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[system_prompt] + messages,
            temperature=0.8,
            max_completion_tokens=512,
            top_p=1,
            stream=True
        )
        for chunk in completion:
            token = chunk.choices[0].delta.content or ""
            if token:
                yield token
