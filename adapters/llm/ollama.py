"""
Ollama Local LLM Client for Fantastic Router
Provides integration with local LLMs via Ollama
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any, Optional, List


class OllamaLLMClient:
    """Ollama LLM client for local models that implements the LLMClient protocol"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.1:8b",  # Good balance of speed and quality
        timeout: int = 60,  # Local models can be slower
        temperature: float = 0.1,
        max_tokens: int = 1000
    ):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # API endpoints
        self.generate_url = f"{self.base_url}/api/generate"
        self.chat_url = f"{self.base_url}/api/chat"
        self.tags_url = f"{self.base_url}/api/tags"
    
    async def analyze(self, prompt: str, temperature: float = 0.1) -> Dict[str, Any]:
        """
        Analyze a prompt using Ollama and return structured JSON response
        
        Args:
            prompt: The input prompt to analyze
            temperature: Controls randomness (0.0 = deterministic, 1.0 = creative)
            
        Returns:
            Dict containing the structured response from the local LLM
        """
        
        try:
            # Check if Ollama is available
            if not await self._check_ollama_health():
                raise Exception("Ollama server not available. Make sure Ollama is running.")
            
            # Enhance prompt for JSON output
            enhanced_prompt = f"""
{prompt}

IMPORTANT: Respond with valid JSON only. No markdown, no explanations, no extra text.
Your response must be parseable as JSON.

Example format:
{{
    "action_type": "NAVIGATE",
    "entities": ["example"],
    "confidence": 0.85,
    "reasoning": "explanation here"
}}
"""
            
            # Prepare request payload
            payload = {
                "model": self.model,
                "prompt": enhanced_prompt,
                "stream": False,  # Get complete response
                "options": {
                    "temperature": temperature,
                    "num_predict": self.max_tokens,
                    "stop": ["```", "---", "###"]  # Stop on common markdown
                }
            }
            
            # Make the request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.generate_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error ({response.status}): {error_text}")
                    
                    result = await response.json()
                    
                    if 'response' not in result:
                        raise Exception("Invalid response from Ollama")
                    
                    response_text = result['response'].strip()
                    
                    # Parse JSON response
                    try:
                        parsed_response = json.loads(response_text)
                        return parsed_response
                    except json.JSONDecodeError:
                        # Try to extract JSON from response
                        return self._extract_json_from_text(response_text)
        
        except asyncio.TimeoutError:
            raise Exception(f"Ollama request timed out after {self.timeout} seconds")
        except Exception as e:
            # Return error response in expected format
            return {
                "error": f"Ollama error: {str(e)}",
                "action_type": "NAVIGATE",
                "entities": [],
                "confidence": 0.1,
                "reasoning": f"Local LLM error: {str(e)}"
            }
    
    async def _check_ollama_health(self) -> bool:
        """Check if Ollama server is running and accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.tags_url,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except:
            return False
    
    async def list_models(self) -> List[str]:
        """List available models in Ollama"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.tags_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return [model['name'] for model in data.get('models', [])]
                    return []
        except:
            return []
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull a model if it's not available locally"""
        try:
            pull_url = f"{self.base_url}/api/pull"
            payload = {"name": model_name}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    pull_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300)  # 5 min for model download
                ) as response:
                    return response.status == 200
        except:
            return False
    
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
        
        # If no valid JSON found, try to create a response from the text
        return {
            "error": "Could not parse JSON from local LLM response",
            "action_type": "NAVIGATE",
            "entities": [],
            "confidence": 0.1,
            "reasoning": f"Failed to parse response: {text[:200]}...",
            "raw_response": text
        }


def create_ollama_client(
    base_url: str = "http://localhost:11434",
    model: str = "llama3.1:8b",
    timeout: int = 60,
    temperature: float = 0.1,
    max_tokens: int = 1000
) -> OllamaLLMClient:
    """
    Factory function to create an Ollama LLM client
    
    Args:
        base_url: Ollama server URL (default: http://localhost:11434)
        model: Model name to use (see RECOMMENDED_MODELS)
        timeout: Request timeout in seconds (local models can be slower)
        temperature: Creativity level (0.0-1.0)
        max_tokens: Maximum tokens in response
        
    Returns:
        Configured OllamaLLMClient instance
    """
    return OllamaLLMClient(
        base_url=base_url,
        model=model,
        timeout=timeout,
        temperature=temperature,
        max_tokens=max_tokens
    )


# Recommended models for different use cases
RECOMMENDED_MODELS = {
    "best": "mistral-small3.2:24b",     # Best for function calling and structured output (15GB RAM)
    "balanced": "llama3.1:8b",          # Good balance of speed and quality (4GB RAM)
    "quality": "llama3.1:70b",          # High quality but slower (40GB RAM)
    "fast": "llama3.1:1b",              # Very fast, basic quality (1GB RAM)
    "code": "codellama:7b",             # Good for code understanding (4GB RAM)
    "instruct": "mistral-small3.1:24b", # Great for following instructions (15GB RAM)
    "claude_style": "incept5/llama3.1-claude", # Claude-like responses (4GB RAM)
    "efficient": "phi3:mini",           # Microsoft's efficient model (2GB RAM)
}

# Quick setup guide
SETUP_GUIDE = """
🚀 Quick Ollama Setup:

1. Install Ollama:
   - macOS: brew install ollama
   - Linux: curl -fsSL https://ollama.ai/install.sh | sh
   - Windows: Download from https://ollama.ai

2. Start Ollama:
   ollama serve

3. Pull a model:
   ollama pull llama3.1:8b

4. Use with Fantastic Router:
   from adapters.llm.ollama import create_ollama_client
   
   llm_client = create_ollama_client(
       model="llama3.1:8b"  # or any model you've pulled
   )
   
   router = FantasticRouter(
       llm_client=llm_client,
       db_client=db_client,
       config=config
   )

💡 Model Recommendations by Hardware:
- 8GB RAM: llama3.1:8b or codellama:7b
- 16GB RAM: llama3.1:8b (fast) or mistral:7b
- 32GB+ RAM: llama3.1:70b (best quality)
- Low RAM: llama3.1:1b or phi3:mini
"""

# Usage example:
"""
# Basic usage
from adapters.llm.ollama import create_ollama_client

llm_client = create_ollama_client(
    model="llama3.1:8b",
    base_url="http://localhost:11434"
)

# Check available models
models = await llm_client.list_models()
print(f"Available models: {models}")

# Pull a new model if needed
await llm_client.pull_model("llama3.1:8b")

# Use with router (same as any other LLM client)
router = FantasticRouter(
    llm_client=llm_client,
    db_client=db_client,
    config=config
)
""" 