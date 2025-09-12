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
        """Lazy load LLM client"""
        if self._client is None:
            if self.openai_api_key:
                try:
                    import openai
                    self._client = openai.OpenAI(api_key=self.openai_api_key)
                except Exception:
                    self._client = MockLLMClient()
            else:
                self._client = MockLLMClient()
        return self._client
    
    async def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.1) -> str:
        """Generate text using LLM"""
        try:
            if hasattr(self.client, 'chat'):
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content
            else:
                # Mock response
                return self._generate_mock_response(prompt)
        except Exception as e:
            print(f"LLM generation failed: {e}")
            return self._generate_mock_response(prompt)
    
    def _generate_mock_response(self, prompt: str) -> str:
        """Generate mock response for development"""
        if "SELECT" in prompt.upper() or "sql" in prompt.lower():
            return """
SQL: SELECT name, email FROM users WHERE created_at > '2023-01-01' LIMIT 100;
EXPLANATION: This query retrieves user names and emails for users created after January 1st, 2023.
REASONING: I identified the users table based on the schema and applied the date filter as requested.
"""
        return "This is a mock LLM response for development purposes."

class MockLLMClient:
    """Mock client for development"""
    
    def generate(self, prompt, **kwargs):
        return "Mock LLM response"

llm_provider_resource = LLMProviderResource(
    openai_api_key=os.getenv("OPENAI_API_KEY", ""),
    model_name=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
)