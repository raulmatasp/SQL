from dagster import ConfigurableResource
from typing import Dict, Any
import os

class LLMProviderResource(ConfigurableResource):
    """LLM provider resource for AI operations"""
    
    openai_api_key: str = ""
    model_name: str = "gpt-3.5-turbo"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._client = None
    
    @property
    def client(self):
        """Lazy load LLM client or raise if not configured"""
        if self._client is None:
            if not self.openai_api_key:
                raise RuntimeError(
                    "LLM not configured: set OPENAI_API_KEY for Dagster LLMProviderResource"
                )
            import openai
            self._client = openai.OpenAI(api_key=self.openai_api_key)
        return self._client
    
    def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.1) -> str:
        """Generate text using LLM (synchronous for asset compatibility)"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(
                f"Dagster LLM generation failed: {e}. Ensure OPENAI_API_KEY is set and valid."
            )

llm_provider_resource = LLMProviderResource(
    openai_api_key=os.getenv("OPENAI_API_KEY", ""),
    model_name=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
)
