"""
Hugging Face Provider Integration
Handles API calls to Hugging Face for AI model inference
"""
import os
import requests
import time
import json
import logging
from typing import Dict, Any, Optional, List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("huggingface")

class HuggingFaceProvider:
    """Hugging Face API provider for model inference"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Hugging Face provider with API key"""
        self.api_key = api_key or os.getenv("HUGGINGFACE_API_KEY")
        if not self.api_key:
            logger.warning("No Hugging Face API key provided. Set HUGGINGFACE_API_KEY env variable.")
        
        self.base_url = "https://api-inference.huggingface.co/models"
        self.headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
    
    def generate_text(self, 
                     prompt: str, 
                     model: str = "mistralai/Mistral-7B-Instruct-v0.2", 
                     max_tokens: int = 1000, 
                     temperature: float = 0.7, 
                     **kwargs) -> Dict[str, Any]:
        """Generate text using Hugging Face text generation models"""
        start_time = time.time()
        
        try:
            url = f"{self.base_url}/{model}"
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": temperature,
                    "return_full_text": False,
                    **kwargs
                }
            }
            
            response = requests.post(
                url, 
                headers=self.headers, 
                json=payload
            )
            
            # Check for errors
            if response.status_code != 200:
                logger.error(f"Error from Hugging Face API: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"Hugging Face API error: {response.status_code}",
                    "response_time": time.time() - start_time,
                    "model": model,
                    "provider": "huggingface"
                }
            
            result = response.json()
            
            # Handle different response formats
            generated_text = ""
            if isinstance(result, list) and len(result) > 0:
                if "generated_text" in result[0]:
                    generated_text = result[0]["generated_text"]
                else:
                    generated_text = result[0].get("text", "")
            elif "generated_text" in result:
                generated_text = result["generated_text"]
            
            return {
                "success": True,
                "text": generated_text,
                "model": model,
                "provider": "huggingface",
                "response_time": time.time() - start_time,
                "raw_response": result
            }
            
        except Exception as e:
            logger.error(f"Error generating text with Hugging Face: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time,
                "model": model,
                "provider": "huggingface"
            }
    
    def generate_image(self, 
                     prompt: str, 
                     model: str = "stabilityai/stable-diffusion-xl-base-1.0", 
                     height: int = 512, 
                     width: int = 512, 
                     **kwargs) -> Dict[str, Any]:
        """Generate image using Hugging Face image generation models"""
        start_time = time.time()
        
        try:
            url = f"{self.base_url}/{model}"
            payload = {
                "inputs": prompt,
                "parameters": {
                    "height": height,
                    "width": width,
                    **kwargs
                }
            }
            
            response = requests.post(
                url, 
                headers=self.headers, 
                json=payload
            )
            
            # Image response is binary
            if response.status_code != 200:
                logger.error(f"Error from Hugging Face API: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"Hugging Face API error: {response.status_code}",
                    "response_time": time.time() - start_time,
                    "model": model,
                    "provider": "huggingface"
                }
            
            # Return binary image data in base64
            import base64
            image_data = base64.b64encode(response.content).decode("utf-8")
            
            return {
                "success": True,
                "image_data": image_data,
                "model": model,
                "provider": "huggingface",
                "response_time": time.time() - start_time
            }
            
        except Exception as e:
            logger.error(f"Error generating image with Hugging Face: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time,
                "model": model,
                "provider": "huggingface"
            }
    
    def get_available_models(self, task: str = "text-generation") -> List[Dict[str, Any]]:
        """Get available models for a specific task"""
        try:
            url = "https://huggingface.co/api/models"
            params = {
                "filter": task,
                "sort": "downloads",
                "direction": -1,
                "limit": 100
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                logger.error(f"Error fetching models: {response.status_code} - {response.text}")
                return []
            
            models = response.json()
            return [
                {
                    "id": model["id"],
                    "name": model.get("name", model["id"]),
                    "downloads": model.get("downloads", 0),
                    "tags": model.get("tags", [])
                }
                for model in models
            ]
            
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return []

# Example usage
if __name__ == "__main__":
    # Test the provider
    provider = HuggingFaceProvider()
    result = provider.generate_text("Write a short poem about AI.")
    print(json.dumps(result, indent=2)) 