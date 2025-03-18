"""
OpenAI Provider Integration
Handles API calls to OpenAI for text and image generation
"""
import os
import time
import json
import logging
from typing import Dict, Any, Optional, List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("openai")

try:
    import openai
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    logger.warning("OpenAI package not installed. Install with: pip install openai")
    HAS_OPENAI = False

class OpenAIProvider:
    """OpenAI API provider for model inference"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the OpenAI provider with API key"""
        if not HAS_OPENAI:
            logger.error("OpenAI package not installed. Install with: pip install openai")
            return
            
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("No OpenAI API key provided. Set OPENAI_API_KEY env variable.")
        
        # Initialize client
        self.client = OpenAI(api_key=self.api_key)
    
    def generate_text(self, 
                    prompt: str, 
                    model: str = "gpt-3.5-turbo", 
                    max_tokens: int = 1000, 
                    temperature: float = 0.7, 
                    system_message: str = "You are a helpful assistant.", 
                    **kwargs) -> Dict[str, Any]:
        """Generate text using OpenAI models"""
        if not HAS_OPENAI or not self.api_key:
            return {"success": False, "error": "OpenAI package not installed or API key not provided"}
            
        start_time = time.time()
        
        try:
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            # Extract the generated text
            generated_text = response.choices[0].message.content
            
            return {
                "success": True,
                "text": generated_text,
                "model": model,
                "provider": "openai",
                "response_time": time.time() - start_time,
                "tokens": {
                    "prompt": response.usage.prompt_tokens,
                    "completion": response.usage.completion_tokens,
                    "total": response.usage.total_tokens
                },
                "raw_response": response.model_dump()
            }
            
        except Exception as e:
            logger.error(f"Error generating text with OpenAI: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time,
                "model": model,
                "provider": "openai"
            }
    
    def generate_image(self, 
                    prompt: str, 
                    model: str = "dall-e-3", 
                    size: str = "1024x1024", 
                    quality: str = "standard", 
                    n: int = 1, 
                    **kwargs) -> Dict[str, Any]:
        """Generate image using OpenAI DALL-E models"""
        if not HAS_OPENAI or not self.api_key:
            return {"success": False, "error": "OpenAI package not installed or API key not provided"}
            
        start_time = time.time()
        
        try:
            response = self.client.images.generate(
                model=model,
                prompt=prompt,
                size=size,
                quality=quality,
                n=n,
                **kwargs
            )
            
            return {
                "success": True,
                "image_url": response.data[0].url,  # URL of the generated image
                "model": model,
                "provider": "openai",
                "response_time": time.time() - start_time,
                "raw_response": response.model_dump()
            }
            
        except Exception as e:
            logger.error(f"Error generating image with OpenAI: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time,
                "model": model,
                "provider": "openai"
            }
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available OpenAI models"""
        if not HAS_OPENAI or not self.api_key:
            return []
            
        try:
            response = self.client.models.list()
            
            models = [
                {
                    "id": model.id,
                    "name": model.id,
                    "created": model.created
                }
                for model in response.data
            ]
            
            # Filter to only include completion and chat models
            text_models = [
                model for model in models
                if any(prefix in model["id"] for prefix in ["gpt-", "text-"])
            ]
            
            # Add DALL-E models (they don't show up in the list)
            image_models = [
                {"id": "dall-e-3", "name": "DALL-E 3"},
                {"id": "dall-e-2", "name": "DALL-E 2"}
            ]
            
            return {
                "text_models": text_models,
                "image_models": image_models
            }
            
        except Exception as e:
            logger.error(f"Error fetching OpenAI models: {e}")
            return []

# Example usage
if __name__ == "__main__":
    # Test the provider
    provider = OpenAIProvider()
    result = provider.generate_text("Write a short poem about AI.")
    print(json.dumps(result, indent=2)) 