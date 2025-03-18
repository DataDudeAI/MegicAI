"""
Prompt Marketplace Module
Enables users to create, sell, purchase, and use AI prompts
"""
import os
import json
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from prompts.prompt_templates import PromptTemplate, PromptTemplateManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("prompt_marketplace")

class PromptMarketplace:
    """Manages the prompt marketplace functionality"""
    
    def __init__(self, data_dir: str = None):
        """Initialize the prompt marketplace"""
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), "marketplace_data")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Paths for data files
        self.purchases_file = os.path.join(self.data_dir, "purchases.json")
        self.sales_file = os.path.join(self.data_dir, "sales.json")
        self.stats_file = os.path.join(self.data_dir, "stats.json")
        
        # Initialize data files if they don't exist
        self._initialize_data_files()
        
        # Create prompt template manager
        self.template_manager = PromptTemplateManager()
    
    def _initialize_data_files(self):
        """Initialize data files if they don't exist"""
        if not os.path.exists(self.purchases_file):
            with open(self.purchases_file, "w") as f:
                json.dump([], f)
        
        if not os.path.exists(self.sales_file):
            with open(self.sales_file, "w") as f:
                json.dump([], f)
        
        if not os.path.exists(self.stats_file):
            with open(self.stats_file, "w") as f:
                json.dump({
                    "total_sales": 0,
                    "total_revenue": 0,
                    "prompt_usage": {},
                    "popular_categories": {}
                }, f, indent=2)
    
    def list_marketplace_prompts(self, category: str = None, sort_by: str = "popular") -> List[Dict[str, Any]]:
        """
        List prompts available in the marketplace
        
        Args:
            category: Optional category to filter by
            sort_by: Sorting method ('popular', 'newest', 'price_low', 'price_high')
            
        Returns:
            List of prompt templates available for purchase
        """
        # Get all public templates
        all_templates = self.template_manager.get_public_templates()
        
        # Filter by category if specified
        if category:
            all_templates = [t for t in all_templates if t.category.lower() == category.lower()]
        
        # Convert to dictionaries for easier manipulation
        templates_dict = [t.to_dict() for t in all_templates]
        
        # Add usage statistics
        templates_with_stats = self._add_stats_to_templates(templates_dict)
        
        # Sort the templates
        if sort_by == "popular":
            templates_with_stats.sort(key=lambda x: x.get("stats", {}).get("usage_count", 0), reverse=True)
        elif sort_by == "newest":
            templates_with_stats.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        elif sort_by == "price_low":
            templates_with_stats.sort(key=lambda x: x.get("price", 0))
        elif sort_by == "price_high":
            templates_with_stats.sort(key=lambda x: x.get("price", 0), reverse=True)
        
        return templates_with_stats
    
    def _add_stats_to_templates(self, templates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add usage statistics to template dictionaries"""
        try:
            with open(self.stats_file, "r") as f:
                stats = json.load(f)
            
            prompt_usage = stats.get("prompt_usage", {})
            
            # Add stats to each template
            for template in templates:
                template_id = template.get("id")
                template["stats"] = {
                    "usage_count": prompt_usage.get(template_id, {}).get("count", 0),
                    "purchase_count": prompt_usage.get(template_id, {}).get("purchases", 0),
                    "rating": prompt_usage.get(template_id, {}).get("avg_rating", 0),
                    "reviews": prompt_usage.get(template_id, {}).get("review_count", 0)
                }
            
            return templates
        except Exception as e:
            logger.error(f"Error adding stats to templates: {e}")
            return templates
    
    def get_prompt_details(self, prompt_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a marketplace prompt
        
        Args:
            prompt_id: ID of the prompt template
            
        Returns:
            Detailed prompt information including stats and sample outputs
        """
        prompt = self.template_manager.get_template(prompt_id)
        
        if not prompt:
            return {"success": False, "error": "Prompt not found"}
        
        if not prompt.is_public and prompt.created_by != "system":
            return {"success": False, "error": "Prompt is not available in the marketplace"}
        
        # Get prompt details
        prompt_dict = prompt.to_dict()
        
        # Add stats
        prompt_dict = self._add_stats_to_templates([prompt_dict])[0]
        
        # Get purchase information
        prompt_dict["purchases"] = self._get_prompt_purchases(prompt_id)
        
        return {
            "success": True,
            "prompt": prompt_dict
        }
    
    def _get_prompt_purchases(self, prompt_id: str) -> Dict[str, Any]:
        """Get purchase information for a prompt"""
        try:
            with open(self.sales_file, "r") as f:
                sales = json.load(f)
            
            # Filter sales for this prompt
            prompt_sales = [s for s in sales if s.get("prompt_id") == prompt_id]
            
            return {
                "total": len(prompt_sales),
                "recent": len([s for s in prompt_sales if 
                              (datetime.now() - datetime.fromisoformat(s.get("timestamp", ""))).days < 7])
            }
        except Exception as e:
            logger.error(f"Error getting prompt purchases: {e}")
            return {"total": 0, "recent": 0}
    
    def create_prompt_for_sale(self, 
                              name: str,
                              description: str,
                              template: str,
                              system_message: str,
                              category: str,
                              price: float,
                              parameters: Dict[str, Any],
                              created_by: str,
                              provider_defaults: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a new prompt template for sale in the marketplace
        
        Args:
            name: Name of the prompt template
            description: Description of what the prompt does
            template: The prompt template text
            system_message: System message for the prompt
            category: Category for the prompt
            price: Price in credits
            parameters: Dictionary of parameters for the prompt
            created_by: User ID of the creator
            provider_defaults: Default settings for different providers
            
        Returns:
            Result dictionary with success status and prompt information
        """
        # Validate inputs
        if not name or not template:
            return {"success": False, "error": "Name and template are required"}
        
        if price < 0:
            return {"success": False, "error": "Price cannot be negative"}
        
        # Create the prompt template
        new_prompt = PromptTemplate(
            name=name,
            description=description,
            template=template,
            system_message=system_message,
            category=category,
            is_public=True,  # It's for sale, so make it public
            created_by=created_by,
            price=price,
            parameters=parameters,
            provider_defaults=provider_defaults or {}
        )
        
        # Save the prompt
        created_prompt = self.template_manager.create_template(new_prompt)
        
        # Initialize stats for this prompt
        self._initialize_prompt_stats(created_prompt.id)
        
        return {
            "success": True,
            "prompt": created_prompt.to_dict(),
            "message": "Prompt successfully created and listed in the marketplace"
        }
    
    def _initialize_prompt_stats(self, prompt_id: str):
        """Initialize statistics for a new prompt"""
        try:
            with open(self.stats_file, "r") as f:
                stats = json.load(f)
            
            prompt_usage = stats.get("prompt_usage", {})
            prompt_usage[prompt_id] = {
                "count": 0,
                "purchases": 0,
                "avg_rating": 0,
                "review_count": 0,
                "last_used": None
            }
            
            stats["prompt_usage"] = prompt_usage
            
            with open(self.stats_file, "w") as f:
                json.dump(stats, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error initializing prompt stats: {e}")
    
    def purchase_prompt(self, prompt_id: str, user_id: str, credits_available: float) -> Dict[str, Any]:
        """
        Purchase a prompt from the marketplace
        
        Args:
            prompt_id: ID of the prompt to purchase
            user_id: ID of the user making the purchase
            credits_available: Credits available to the user
            
        Returns:
            Result dictionary with success status and transaction details
        """
        # Get the prompt
        prompt = self.template_manager.get_template(prompt_id)
        
        if not prompt:
            return {"success": False, "error": "Prompt not found"}
        
        if not prompt.is_public:
            return {"success": False, "error": "Prompt is not available for purchase"}
        
        # Check if user already owns this prompt
        if self._user_owns_prompt(user_id, prompt_id):
            return {"success": False, "error": "You already own this prompt"}
        
        # Check if user has enough credits
        if credits_available < prompt.price:
            return {"success": False, "error": "Insufficient credits", "credits_needed": prompt.price}
        
        # Process the purchase
        purchase_id = str(uuid.uuid4())
        purchase_time = datetime.now().isoformat()
        
        purchase_record = {
            "id": purchase_id,
            "prompt_id": prompt_id,
            "user_id": user_id,
            "seller_id": prompt.created_by,
            "price": prompt.price,
            "timestamp": purchase_time
        }
        
        # Record the purchase
        self._record_purchase(purchase_record)
        
        # Record the sale
        self._record_sale(purchase_record)
        
        # Update statistics
        self._update_stats_after_purchase(prompt_id)
        
        return {
            "success": True,
            "transaction": {
                "id": purchase_id,
                "prompt_id": prompt_id,
                "prompt_name": prompt.name,
                "price": prompt.price,
                "timestamp": purchase_time
            },
            "credits_used": prompt.price,
            "message": f"Successfully purchased prompt: {prompt.name}"
        }
    
    def _user_owns_prompt(self, user_id: str, prompt_id: str) -> bool:
        """Check if a user already owns a prompt"""
        try:
            with open(self.purchases_file, "r") as f:
                purchases = json.load(f)
            
            # Check if the user has already purchased this prompt
            for purchase in purchases:
                if purchase.get("user_id") == user_id and purchase.get("prompt_id") == prompt_id:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking if user owns prompt: {e}")
            return False
    
    def _record_purchase(self, purchase_record: Dict[str, Any]):
        """Record a prompt purchase"""
        try:
            with open(self.purchases_file, "r") as f:
                purchases = json.load(f)
            
            purchases.append(purchase_record)
            
            with open(self.purchases_file, "w") as f:
                json.dump(purchases, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error recording purchase: {e}")
    
    def _record_sale(self, purchase_record: Dict[str, Any]):
        """Record a prompt sale"""
        try:
            with open(self.sales_file, "r") as f:
                sales = json.load(f)
            
            sales.append(purchase_record)
            
            with open(self.sales_file, "w") as f:
                json.dump(sales, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error recording sale: {e}")
    
    def _update_stats_after_purchase(self, prompt_id: str):
        """Update statistics after a prompt purchase"""
        try:
            with open(self.stats_file, "r") as f:
                stats = json.load(f)
            
            # Update prompt-specific stats
            prompt_usage = stats.get("prompt_usage", {})
            if prompt_id not in prompt_usage:
                prompt_usage[prompt_id] = {
                    "count": 0,
                    "purchases": 0,
                    "avg_rating": 0,
                    "review_count": 0
                }
            
            prompt_usage[prompt_id]["purchases"] = prompt_usage[prompt_id].get("purchases", 0) + 1
            
            # Update global stats
            stats["total_sales"] = stats.get("total_sales", 0) + 1
            
            # Get the prompt price
            prompt = self.template_manager.get_template(prompt_id)
            if prompt:
                stats["total_revenue"] = stats.get("total_revenue", 0) + prompt.price
                
                # Update category popularity
                category = prompt.category
                popular_categories = stats.get("popular_categories", {})
                popular_categories[category] = popular_categories.get(category, 0) + 1
                stats["popular_categories"] = popular_categories
            
            # Save updated stats
            with open(self.stats_file, "w") as f:
                json.dump(stats, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating stats after purchase: {e}")
    
    def get_user_purchased_prompts(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get prompts purchased by a specific user
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of prompts owned by the user
        """
        purchased_prompt_ids = self._get_user_purchased_prompt_ids(user_id)
        
        # Get the prompt details for each purchased prompt
        purchased_prompts = []
        for prompt_id in purchased_prompt_ids:
            prompt = self.template_manager.get_template(prompt_id)
            if prompt:
                prompt_dict = prompt.to_dict()
                purchased_prompts.append(prompt_dict)
        
        return purchased_prompts
    
    def _get_user_purchased_prompt_ids(self, user_id: str) -> List[str]:
        """Get IDs of prompts purchased by a user"""
        try:
            with open(self.purchases_file, "r") as f:
                purchases = json.load(f)
            
            # Get unique prompt IDs purchased by this user
            prompt_ids = set()
            for purchase in purchases:
                if purchase.get("user_id") == user_id:
                    prompt_ids.add(purchase.get("prompt_id"))
            
            return list(prompt_ids)
            
        except Exception as e:
            logger.error(f"Error getting user purchased prompt IDs: {e}")
            return []
    
    def get_user_sales(self, user_id: str) -> Dict[str, Any]:
        """
        Get sales information for a specific seller
        
        Args:
            user_id: ID of the seller
            
        Returns:
            Dictionary with sales information
        """
        try:
            with open(self.sales_file, "r") as f:
                sales = json.load(f)
            
            # Filter sales by this seller
            user_sales = [s for s in sales if s.get("seller_id") == user_id]
            
            # Calculate total revenue
            total_revenue = sum(s.get("price", 0) for s in user_sales)
            
            # Group sales by prompt
            sales_by_prompt = {}
            for sale in user_sales:
                prompt_id = sale.get("prompt_id")
                if prompt_id not in sales_by_prompt:
                    sales_by_prompt[prompt_id] = []
                sales_by_prompt[prompt_id].append(sale)
            
            # Get prompt details and calculate stats for each prompt
            prompt_sales = []
            for prompt_id, sales_list in sales_by_prompt.items():
                prompt = self.template_manager.get_template(prompt_id)
                if not prompt:
                    continue
                
                prompt_revenue = sum(s.get("price", 0) for s in sales_list)
                
                prompt_sales.append({
                    "prompt_id": prompt_id,
                    "prompt_name": prompt.name,
                    "price": prompt.price,
                    "sales_count": len(sales_list),
                    "revenue": prompt_revenue,
                    "last_sale": max(s.get("timestamp", "") for s in sales_list)
                })
            
            # Sort by revenue
            prompt_sales.sort(key=lambda x: x.get("revenue", 0), reverse=True)
            
            return {
                "success": True,
                "total_sales": len(user_sales),
                "total_revenue": total_revenue,
                "prompt_count": len(prompt_sales),
                "prompts": prompt_sales
            }
            
        except Exception as e:
            logger.error(f"Error getting user sales: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def record_prompt_usage(self, prompt_id: str, user_id: str, provider: str = None) -> bool:
        """
        Record usage of a prompt
        
        Args:
            prompt_id: ID of the prompt used
            user_id: ID of the user using the prompt
            provider: Optional provider used
            
        Returns:
            Success status
        """
        try:
            with open(self.stats_file, "r") as f:
                stats = json.load(f)
            
            # Update prompt usage stats
            prompt_usage = stats.get("prompt_usage", {})
            if prompt_id not in prompt_usage:
                prompt_usage[prompt_id] = {
                    "count": 0,
                    "purchases": 0,
                    "avg_rating": 0,
                    "review_count": 0
                }
            
            prompt_usage[prompt_id]["count"] = prompt_usage[prompt_id].get("count", 0) + 1
            prompt_usage[prompt_id]["last_used"] = datetime.now().isoformat()
            
            # Track provider usage if provided
            if provider:
                providers = prompt_usage[prompt_id].get("providers", {})
                providers[provider] = providers.get(provider, 0) + 1
                prompt_usage[prompt_id]["providers"] = providers
            
            # Save updated stats
            with open(self.stats_file, "w") as f:
                json.dump(stats, f, indent=2)
            
            return True
                
        except Exception as e:
            logger.error(f"Error recording prompt usage: {e}")
            return False
    
    def rate_prompt(self, prompt_id: str, user_id: str, rating: int, review: str = None) -> Dict[str, Any]:
        """
        Rate and review a prompt
        
        Args:
            prompt_id: ID of the prompt to rate
            user_id: ID of the user providing the rating
            rating: Rating value (1-5)
            review: Optional review text
            
        Returns:
            Result dictionary with success status
        """
        # Validate rating
        if rating < 1 or rating > 5:
            return {"success": False, "error": "Rating must be between 1 and 5"}
        
        # Check if the user owns the prompt
        if not self._user_owns_prompt(user_id, prompt_id):
            return {"success": False, "error": "You must purchase a prompt before rating it"}
        
        try:
            # Update the stats with the new rating
            with open(self.stats_file, "r") as f:
                stats = json.load(f)
            
            prompt_usage = stats.get("prompt_usage", {})
            if prompt_id not in prompt_usage:
                return {"success": False, "error": "Prompt not found"}
            
            # Calculate new average rating
            current_avg = prompt_usage[prompt_id].get("avg_rating", 0)
            current_count = prompt_usage[prompt_id].get("review_count", 0)
            
            if current_count == 0:
                new_avg = rating
            else:
                new_avg = (current_avg * current_count + rating) / (current_count + 1)
            
            prompt_usage[prompt_id]["avg_rating"] = new_avg
            prompt_usage[prompt_id]["review_count"] = current_count + 1
            
            # Save the review if provided
            if review:
                reviews = prompt_usage[prompt_id].get("reviews", [])
                reviews.append({
                    "user_id": user_id,
                    "rating": rating,
                    "review": review,
                    "timestamp": datetime.now().isoformat()
                })
                prompt_usage[prompt_id]["reviews"] = reviews
            
            # Save updated stats
            with open(self.stats_file, "w") as f:
                json.dump(stats, f, indent=2)
            
            return {
                "success": True,
                "message": "Rating submitted successfully",
                "new_rating": new_avg,
                "review_count": current_count + 1
            }
                
        except Exception as e:
            logger.error(f"Error rating prompt: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_marketplace_stats(self) -> Dict[str, Any]:
        """Get overall marketplace statistics"""
        try:
            with open(self.stats_file, "r") as f:
                stats = json.load(f)
            
            # Get the top prompts by usage
            prompt_usage = stats.get("prompt_usage", {})
            top_prompts = []
            
            for prompt_id, usage in prompt_usage.items():
                prompt = self.template_manager.get_template(prompt_id)
                if not prompt:
                    continue
                
                top_prompts.append({
                    "id": prompt_id,
                    "name": prompt.name,
                    "creator": prompt.created_by,
                    "category": prompt.category,
                    "price": prompt.price,
                    "usage_count": usage.get("count", 0),
                    "purchase_count": usage.get("purchases", 0),
                    "rating": usage.get("avg_rating", 0),
                    "review_count": usage.get("review_count", 0)
                })
            
            # Sort by usage count
            top_prompts.sort(key=lambda x: x.get("usage_count", 0), reverse=True)
            top_prompts = top_prompts[:10]  # Get top 10
            
            # Get top categories
            categories = stats.get("popular_categories", {})
            top_categories = [{"category": k, "count": v} for k, v in categories.items()]
            top_categories.sort(key=lambda x: x.get("count", 0), reverse=True)
            
            return {
                "success": True,
                "total_sales": stats.get("total_sales", 0),
                "total_revenue": stats.get("total_revenue", 0),
                "top_prompts": top_prompts,
                "top_categories": top_categories
            }
                
        except Exception as e:
            logger.error(f"Error getting marketplace stats: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Example usage
if __name__ == "__main__":
    # Initialize the marketplace
    marketplace = PromptMarketplace()
    
    # Create a sample prompt for sale
    prompt_result = marketplace.create_prompt_for_sale(
        name="Advanced SEO Article Writer",
        description="Generate comprehensive SEO-optimized articles with proper keyword placement and structure",
        template="Write a {length} word SEO-optimized article about {topic}. Target the keyword {keyword} with a keyword density of {density}%. Include {headings} headings, a compelling introduction, and a conclusion with call-to-action.",
        system_message="You are an expert SEO content writer who creates engaging, well-researched content that ranks well in search engines.",
        category="marketing",
        price=25.0,
        parameters={
            "topic": {"type": "string", "description": "Main topic of the article", "required": True},
            "keyword": {"type": "string", "description": "Target keyword to optimize for", "required": True},
            "length": {"type": "number", "description": "Word count", "default": 1500},
            "density": {"type": "number", "description": "Keyword density percentage", "default": 2},
            "headings": {"type": "number", "description": "Number of headings to include", "default": 5}
        },
        created_by="seller123",
        provider_defaults={
            "openai": {"model": "gpt-4-turbo"}
        }
    )
    
    print(f"Created prompt: {prompt_result['success']}")
    
    if prompt_result['success']:
        # Simulate a purchase
        purchase_result = marketplace.purchase_prompt(
            prompt_id=prompt_result['prompt']['id'],
            user_id="buyer456",
            credits_available=100.0
        )
        
        print(f"Purchase result: {purchase_result['success']}")
        
        # Record usage of the prompt
        marketplace.record_prompt_usage(
            prompt_id=prompt_result['prompt']['id'],
            user_id="buyer456",
            provider="openai"
        )
        
        # Rate the prompt
        rating_result = marketplace.rate_prompt(
            prompt_id=prompt_result['prompt']['id'],
            user_id="buyer456",
            rating=5,
            review="This prompt generated an excellent SEO article that ranked quickly!"
        )
        
        print(f"Rating result: {rating_result['success']}")
        
    # Get marketplace stats
    stats = marketplace.get_marketplace_stats()
    print(f"Marketplace stats: {stats['success']}")
    if stats['success']:
        print(f"Total sales: {stats['total_sales']}") 