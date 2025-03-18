"""
Prompt Templates Module
Manages prompt templates for different AI tools and providers
Includes system for storing, loading, and managing user-created prompts
"""
import os
import json
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("prompts")

class PromptTemplate:
    """Represents a prompt template that can be used with AI providers"""
    
    def __init__(self, 
                id: str = None,
                name: str = "",
                description: str = "",
                template: str = "",
                system_message: str = "",
                category: str = "",
                is_public: bool = False,
                created_by: str = "system",
                created_at: str = None,
                price: float = 0.0,
                parameters: Dict[str, Any] = None,
                provider_defaults: Dict[str, Any] = None):
        """Initialize a prompt template"""
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.template = template
        self.system_message = system_message
        self.category = category
        self.is_public = is_public
        self.created_by = created_by
        self.created_at = created_at or datetime.now().isoformat()
        self.price = price
        self.parameters = parameters or {}
        self.provider_defaults = provider_defaults or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "template": self.template,
            "system_message": self.system_message,
            "category": self.category,
            "is_public": self.is_public,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "price": self.price,
            "parameters": self.parameters,
            "provider_defaults": self.provider_defaults
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptTemplate':
        """Create template from dictionary"""
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            template=data.get("template", ""),
            system_message=data.get("system_message", ""),
            category=data.get("category", ""),
            is_public=data.get("is_public", False),
            created_by=data.get("created_by", "system"),
            created_at=data.get("created_at"),
            price=data.get("price", 0.0),
            parameters=data.get("parameters", {}),
            provider_defaults=data.get("provider_defaults", {})
        )
    
    def render(self, variables: Dict[str, Any] = None) -> Dict[str, str]:
        """
        Render the prompt template with the provided variables
        Returns both the rendered prompt and system message
        """
        variables = variables or {}
        prompt = self.template
        system = self.system_message
        
        # Replace variables in the template
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            prompt = prompt.replace(placeholder, str(value))
            system = system.replace(placeholder, str(value))
        
        return {
            "prompt": prompt,
            "system_message": system
        }

class PromptTemplateManager:
    """Manages prompt templates, including default and user-created ones"""
    
    def __init__(self, templates_dir: str = None):
        """Initialize the prompt template manager"""
        self.templates_dir = templates_dir or os.path.join(os.path.dirname(__file__), "templates")
        self.user_templates_dir = os.path.join(self.templates_dir, "user")
        
        # Create directories if they don't exist
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.user_templates_dir, exist_ok=True)
        
        # Load default templates
        self.default_templates = self._load_default_templates()
        
        # Load user templates
        self.user_templates = self._load_user_templates()
    
    def _load_default_templates(self) -> Dict[str, PromptTemplate]:
        """Load default templates from files"""
        templates = {}
        
        # Define default templates if no files exist yet
        default_templates = {
            "general_chat": PromptTemplate(
                id="general_chat",
                name="General Chat",
                description="A general-purpose chat prompt",
                template="Please answer the following question or respond to the message: {input}",
                system_message="You are a helpful assistant that provides accurate and concise responses.",
                category="general",
                created_by="system"
            ),
            "creative_writing": PromptTemplate(
                id="creative_writing",
                name="Creative Writing",
                description="Generate creative writing based on a premise",
                template="Write a {genre} {format} about {topic}.",
                system_message="You are a creative writer with expertise in different genres and formats.",
                category="creative",
                created_by="system",
                parameters={
                    "genre": {"type": "string", "description": "Genre of the writing", "default": "science fiction"},
                    "format": {"type": "string", "description": "Format of the writing", "default": "short story"},
                    "topic": {"type": "string", "description": "Topic or premise", "required": True}
                }
            ),
            "code_assistant": PromptTemplate(
                id="code_assistant",
                name="Code Assistant",
                description="Generate or debug code in various languages",
                template="I need help with the following code task in {language}:\n\n{task}\n\n{code}",
                system_message="You are an expert programmer. Provide well-commented, efficient, and correct code solutions.",
                category="development",
                created_by="system",
                parameters={
                    "language": {"type": "string", "description": "Programming language", "required": True},
                    "task": {"type": "string", "description": "Description of the coding task", "required": True},
                    "code": {"type": "string", "description": "Existing code (if any)", "default": ""}
                },
                provider_defaults={
                    "openai": {"model": "gpt-4-turbo"},
                    "deepseek": {"model": "deepseek-coder"}
                }
            ),
            "image_prompt": PromptTemplate(
                id="image_prompt",
                name="Image Generation",
                description="Detailed prompt for image generation",
                template="{subject} {style}, {details}, {quality}",
                system_message="",
                category="images",
                created_by="system",
                parameters={
                    "subject": {"type": "string", "description": "Main subject of the image", "required": True},
                    "style": {"type": "string", "description": "Art style", "default": "digital art"},
                    "details": {"type": "string", "description": "Additional details", "default": "detailed, vibrant colors"},
                    "quality": {"type": "string", "description": "Quality descriptors", "default": "high quality, 4k, trending on artstation"}
                },
                provider_defaults={
                    "openai": {"model": "dall-e-3"}
                }
            )
        }
        
        # Save default templates if they don't exist
        for template_id, template in default_templates.items():
            template_path = os.path.join(self.templates_dir, f"{template_id}.json")
            
            if not os.path.exists(template_path):
                with open(template_path, "w") as f:
                    json.dump(template.to_dict(), f, indent=2)
            
            templates[template_id] = template
        
        return templates
    
    def _load_user_templates(self) -> Dict[str, PromptTemplate]:
        """Load user-created templates"""
        templates = {}
        
        try:
            # List all JSON files in user_templates_dir
            for filename in os.listdir(self.user_templates_dir):
                if filename.endswith(".json"):
                    template_path = os.path.join(self.user_templates_dir, filename)
                    
                    with open(template_path, "r") as f:
                        template_data = json.load(f)
                        template = PromptTemplate.from_dict(template_data)
                        templates[template.id] = template
        except Exception as e:
            logger.error(f"Error loading user templates: {e}")
        
        return templates
    
    def get_all_templates(self) -> List[PromptTemplate]:
        """Get all available templates (default + user)"""
        all_templates = list(self.default_templates.values())
        
        # Add public user templates and user's own templates
        for template in self.user_templates.values():
            if template.is_public:
                all_templates.append(template)
        
        return all_templates
    
    def get_user_templates(self, user_id: str) -> List[PromptTemplate]:
        """Get templates created by a specific user"""
        return [t for t in self.user_templates.values() if t.created_by == user_id]
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Get a specific template by ID"""
        if template_id in self.default_templates:
            return self.default_templates[template_id]
        
        if template_id in self.user_templates:
            return self.user_templates[template_id]
        
        return None
    
    def create_template(self, template: PromptTemplate) -> PromptTemplate:
        """Create a new user template"""
        # Ensure unique ID
        if template.id in self.default_templates or template.id in self.user_templates:
            template.id = str(uuid.uuid4())
        
        # Save template to file
        template_path = os.path.join(self.user_templates_dir, f"{template.id}.json")
        
        with open(template_path, "w") as f:
            json.dump(template.to_dict(), f, indent=2)
        
        # Add to user templates
        self.user_templates[template.id] = template
        
        return template
    
    def update_template(self, template: PromptTemplate) -> Optional[PromptTemplate]:
        """Update an existing user template"""
        if template.id not in self.user_templates:
            logger.error(f"Template {template.id} not found or not a user template")
            return None
        
        # Save updated template
        template_path = os.path.join(self.user_templates_dir, f"{template.id}.json")
        
        with open(template_path, "w") as f:
            json.dump(template.to_dict(), f, indent=2)
        
        # Update in memory
        self.user_templates[template.id] = template
        
        return template
    
    def delete_template(self, template_id: str, user_id: str) -> bool:
        """Delete a user template"""
        if template_id not in self.user_templates:
            logger.error(f"Template {template_id} not found or not a user template")
            return False
        
        # Check ownership
        template = self.user_templates[template_id]
        if template.created_by != user_id and user_id != "admin":
            logger.error(f"User {user_id} does not own template {template_id}")
            return False
        
        # Delete template file
        template_path = os.path.join(self.user_templates_dir, f"{template_id}.json")
        
        try:
            os.remove(template_path)
            del self.user_templates[template_id]
            return True
        except Exception as e:
            logger.error(f"Error deleting template {template_id}: {e}")
            return False
    
    def get_templates_by_category(self, category: str) -> List[PromptTemplate]:
        """Get templates by category"""
        all_templates = self.get_all_templates()
        return [t for t in all_templates if t.category.lower() == category.lower()]
    
    def get_public_templates(self) -> List[PromptTemplate]:
        """Get all public templates created by users"""
        return [t for t in self.user_templates.values() if t.is_public]

# Example usage
if __name__ == "__main__":
    # Initialize manager
    manager = PromptTemplateManager()
    
    # Get all templates
    all_templates = manager.get_all_templates()
    print(f"Loaded {len(all_templates)} templates")
    
    # Create a new template
    new_template = PromptTemplate(
        name="SEO Content",
        description="Generate SEO-optimized content for websites",
        template="Write SEO-optimized content about {topic} targeting the keyword {keyword}. {tone} tone, {length} words.",
        system_message="You are an expert SEO content writer who creates engaging, well-researched content that ranks well in search engines.",
        category="marketing",
        created_by="user123",
        is_public=True,
        parameters={
            "topic": {"type": "string", "description": "Main topic", "required": True},
            "keyword": {"type": "string", "description": "Target keyword", "required": True},
            "tone": {"type": "string", "description": "Content tone", "default": "professional"},
            "length": {"type": "number", "description": "Content length in words", "default": 500}
        }
    )
    
    created = manager.create_template(new_template)
    print(f"Created new template: {created.id} - {created.name}")
    
    # Test rendering a template
    code_template = manager.get_template("code_assistant")
    if code_template:
        rendered = code_template.render({
            "language": "Python",
            "task": "Create a function to calculate Fibonacci numbers",
            "code": "def fibonacci(n):\n    # TODO: Implement"
        })
        
        print("\nRendered prompt:")
        print(rendered["prompt"])
        print("\nSystem message:")
 