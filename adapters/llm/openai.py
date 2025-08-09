"""
OpenAI LLM client adapter for Fantastic Router
"""

import json
import openai
from typing import Dict, Any, Optional
import asyncio


class OpenAILLMClient:
    """OpenAI client that implements the LLMClient protocol"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo-1106",  # Much faster model with JSON support
        max_tokens: int = 1000,
        timeout: int = 30
    ):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout
    
    async def analyze(self, prompt: str, temperature: float = 0.1) -> Dict[str, Any]:
        """
        Analyze a prompt and return structured response
        
        Args:
            prompt: The prompt to analyze
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            
        Returns:
            Parsed JSON response from the LLM
        """
        
        try:
            # Check if model supports JSON mode
            json_mode_models = [
                "gpt-4-1106-preview", "gpt-4-turbo-preview", "gpt-4-turbo",
                "gpt-3.5-turbo-1106", "gpt-3.5-turbo-0125"
            ]
            
            request_params = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing user intents and returning structured JSON responses. Always respond with valid JSON only, no extra text."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": temperature,
                "max_tokens": self.max_tokens
            }
            
            # Only add response_format for models that support it
            if self.model in json_mode_models:
                request_params["response_format"] = {"type": "json_object"}
            
            response = await asyncio.wait_for(
                self.client.chat.completions.create(**request_params),
                timeout=self.timeout
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON response
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                # Fallback: try to extract JSON from response
                return self._extract_json_from_text(content)
                
        except asyncio.TimeoutError:
            return {
                "error": "LLM request timed out",
                "confidence": 0.0,
                "reasoning": "Request took too long to complete"
            }
        except Exception as e:
            return {
                "error": f"LLM request failed: {str(e)}",
                "confidence": 0.0,
                "reasoning": f"Technical error: {str(e)}"
            }
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Try to extract JSON from text response as fallback"""
        
        # Look for JSON-like content between braces
        start = text.find('{')
        end = text.rfind('}')
        
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                pass
        
        # Ultimate fallback
        return {
            "error": "Could not parse LLM response as JSON",
            "raw_response": text,
            "confidence": 0.0,
            "reasoning": "LLM returned unparseable response"
        }
    
    async def test_connection(self) -> bool:
        """Test if the LLM client is working"""
        
        try:
            response = await self.analyze("Test query: respond with {'status': 'ok'}")
            return response.get('status') == 'ok'
        except Exception:
            return False


# Convenience function for creating OpenAI client
def create_openai_client(
    api_key: str,
    model: str = "gpt-3.5-turbo-1106",
    max_tokens: int = 1000,
    timeout: int = 30
) -> OpenAILLMClient:
    """Create an OpenAI LLM client"""
    return OpenAILLMClient(
        api_key=api_key,
        model=model,
        max_tokens=max_tokens,
        timeout=timeout
    )
