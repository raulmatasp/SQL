from abc import ABC, abstractmethod
from typing import Optional
import openai
import asyncio

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.1) -> str:
        pass


class NotConfiguredLLMProvider(LLMProvider):
    """LLM provider that raises clear configuration errors."""

    def __init__(self, reason: str = "OpenAI API key is missing"):
        self.reason = reason

    async def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.1) -> str:
        raise RuntimeError(
            f"LLM provider is not configured: {self.reason}. "
            f"Set OPENAI_API_KEY (and optionally OPENAI_MODEL) to enable completions."
        )

class OpenAIProvider(LLMProvider):
    """OpenAI LLM Provider"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.1) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful SQL generation assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

class MockLLMProvider(LLMProvider):
    """Mock LLM Provider for testing"""
    
    async def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.1) -> str:
        # Return a mock SQL response based on the prompt
        await asyncio.sleep(0.1)  # Simulate API delay
        
        # Simple pattern matching for common queries
        prompt_lower = prompt.lower()
        
        if "sales" in prompt_lower and "region" in prompt_lower:
            return """
SQL: SELECT region, SUM(amount) as total_sales
FROM sales 
GROUP BY region
ORDER BY total_sales DESC
LIMIT 100;

EXPLANATION: This query calculates total sales for each region by grouping the sales data and summing the amounts.

REASONING: 
- Identified the sales table from the schema
- Used SUM aggregation to calculate totals
- Grouped by region to get sales per region
- Added ORDER BY to show highest sales first
- Added LIMIT for performance
            """
        elif "users" in prompt_lower:
            return """
SQL: SELECT id, name, email, created_at
FROM users 
WHERE created_at >= '2024-01-01'
ORDER BY created_at DESC
LIMIT 100;

EXPLANATION: This query retrieves user information filtered by creation date.

REASONING: 
- Selected relevant user fields
- Applied date filter for recent users
- Ordered by creation date
- Added LIMIT for performance
            """
        else:
            # Generic fallback
            return """
SQL: SELECT * FROM table_name LIMIT 100;

EXPLANATION: This is a generic query to retrieve data from the specified table.

REASONING: 
- Used generic SELECT statement
- Added LIMIT for safety
- Query structure follows best practices
            """
