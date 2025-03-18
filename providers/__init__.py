"""
AI Providers Package
Exports provider classes for different AI model providers
"""

from providers.huggingface import HuggingFaceProvider
from providers.openai import OpenAIProvider
from providers.deepseek import DeepSeekProvider
from providers.openrouter import OpenRouterProvider

__all__ = [
    'HuggingFaceProvider',
    'OpenAIProvider',
    'DeepSeekProvider', 
    'OpenRouterProvider'
]

# Provider registry for easy access
PROVIDERS = {
    'huggingface': HuggingFaceProvider,
    'openai': OpenAIProvider,
    'deepseek': DeepSeekProvider,
    'openrouter': OpenRouterProvider
}

def get_provider(provider_name: str, api_key: str = None):
    """
    Get a provider instance by name
    
    Args:
        provider_name: Name of the provider ('huggingface', 'openai', etc.)
        api_key: Optional API key to use
        
    Returns:
        Provider instance or None if provider not found
    """
    provider_class = PROVIDERS.get(provider_name.lower())
    if not provider_class:
        return None
    
    return provider_class(api_key=api_key) 