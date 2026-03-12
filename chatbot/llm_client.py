"""
Thin wrapper around OpenAI / Gemini API.
Switchable via LLM_PROVIDER environment variable.
"""
import os


class LLMClient:
    def __init__(self, provider: str = None):
        self.provider = provider or os.getenv("LLM_PROVIDER", "openai")

    def chat(self, messages: list) -> str:
        """Send messages to the chosen LLM and return the response."""
        if self.provider == "openai":
            return self._call_openai(messages)
        elif self.provider == "gemini":
            return self._call_gemini(messages)
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

    def _call_openai(self, messages: list) -> str:
        from openai import OpenAI
        client = OpenAI()  # uses OPENAI_API_KEY env var
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            temperature=0.3,
        )
        return response.choices[0].message.content

    def _call_gemini(self, messages: list) -> str:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))

        # Convert OpenAI-style messages to Gemini format
        # Gemini uses 'user' and 'model' roles, system goes into first user message
        system_text = ""
        history = []
        for msg in messages:
            if msg["role"] == "system":
                system_text = msg["content"]
            elif msg["role"] == "user":
                content = msg["content"]
                if system_text and not history:
                    content = f"System instructions: {system_text}\n\n{content}"
                    system_text = ""
                history.append({"role": "user", "parts": [content]})
            elif msg["role"] == "assistant":
                history.append({"role": "model", "parts": [msg["content"]]})

        chat = model.start_chat(history=history[:-1])
        last_msg = history[-1]["parts"][0] if history else ""
        response = chat.send_message(last_msg)
        return response.text
