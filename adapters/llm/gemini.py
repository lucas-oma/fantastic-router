"""
Gemini LLM Client for Fantastic Router
Provides integration with Google's Gemini API
"""

import asyncio
import json
from typing import Dict, Any, Optional

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
except ImportError:
    genai = None


class GeminiLLMClient:
    """Gemini LLM client that implements the LLMClient protocol"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",  # Fast and efficient model
        max_tokens: int = 1000,
        timeout: int = 30,
        temperature: float = 0.1
    ):
        if genai is None:
            raise ImportError(
                "google-generativeai package not found. "
                "Install with: pip install google-generativeai"
            )
        
        self.api_key = api_key
        self.model_name = model
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.temperature = temperature
        
        # Configure the client
        genai.configure(api_key=api_key)
        
        # Initialize the model with safety settings
        self.model = genai.GenerativeModel(
            model_name=model,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
                response_mime_type="application/json"  # Force JSON output
            ),
            # TODO double check this: Relaxed safety settings for business use cases.
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
    
    async def analyze(self, prompt: str, temperature: float = 0.1) -> Dict[str, Any]:
        """
        Analyze a prompt using Gemini and return structured JSON response
        
        Args:
            prompt: The input prompt to analyze
            temperature: Controls randomness (0.0 = deterministic, 1.0 = creative)
            
        Returns:
            Dict containing the structured response from Gemini
        """
        
        try:
            # Enhance prompt to ensure JSON output
            enhanced_prompt = f"""
{prompt}

CRITICAL: You must respond with valid JSON only. No markdown, no explanations, no extra text.
Just pure JSON that can be parsed directly.
"""
            
            # Create a new generation config for this specific call
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=self.max_tokens,
                temperature=temperature,
                response_mime_type="application/json"
            )
            
            # Generate response asynchronously
            response = await asyncio.wait_for(
                self._generate_content_async(enhanced_prompt, generation_config),
                timeout=self.timeout
            )
            
            # Extract and parse the response
            if not response.candidates:
                raise Exception("No response candidates from Gemini")
            
            response_text = response.candidates[0].content.parts[0].text.strip()
            
            # Parse JSON response
            try:
                parsed_response = json.loads(response_text)
                return parsed_response
            except json.JSONDecodeError as e:
                # Try to extract JSON from response if it contains extra text
                return self._extract_json_from_text(response_text)
                
        except asyncio.TimeoutError:
            raise Exception(f"Gemini request timed out after {self.timeout} seconds")
        except Exception as e:
            # Return error response in expected format
            return {
                "error": f"Gemini API error: {str(e)}",
                "action_type": "NAVIGATE",
                "entities": [],
                "confidence": 0.1,
                "reasoning": f"Technical error: {str(e)}"
            }
    
    async def _generate_content_async(self, prompt: str, generation_config) -> Any:
        """Async wrapper for Gemini content generation"""
        # Run the synchronous API call in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
        )
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Try to extract JSON from text that might contain extra content"""
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
            "error": "Could not parse JSON from Gemini response",
            "action_type": "NAVIGATE",
            "entities": [],
            "confidence": 0.1,
            "reasoning": f"Failed to parse response: {text[:100]}..."
        }


def create_gemini_client(
    api_key: str,
    model: str = "gemini-1.5-flash",
    max_tokens: int = 1000,
    timeout: int = 30,
    temperature: float = 0.1
) -> GeminiLLMClient:
    """
    Factory function to create a Gemini LLM client
    
    Args:
        api_key: Your Google AI API key
        model: Gemini model to use (gemini-1.5-flash, gemini-1.5-pro, etc.)
        max_tokens: Maximum tokens in response
        timeout: Request timeout in seconds
        temperature: Creativity level (0.0-1.0)
        
    Returns:
        Configured GeminiLLMClient instance
    """
    return GeminiLLMClient(
        api_key=api_key,
        model=model,
        max_tokens=max_tokens,
        timeout=timeout,
        temperature=temperature
    )


# Model recommendations
GEMINI_MODELS = {
    "fast": "gemini-1.5-flash",      # Fastest, most cost-effective
    "balanced": "gemini-1.5-pro",    # Best balance of speed and quality
    "smart": "gemini-1.0-pro",       # High quality reasoning
}

# Usage example:
"""
from adapters.llm.gemini import create_gemini_client

# Create client
llm_client = create_gemini_client(
    api_key="your-google-ai-api-key",
    model="gemini-1.5-flash"  # Fast model for quick responses
)

# Use with FantasticRouter
router = FantasticRouter(
    llm_client=llm_client,
    db_client=db_client,
    config=config
)
""" 