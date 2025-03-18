"""
OpenRouter Provider Integration
Handles API calls to OpenRouter for AI model inference across multiple providers
"""
import os
import requests
import time
import json
import logging
from typing import Dict, Any, Optional, List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("openrouter")

class OpenRouterProvider:
    """OpenRouter API provider for model inference across multiple AI providers"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the OpenRouter provider with API key"""
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            logger.warning("No OpenRouter API key provided. Set OPENROUTER_API_KEY env variable.")
        
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.getenv("APP_URL", "http://localhost:8000"),  # Required by OpenRouter
            "X-Title": os.getenv("APP_NAME", "AI Tool Hub")  # Your app name
        }
    
    def generate_text(self, 
                     prompt: str, 
                     model: str = "anthropic/claude-3-opus:beta", 
                     max_tokens: int = 1000, 
                     temperature: float = 0.7, 
                     system_message: str = "You are a helpful assistant.", 
                     **kwargs) -> Dict[str, Any]:
        """Generate text using OpenRouter models"""
        if not self.api_key:
            return {"success": False, "error": "OpenRouter API key not provided"}
            
        start_time = time.time()
        
        try:
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
            
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                **kwargs
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload
            )
            
            # Check for errors
            if response.status_code != 200:
                logger.error(f"Error from OpenRouter API: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"OpenRouter API error: {response.status_code}",
                    "response_time": time.time() - start_time,
                    "model": model,
                    "provider": "openrouter"
                }
            
            result = response.json()
            
            # Extract the generated text
            generated_text = result["choices"][0]["message"]["content"]
            
            return {
                "success": True,
                "text": generated_text,
                "model": model,
                "provider": "openrouter",
                "response_time": time.time() - start_time,
                "tokens": {
                    "prompt": result.get("usage", {}).get("prompt_tokens", 0),
                    "completion": result.get("usage", {}).get("completion_tokens", 0),
                    "total": result.get("usage", {}).get("total_tokens", 0)
                },
                "raw_response": result
            }
            
        except Exception as e:
            logger.error(f"Error generating text with OpenRouter: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time,
                "model": model,
                "provider": "openrouter"
            }
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available OpenRouter models"""
        if not self.api_key:
            return []
            
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers
            )
            
            if response.status_code != 200:
                logger.error(f"Error fetching OpenRouter models: {response.status_code} - {response.text}")
                return []
            
            models_data = response.json()
            models = []
            
            for model in models_data.get("data", []):
                models.append({
                    "id": model.get("id"),
                    "name": model.get("name", model.get("id")),
                    "description": model.get("description", ""),
                    "context_length": model.get("context_length", 4096),
                    "pricing": {
                        "prompt": model.get("pricing", {}).get("prompt", 0),
                        "completion": model.get("pricing", {}).get("completion", 0)
                    }
                })
            
            return models
            
        except Exception as e:
            logger.error(f"Error fetching OpenRouter models: {e}")
            return []
    
    def get_models_by_provider(self, provider: str = None) -> List[Dict[str, Any]]:
        """Get available models filtered by provider"""
        models = self.get_available_models()
        
        if not provider:
            return models
            
        return [model for model in models if provider.lower() in model.get("id", "").lower()]

# Example usage
if __name__ == "__main__":
    # Test the provider
    provider = OpenRouterProvider()
    result = provider.generate_text("Write a short poem about AI.")
    print(json.dumps(result, indent=2))
    
    # Get all models
    models = provider.get_available_models()
    print(f"Found {len(models)} models")
    
    # Get only Anthropic models
    anthropic_models = provider.get_models_by_provider("anthropic")
    print(f"Found {len(anthropic_models)} Anthropic models") 