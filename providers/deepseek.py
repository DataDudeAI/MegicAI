"""
DeepSeek Provider Integration
Handles API calls to DeepSeek for AI model inference
"""
import os
import requests
import time
import json
import logging
from typing import Dict, Any, Optional, List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("deepseek")

class DeepSeekProvider:
    """DeepSeek API provider for model inference"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the DeepSeek provider with API key"""
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            logger.warning("No DeepSeek API key provided. Set DEEPSEEK_API_KEY env variable.")
        
        self.base_url = "https://api.deepseek.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_text(self, 
                    prompt: str, 
                    model: str = "deepseek-chat", 
                    max_tokens: int = 1000, 
                    temperature: float = 0.7, 
                    system_message: str = "You are a helpful assistant.", 
                    **kwargs) -> Dict[str, Any]:
        """Generate text using DeepSeek models"""
        if not self.api_key:
            return {"success": False, "error": "DeepSeek API key not provided"}
            
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
                logger.error(f"Error from DeepSeek API: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"DeepSeek API error: {response.status_code}",
                    "response_time": time.time() - start_time,
                    "model": model,
                    "provider": "deepseek"
                }
            
            result = response.json()
            
            # Extract the generated text
            generated_text = result["choices"][0]["message"]["content"]
            
            return {
                "success": True,
                "text": generated_text,
                "model": model,
                "provider": "deepseek",
                "response_time": time.time() - start_time,
                "tokens": {
                    "prompt": result.get("usage", {}).get("prompt_tokens", 0),
                    "completion": result.get("usage", {}).get("completion_tokens", 0),
                    "total": result.get("usage", {}).get("total_tokens", 0)
                },
                "raw_response": result
            }
            
        except Exception as e:
            logger.error(f"Error generating text with DeepSeek: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time,
                "model": model,
                "provider": "deepseek"
            }
    
    def generate_code(self, 
                    prompt: str, 
                    model: str = "deepseek-coder", 
                    max_tokens: int = 2000, 
                    temperature: float = 0.5, 
                    **kwargs) -> Dict[str, Any]:
        """Generate code using DeepSeek Coder models"""
        if not self.api_key:
            return {"success": False, "error": "DeepSeek API key not provided"}
            
        start_time = time.time()
        
        try:
            messages = [
                {"role": "system", "content": "You are a helpful coding assistant."},
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
                logger.error(f"Error from DeepSeek API: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"DeepSeek API error: {response.status_code}",
                    "response_time": time.time() - start_time,
                    "model": model,
                    "provider": "deepseek"
                }
            
            result = response.json()
            
            # Extract the generated code
            generated_code = result["choices"][0]["message"]["content"]
            
            return {
                "success": True,
                "text": generated_code,
                "model": model,
                "provider": "deepseek",
                "response_time": time.time() - start_time,
                "tokens": {
                    "prompt": result.get("usage", {}).get("prompt_tokens", 0),
                    "completion": result.get("usage", {}).get("completion_tokens", 0),
                    "total": result.get("usage", {}).get("total_tokens", 0)
                },
                "raw_response": result
            }
            
        except Exception as e:
            logger.error(f"Error generating code with DeepSeek: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time,
                "model": model,
                "provider": "deepseek"
            }
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available DeepSeek models"""
        if not self.api_key:
            return []
            
        # DeepSeek doesn't have a list models endpoint yet, so we hardcode the currently available models
        models = [
            {
                "id": "deepseek-chat",
                "name": "DeepSeek Chat",
                "description": "General-purpose language model for chat",
                "context_length": 4096
            },
            {
                "id": "deepseek-coder",
                "name": "DeepSeek Coder",
                "description": "Specialized model for code generation",
                "context_length": 8192
            },
            {
                "id": "deepseek-math",
                "name": "DeepSeek Math",
                "description": "Model fine-tuned for mathematical reasoning",
                "context_length": 4096
            }
        ]
        
        return models

# Example usage
if __name__ == "__main__":
    # Test the provider
    provider = DeepSeekProvider()
    result = provider.generate_text("Write a short poem about AI.")
    print(json.dumps(result, indent=2)) 