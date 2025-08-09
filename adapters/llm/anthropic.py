"""
Anthropic Claude LLM Client for Fantastic Router
Provides integration with Anthropic's Claude API
"""

import asyncio
import json
from typing import Dict, Any, Optional

try:
    import anthropic
except ImportError:
    anthropic = None


class AnthropicLLMClient:
    """Anthropic Claude client that implements the LLMClient protocol"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-haiku-20240307",  # Fast and cost-effective
        max_tokens: int = 1000,
        timeout: int = 30,
        temperature: float = 0.1
    ):
        if anthropic is None:
            raise ImportError(
                "anthropic package not found. "
                "Install with: pip install anthropic"
            )
        
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.temperature = temperature
        
        # Initialize the client
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key,
            timeout=timeout
        )
    
    async def analyze(self, prompt: str, temperature: float = 0.1) -> Dict[str, Any]:
        """
        Analyze a prompt using Claude and return structured JSON response
        
        Args:
            prompt: The input prompt to analyze
            temperature: Controls randomness (0.0 = deterministic, 1.0 = creative)
            
        Returns:
            Dict containing the structured response from Claude
        """
        
        try:
            # Enhance prompt to ensure JSON output
            enhanced_prompt = f"""
{prompt}

CRITICAL: You must respond with valid JSON only. No markdown, no explanations, no extra text.
Just pure JSON that can be parsed directly.

Example format:
{{
    "action_type": "NAVIGATE",
    "entities": ["example"],
    "confidence": 0.85,
    "reasoning": "explanation here"
}}

Respond with JSON now:
"""
            
            # Make the request to Claude
            response = await asyncio.wait_for(
                self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=temperature,
                    system="You are an expert at analyzing user intents and returning structured JSON responses. Always respond with valid JSON only, no extra text.",
                    messages=[
                        {
                            "role": "user",
                            "content": enhanced_prompt
                        }
                    ]
                ),
                timeout=self.timeout
            )
            
            # Extract the response text
            if not response.content:
                raise Exception("Empty response from Claude")
            
            response_text = response.content[0].text.strip()
            
            # Parse JSON response
            try:
                parsed_response = json.loads(response_text)
                return parsed_response
            except json.JSONDecodeError:
                # Try to extract JSON from response if it contains extra text
                return self._extract_json_from_text(response_text)
        
        except asyncio.TimeoutError:
            raise Exception(f"Claude request timed out after {self.timeout} seconds")
        except Exception as e:
            # Return error response in expected format
            return {
                "error": f"Claude API error: {str(e)}",
                "action_type": "NAVIGATE",
                "entities": [],
                "confidence": 0.1,
                "reasoning": f"Technical error: {str(e)}"
            }
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Try to extract JSON from text that might contain extra content"""
        # Remove common markdown artifacts
        text = text.replace('```json', '').replace('```', '').strip()
        
        # Look for JSON-like structures
        start_chars = ['{', '[']
        end_chars = ['}', ']']
        
        for start_char, end_char in zip(start_chars, end_chars):
            start_idx = text.find(start_char)
            if start_idx != -1:
                # Find the matching closing bracket
                bracket_count = 0
                for i, char in enumerate(text[start_idx:], start_idx):
                    if char == start_char:
                        bracket_count += 1
                    elif char == end_char:
                        bracket_count -= 1
                        if bracket_count == 0:
                            try:
                                json_str = text[start_idx:i+1]
                                return json.loads(json_str)
                            except json.JSONDecodeError:
                                continue
        
        # If no valid JSON found, return error response
        return {
            "error": "Could not parse JSON from Claude response",
            "action_type": "NAVIGATE",
            "entities": [],
            "confidence": 0.1,
            "reasoning": f"Failed to parse response: {text[:100]}...",
            "raw_response": text
        }


def create_anthropic_client(
    api_key: str,
    model: str = "claude-3-haiku-20240307",
    max_tokens: int = 1000,
    timeout: int = 30,
    temperature: float = 0.1
) -> AnthropicLLMClient:
    """
    Factory function to create an Anthropic LLM client
    
    Args:
        api_key: Your Anthropic API key
        model: Claude model to use (see RECOMMENDED_MODELS)
        max_tokens: Maximum tokens in response
        timeout: Request timeout in seconds
        temperature: Creativity level (0.0-1.0)
        
    Returns:
        Configured AnthropicLLMClient instance
    """
    return AnthropicLLMClient(
        api_key=api_key,
        model=model,
        max_tokens=max_tokens,
        timeout=timeout,
        temperature=temperature
    )


# Recommended Claude models for different use cases
RECOMMENDED_MODELS = {
    "fast": "claude-3-haiku-20240307",       # Fastest, most cost-effective
    "balanced": "claude-3-5-sonnet-20241022", # Best balance of speed and intelligence
    "smart": "claude-3-5-sonnet-20241022",   # Most intelligent (same as balanced)
    "legacy": "claude-3-opus-20240229",      # Previous top model (slower, more expensive)
}

# Quick setup guide
SETUP_GUIDE = """
🚀 Quick Anthropic Setup:

1. Get API Key:
   - Sign up at https://console.anthropic.com
   - Generate an API key from the dashboard

2. Use with Fantastic Router:
   from adapters.llm.anthropic import create_anthropic_client
   
   llm_client = create_anthropic_client(
       api_key="your-anthropic-api-key"
   )
   
   router = FantasticRouter(
       llm_client=llm_client,
       db_client=db_client,
       config=config
   )

💡 Model Recommendations:
- claude-3-haiku-20240307: Fastest, cheapest, good for simple tasks
- claude-3-5-sonnet-20241022: Best overall, excellent reasoning
- claude-3-opus-20240229: Most capable but slower and expensive

🔍 Features:
- Very good at following instructions
- Excellent reasoning capabilities
- Strong JSON formatting
- Good at understanding context
"""

# Usage example:
"""
# Basic usage
from adapters.llm.anthropic import create_anthropic_client

llm_client = create_anthropic_client(
    api_key="your-anthropic-api-key",
    model="claude-3-haiku-20240307"  # Fast model
)

# Use with router (same as any other LLM client)
router = FantasticRouter(
    llm_client=llm_client,
    db_client=db_client,
    config=config
)
""" 