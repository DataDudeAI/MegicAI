"""
AI Tool Hub - Main Application
Integrates all components into a single FastAPI application
"""
import os
import json
import uuid
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request, Response, Depends, HTTPException, Form, Cookie, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import provider modules
from providers import get_provider, HuggingFaceProvider, OpenAIProvider, DeepSeekProvider, OpenRouterProvider

# Import prompt modules
from prompts import PromptTemplate, PromptTemplateManager, PromptMarketplace

# Import ads module
from ads import GoogleAdsManager

# Import additional modules
import random
import time
import hashlib

# Import the Base from models.py
from models import Base

# Import the TOOLS from tools.py
from tools import TOOLS

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

# Database setup
DATABASE_URL = "sqlite:///./magicAi.db"  # Path to your SQLite database
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the database tables
Base.metadata.create_all(bind=engine)

# Create the FastAPI app
app = FastAPI(
    title="AI Tool Hub",
    description="A platform for using AI models with various tools and prompt templates",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Initialize components
template_manager = PromptTemplateManager()
marketplace = PromptMarketplace()
ads_manager = GoogleAdsManager()

# Security
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
security = HTTPBearer(auto_error=False)

# In-memory store of API keys for demo purpose
# In production, these would be stored in a database
API_KEYS = {}

# In-memory session store for demo purpose
# In production, these would be stored in a database or Redis
SESSIONS = {}

# Add new models for ad rewards
class AdRewardRequest(BaseModel):
    ad_type: str  # 'daily' or 'special'
    impression_id: Optional[str] = None

class DailyReward(BaseModel):
    user_id: str
    date: str
    count: int = 0
    last_reward: Optional[str] = None

class SpecialReward(BaseModel):
    user_id: str
    date: str
    claimed: bool = False
    claimed_at: Optional[str] = None

# In-memory stores for rewards (in production, use a database)
DAILY_REWARDS = {}
SPECIAL_REWARDS = {}

# Models
class CreditUpdateRequest(BaseModel):
    user_id: str
    amount: float
    reason: str = "manual"

class GenerateRequest(BaseModel):
    prompt: str
    model: str
    provider: str
    system_message: Optional[str] = None
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    prompt_template_id: Optional[str] = None
    template_variables: Optional[Dict[str, Any]] = None

class ImageGenerateRequest(BaseModel):
    prompt: str
    provider: str = "openai"
    model: Optional[str] = None
    size: Optional[str] = "1024x1024"
    prompt_template_id: Optional[str] = None
    template_variables: Optional[Dict[str, Any]] = None

class UserInfo(BaseModel):
    id: str
    username: str
    email: str
    credits: float = 10.0  # New users start with some free credits
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_login: str = Field(default_factory=lambda: datetime.now().isoformat())
    role: str = "user"

# Models for prompt system
class Prompt(BaseModel):
    id: str
    tool_id: str
    title: str
    content: str
    description: Optional[str] = None
    creator_id: Optional[str] = None
    is_default: bool = False
    usage_count: int = 0
    avg_rating: float = 0.0
    created_at: str = None
    updated_at: str = None
    tags: List[str] = []

class PromptRating(BaseModel):
    prompt_id: str
    user_id: str
    rating: int  # 1-5
    created_at: str

class UserPromptHistory(BaseModel):
    user_id: str
    prompt_id: str
    tool_id: str
    used_at: str
    was_modified: bool = False
    modifications: Optional[str] = None

# Mock database (replace with actual DynamoDB integration)
PROMPTS = {}
PROMPT_RATINGS = []
USER_PROMPT_HISTORY = []

# Initialize default prompts
def init_default_prompts():
    default_prompts = [
        {
            "id": "text-summary-default",
            "tool_id": "text-summary",
            "title": "Concise Text Summary",
            "content": "Summarize the following text in 3-5 bullet points highlighting the main ideas: {{input}}",
            "description": "Creates a bulleted summary of any text",
            "is_default": True,
            "tags": ["summary", "concise", "bullets"]
        },
        {
            "id": "image-portrait-default",
            "tool_id": "image-generator",
            "title": "Professional Portrait",
            "content": "Create a professional portrait photo of {{subject}}, high quality, studio lighting, detailed features, professional attire",
            "description": "Generates professional-looking portrait images",
            "is_default": True,
            "tags": ["portrait", "professional", "photo"]
        },
        {
            "id": "text-blog-default",
            "tool_id": "text-generator",
            "title": "Blog Post Generator",
            "content": "Write a comprehensive blog post about {{topic}}. Include an introduction, 3-5 main sections with subheadings, and a conclusion. Use a conversational tone and include practical examples where appropriate.",
            "description": "Creates complete blog posts with proper structure",
            "is_default": True,
            "tags": ["blog", "writing", "content"]
        },
        {
            "id": "code-python-default",
            "tool_id": "code-generator",
            "title": "Python Function",
            "content": "Write a Python function that {{task}}. Include docstrings, type hints, error handling, and comments explaining your logic. Provide a small example of how to use the function.",
            "description": "Generates well-structured Python functions",
            "is_default": True,
            "tags": ["python", "function", "code"]
        }
    ]
    
    for prompt in default_prompts:
        prompt_obj = Prompt(
            id=prompt["id"],
            tool_id=prompt["tool_id"],
            title=prompt["title"],
            content=prompt["content"],
            description=prompt["description"],
            is_default=prompt["is_default"],
            tags=prompt["tags"],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        PROMPTS[prompt["id"]] = prompt_obj

# Call initialization at startup
init_default_prompts()

# Helper functions for prompt system
def get_prompts_for_tool(tool_id: str) -> List[Prompt]:
    """Get all prompts for a specific tool"""
    return [p for p in PROMPTS.values() if p.tool_id == tool_id]

def get_default_prompts_for_tool(tool_id: str) -> List[Prompt]:
    """Get default prompts for a specific tool"""
    return [p for p in PROMPTS.values() if p.tool_id == tool_id and p.is_default]

def get_trending_prompts(limit: int = 5) -> List[Prompt]:
    """Get trending prompts based on usage count and ratings"""
    sorted_prompts = sorted(
        PROMPTS.values(), 
        key=lambda p: (p.usage_count * 0.7 + p.avg_rating * 0.3), 
        reverse=True
    )
    return sorted_prompts[:limit]

def get_personalized_prompts(user_id: str, tool_id: str, limit: int = 3) -> List[Prompt]:
    """Get personalized prompt recommendations for a user and tool"""
    # Get user history for this tool
    user_tool_history = [h for h in USER_PROMPT_HISTORY 
                        if h.user_id == user_id and h.tool_id == tool_id]
    
    if not user_tool_history:
        # If no history, return default prompts
        return get_default_prompts_for_tool(tool_id)
    
    # Count prompt usage
    prompt_usage = {}
    for history in user_tool_history:
        prompt_usage[history.prompt_id] = prompt_usage.get(history.prompt_id, 0) + 1
    
    # Get most used prompts
    most_used_prompt_ids = sorted(prompt_usage.items(), key=lambda x: x[1], reverse=True)
    most_used_prompts = [PROMPTS.get(pid) for pid, _ in most_used_prompt_ids[:limit]]
    
    # If we don't have enough, add some default or trending ones
    if len(most_used_prompts) < limit:
        defaults = get_default_prompts_for_tool(tool_id)
        for default in defaults:
            if default not in most_used_prompts and len(most_used_prompts) < limit:
                most_used_prompts.append(default)
    
    return most_used_prompts

def record_prompt_usage(user_id: str, prompt_id: str, tool_id: str, was_modified: bool = False, modifications: str = None):
    """Record that a user used a particular prompt"""
    # Update prompt usage count
    if prompt_id in PROMPTS:
        PROMPTS[prompt_id].usage_count += 1
        PROMPTS[prompt_id].updated_at = datetime.now().isoformat()
    
    # Add to history
    history_entry = UserPromptHistory(
        user_id=user_id,
        prompt_id=prompt_id,
        tool_id=tool_id,
        used_at=datetime.now().isoformat(),
        was_modified=was_modified,
        modifications=modifications
    )
    USER_PROMPT_HISTORY.append(history_entry)

def rate_prompt(user_id: str, prompt_id: str, rating: int):
    """Add or update a rating for a prompt"""
    # Check if user already rated this prompt
    existing_rating = next((r for r in PROMPT_RATINGS if r.user_id == user_id and r.prompt_id == prompt_id), None)
    
    if existing_rating:
        # Update existing rating
        existing_rating.rating = rating
        existing_rating.created_at = datetime.now().isoformat()
    else:
        # Add new rating
        rating_obj = PromptRating(
            prompt_id=prompt_id,
            user_id=user_id,
            rating=rating,
            created_at=datetime.now().isoformat()
        )
        PROMPT_RATINGS.append(rating_obj)
    
    # Update average rating on prompt
    if prompt_id in PROMPTS:
        prompt_ratings = [r.rating for r in PROMPT_RATINGS if r.prompt_id == prompt_id]
        if prompt_ratings:
            PROMPTS[prompt_id].avg_rating = sum(prompt_ratings) / len(prompt_ratings)
            PROMPTS[prompt_id].updated_at = datetime.now().isoformat()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# User authentication and session management
def get_session_user(session_id: Optional[str] = Cookie(None)) -> Optional[UserInfo]:
    """Get the user from the session"""
    if not session_id or session_id not in SESSIONS:
        return None
    
    session = SESSIONS[session_id]
    if datetime.now() > session["expires"]:
        # Session expired
        del SESSIONS[session_id]
        return None
    
    # Update session expiration
    session["expires"] = datetime.now() + timedelta(hours=24)
    
    return session["user"]

def require_session_user(admin_required: bool = False, session_user: Optional[UserInfo] = Depends(get_session_user)):
    """Require a logged-in user, optionally requiring admin role"""
    if not session_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if admin_required and getattr(session_user, "role", "") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    return session_user

def verify_api_key(api_key: str = Depends(api_key_header), 
                 credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInfo:
    """Verify API key from header or Bearer token"""
    # Try to get the API key from the header
    key = api_key
    
    # If not found, try to get it from the Bearer token
    if not key and credentials:
        key = credentials.credentials
    
    # Check if the key is valid
    if not key or key not in API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return API_KEYS[key]["user"]

# Credit packages configuration
CREDIT_PACKAGES = [
    {
        "id": "starter",
        "name": "Starter Pack",
        "description": "Perfect for trying out our AI tools",
        "credits": 100,
        "price": 49.99
    },
    {
        "id": "pro",
        "name": "Pro Pack",
        "description": "Most popular choice for regular users",
        "credits": 500,
        "price": 199.99
    },
    {
        "id": "enterprise",
        "name": "Enterprise Pack",
        "description": "Best value for power users",
        "credits": 2000,
        "price": 690.99
    }
]

# Mock user data (replace with database in production)
users = {}

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, session_user: Optional[UserInfo] = Depends(get_session_user)):
    """Home page with tools list"""
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "app_name": "AI Tool Hub",
            "tools": TOOLS,
            "session_user": session_user,
            "user": session_user,  # Add user for consistency with other templates
            "user_credits": session_user.credits if session_user else 0
        }
    )

@app.get("/tool/{tool_id}", response_class=HTMLResponse)
async def tool_page(
    tool_id: str,
    request: Request,
    session_user: Optional[UserInfo] = Depends(get_session_user)
):
    """Tool-specific page to execute a specific AI tool"""
    # Get the tool
    tool = next((t for t in TOOLS if t.id == tool_id), None)
    
    if not tool:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "app_name": "AI Tool Hub",
                "error_title": "Tool Not Found",
                "error_description": "The requested tool does not exist.",
                "user": session_user,
                "user_credits": session_user.credits if session_user else 0,
                "tools": TOOLS  # Include for consistent sidebar navigation
            }
        )
    
    # Get example prompts for this tool
    suggestions = tool.example_prompts if hasattr(tool, 'example_prompts') else []
    
    # Check if the user has enough credits
    has_enough_credits = session_user and session_user.credits >= tool.cost if session_user else False
    
    # Get available providers directly from the tool
    providers = tool.providers
    
    return templates.TemplateResponse(
        "tool.html",
        {
            "request": request,
            "app_name": "AI Tool Hub",
            "tool": tool,
            "user": session_user,
            "user_credits": session_user.credits if session_user else 0,
            "has_enough_credits": has_enough_credits,
            "suggestions": suggestions,
            "providers": providers,
            "tools": TOOLS  # Include all tools for sidebar navigation
        }
    )

@app.get("/result/{result_id}", response_class=HTMLResponse)
async def result_page(
    request: Request, 
    result_id: str,
    session_user: Optional[UserInfo] = Depends(get_session_user)
):
    """Result display page"""
    # In a real app, you'd fetch the result from a database
    # Here, we'll use a mock result for demonstration
    result = {
        "id": result_id,
        "type": "text",  # or "image" or "code"
        "provider": "openai",
        "model": "gpt-4",
        "prompt": "Write a short poem about AI",
        "result": """
        Silicon dreams in neural space,
        Learning patterns, quickening pace.
        Algorithms dance with grace divine,
        In zeros and ones, intelligence shine.
        
        Human-made yet growing beyond,
        Of our creations, we grow fond.
        Partners in progress, AI and we,
        Crafting together what's yet to be.
        """,
        "created_at": datetime.now().isoformat(),
        "response_time": 2.3  # seconds
    }
    
    return templates.TemplateResponse(
        "result.html", 
        {
            "request": request, 
            "app_name": "AI Tool Hub",
            "result": result,
            "user": session_user,
            "user_credits": session_user.credits if session_user else 0
        }
    )

@app.get("/marketplace", response_class=HTMLResponse)
async def marketplace_page(
    request: Request,
    category: Optional[str] = None,
    sort_by: str = "popular",
    session_user: Optional[UserInfo] = Depends(get_session_user)
):
    """Prompt marketplace page"""
    prompts = marketplace.list_marketplace_prompts(category=category, sort_by=sort_by)
    
    return templates.TemplateResponse(
        "marketplace.html", 
        {
            "request": request, 
            "app_name": "AI Tool Hub",
            "prompts": prompts,
            "category": category,
            "sort_by": sort_by,
            "user": session_user,
            "user_credits": session_user.credits if session_user else 0
        }
    )

@app.get("/ad", response_class=HTMLResponse)
async def ad_page(
    request: Request,
    session_user: Optional[UserInfo] = Depends(get_session_user)
):
    """Ad reward page"""
    return templates.TemplateResponse(
        "ad_reward.html", 
        {
            "request": request, 
            "app_name": "AI Tool Hub",
            "user": session_user,
            "user_credits": session_user.credits if session_user else 0
        }
    )

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse(
        "login.html", 
        {
            "request": request, 
            "app_name": "AI Tool Hub"
        }
    )

@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Process login"""
    # Check if admin login
    if username == "admin":
        # Check admin credentials
        admin_key = API_KEYS.get("admin_key")
        if not admin_key or admin_key.get("password") != password:
            # Admin login failure
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "app_name": "AI Tool Hub",
                    "error": "Invalid admin credentials"
                },
                status_code=400
            )
        
        # Admin login success
        user = admin_key["user"]
    else:
        # For demo purposes, any username/password combo works
        # In production, you'd verify against a database
        
        # Create or update user
        user_id = f"user_{username.lower().replace(' ', '_')}"
        user = UserInfo(
            id=user_id,
            username=username,
            email=f"{username.lower().replace(' ', '.')}@example.com",
            last_login=datetime.now().isoformat()
        )
        
        # Create session
        session_id = secrets.token_urlsafe(32)
        SESSIONS[session_id] = {
            "user": user,
            "expires": datetime.now() + timedelta(hours=24)
        }
        
        # Create redirect response
        response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        
        # Set session cookie
        response.set_cookie(
            key="session_id",
            value=session_id,
            max_age=86400,  # 24 hours
            httponly=True,
            samesite="lax"
        )
        
        return response

@app.get("/logout")
async def logout(
    response: Response,
    session_id: Optional[str] = Cookie(None)
):
    """Process logout"""
    if session_id and session_id in SESSIONS:
        del SESSIONS[session_id]
    
    response.delete_cookie(key="session_id")
    
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/credits", response_class=HTMLResponse)
async def credits_page(request: Request, session_user: Optional[UserInfo] = Depends(get_session_user)):
    """Credits management page"""
    if not session_user:
        return RedirectResponse(url="/login")
    
    # Get credit history (mock data - replace with database in production)
    credit_history = [
        {
            "date": "2024-03-20 14:30",
            "type": "Daily Reward",
            "amount": 5,
            "details": "Watched daily ad"
        },
        {
            "date": "2024-03-19 15:45",
            "type": "Tool Usage",
            "amount": -5,
            "details": "Used Image Generation"
        }
    ]
    
    return templates.TemplateResponse(
        "credits.html",
        {
            "request": request,
            "app_name": "AI Tool Hub",
            "user": session_user,
            "user_credits": session_user.credits,
            "credit_packages": CREDIT_PACKAGES,
            "credit_history": credit_history,
            "referral_link": f"{request.base_url}?ref={session_user.id}"
        }
    )

@app.get("/api/ads/status")
async def get_ads_status(request: Request, session_user: Optional[UserInfo] = Depends(get_session_user)):
    """Get user's ad reward status"""
    if not session_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "error": "Authentication required"}
        )
    
    # Get daily reward status
    daily_reward = DAILY_REWARDS.get(f"{session_user.id}_{datetime.now().date().isoformat()}")
    can_claim_daily = True
    cooldown_remaining = 0
    
    if daily_reward and daily_reward.last_reward:
        last_reward_time = datetime.fromisoformat(daily_reward.last_reward)
        if (datetime.now() - last_reward_time).total_seconds() < 3600:  # 1 hour cooldown
            can_claim_daily = False
            cooldown_remaining = 3600 - (datetime.now() - last_reward_time).total_seconds()
    
    # Get special reward status
    special_reward = SPECIAL_REWARDS.get(f"{session_user.id}_{datetime.now().date().isoformat()}")
    can_claim_special = True
    
    if special_reward and special_reward.claimed:
        can_claim_special = False
    
    return JSONResponse(
        content={
            "success": True,
            "daily_rewards": {
                "count": daily_reward.count if daily_reward else 0,
                "can_claim": can_claim_daily and (not daily_reward or daily_reward.count < 3),
                "cooldown_remaining": int(cooldown_remaining)
            },
            "special_reward": {
                "claimed": special_reward.claimed if special_reward else False,
                "can_claim": can_claim_special
            }
        }
    )

@app.post("/api/ads/claim")
async def claim_ad_reward(
    request: Request,
    session_user: Optional[UserInfo] = Depends(get_session_user)
):
    """Process ad reward claim"""
    if not session_user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "error": "Authentication required"}
        )
    
    data = await request.json()
    reward_type = data.get("type")
    
    if reward_type not in ["daily", "special"]:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "error": "Invalid reward type"}
        )
    
    today = datetime.now().date().isoformat()
    
    if reward_type == "daily":
        # Get or create daily reward record
        daily_key = f"{session_user.id}_{today}"
        if daily_key not in DAILY_REWARDS:
            DAILY_REWARDS[daily_key] = DailyReward(
                user_id=session_user.id,
                date=today,
                count=0
            )
        
        daily_reward = DAILY_REWARDS[daily_key]
        
        # Check if user has already claimed maximum daily rewards
        if daily_reward.count >= 3:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "error": "Daily reward limit reached"}
            )
        
        # Check cooldown period
        if daily_reward.last_reward:
            last_reward_time = datetime.fromisoformat(daily_reward.last_reward)
            if (datetime.now() - last_reward_time).total_seconds() < 3600:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"success": False, "error": "Please wait 1 hour between rewards"}
                )
        
        # Award credits
        reward_amount = 10
        session_user.credits += reward_amount
        daily_reward.count += 1
        daily_reward.last_reward = datetime.now().isoformat()
        
        return JSONResponse(
            content={
                "success": True,
                "credits_earned": reward_amount,
                "current_credits": session_user.credits,
                "daily_progress": daily_reward.count
            }
        )
    
    else:  # special reward
        # Get or create special reward record
        special_key = f"{session_user.id}_{today}"
        if special_key not in SPECIAL_REWARDS:
            SPECIAL_REWARDS[special_key] = SpecialReward(
                user_id=session_user.id,
                date=today,
                claimed=False
            )
        
        special_reward = SPECIAL_REWARDS[special_key]
        
        # Check if user has already claimed special reward
        if special_reward.claimed:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "error": "Special reward already claimed"}
            )
        
        # Award credits
        reward_amount = 25
        session_user.credits += reward_amount
        special_reward.claimed = True
        special_reward.claimed_at = datetime.now().isoformat()
        
        return JSONResponse(
            content={
                "success": True,
                "credits_earned": reward_amount,
                "current_credits": session_user.credits
            }
        )

@app.get("/create-admin")
async def create_admin(
    request: Request,
    response: Response,
):
    """Create an admin user (only for development)"""
    # Check if admin already exists
    admin_exists = False
    admin_user = None
    
    for session in SESSIONS.values():
        if session.get("user") and session["user"].username == "admin":
            admin_exists = True
            admin_user = session["user"]
            break
    
    if admin_exists:
        # Update admin credits
        admin_user.credits = 10000
        admin_user.role = "admin"
        return JSONResponse(
            content={
                "success": True,
                "message": "Admin user updated with 10000 credits",
                "user_id": admin_user.id
            }
        )
    
    # Create admin user
    user_id = "admin"
    user = UserInfo(
        id=user_id,
        username="admin",
        email="admin@example.com",
        credits=10000,
        role="admin",
        last_login=datetime.now().isoformat()
    )
    
    # In production, you would hash the password
    # For simplicity, we'll store it in a way that the login function can use it
    # This is for development only, never do this in production!
    admin_info = {
        "user": user,
        "password": "admin123",  # Plaintext for demo only
        "created_at": datetime.now().isoformat()
    }
    
    # Store admin info for login
    API_KEYS["admin_key"] = admin_info
    
    return JSONResponse(
        content={
            "success": True,
            "message": "Admin user created with 10000 credits",
            "user_id": user_id,
            "username": "admin",
            "password": "admin123"
        }
    )

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    user: UserInfo = Depends(lambda: require_session_user(admin_required=True))
):
    """Admin dashboard"""
    # Get all users
    users = []
    for session_id, session in SESSIONS.items():
        if "user" in session:
            users.append({
                "id": session["user"].id,
                "username": session["user"].username,
                "email": session["user"].email,
                "credits": session["user"].credits,
                "role": getattr(session["user"], "role", "user"),
                "session_id": session_id,
                "expires": session["expires"].isoformat() if "expires" in session else None
            })
    
    # Sort users by credits (descending)
    users.sort(key=lambda x: x["credits"], reverse=True)
    
    return templates.TemplateResponse(
        "admin_dashboard.html",
        {
            "request": request,
            "app_name": "AI Tool Hub",
            "user": user,
            "user_credits": user.credits,
            "users": users,
            "total_users": len(users),
            "total_credits": sum(u["credits"] for u in users),
            "admin_count": sum(1 for u in users if u["role"] == "admin")
        }
    )

@app.post("/api/admin/update-credits")
async def admin_update_credits(
    request: Request,
    user: UserInfo = Depends(lambda: require_session_user(admin_required=True))
):
    """Admin endpoint to update user credits"""
    data = await request.json()
    user_id = data.get("user_id")
    new_credits = data.get("credits")
    
    if not user_id or new_credits is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "error": "User ID and credits are required"}
        )
    
    # Find the user
    target_user = None
    for session in SESSIONS.values():
        if "user" in session and session["user"].id == user_id:
                target_user = session["user"]
                break
    
    if not target_user:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"success": False, "error": "User not found"}
        )
    
    # Update credits
    try:
        target_user.credits = float(new_credits)
    except ValueError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "error": "Invalid credit amount"}
        )
    
    return JSONResponse(
        content={
            "success": True,
            "user_id": user_id,
            "new_credits": target_user.credits,
            "message": f"Credits updated for user {target_user.username}"
        }
    )

@app.post("/process-request", response_class=HTMLResponse)
async def process_request(
    request: Request,
    tool_id: str = Form(...),
    prompt: str = Form(...),
    provider: str = Form("openai"),
    model: str = Form("default"),
    session_user: Optional[UserInfo] = Depends(get_session_user)
):
    """Process a tool request from a form"""
    # Get the tool
    tool = next((t for t in TOOLS if t.id == tool_id), None)
    
    if not tool:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "app_name": "AI Tool Hub",
                "error_title": "Tool Not Found",
                "error_description": "The requested tool does not exist.",
                "user": session_user,
                "user_credits": session_user.credits if session_user else 0,
                "tools": TOOLS  # Include for consistent sidebar navigation
            }
        )
    
    # Confirm that user is logged in
    if not session_user:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "app_name": "AI Tool Hub",
                "error_title": "Login Required",
                "error_description": "You must be logged in to use AI tools.",
                "user": None,
                "user_credits": 0,
                "tools": TOOLS  # Include for consistent sidebar navigation
            }
        )
    
    # Check if the user has enough credits
    if session_user.credits < tool.cost:
        return templates.TemplateResponse(
            "ad_reward.html",
            {
                "request": request,
                "app_name": "AI Tool Hub",
                "user": session_user,
                "user_credits": session_user.credits,
                "tool": tool,
                "reward_ad": ads_manager.get_ad_code("reward_video"),
                "sidebar_ad": ads_manager.get_ad_code("sidebar"),
                "return_url": f"/tool/{tool_id}",
                "tools": TOOLS  # Include for consistent sidebar navigation
            }
        )
    
    # Get the provider
    try:
        provider_instance = get_provider(provider)
        if not provider_instance:
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "app_name": "AI Tool Hub",
                    "error_title": "Provider Not Supported",
                    "error_description": f"The provider '{provider}' is not supported.",
                    "user": session_user,
                    "user_credits": session_user.credits if session_user else 0,
                    "tools": TOOLS  # Include for consistent sidebar navigation
                }
            )
        
        result = None
        result_type = "text"  # Default type
        
        # Determine result type based on tool ID
        if "image" in tool.id or "logo" in tool.id or "avatar" in tool.id:
            result_type = "image"
        elif "code" in tool.id or "debugging" in tool.id:
            result_type = "code"
        
        # Process the request based on tool type
        try:
            if result_type == "text":
                # Text generation tool
                result = provider_instance.generate_text(
                    prompt=prompt,
                    model=model if model != "default" else "mistralai/Mistral-7B-Instruct-v0.2",
                    max_tokens=1000,
                    temperature=0.7
                )
            elif result_type == "image":
                # Image generation tool
                try:
                    result = provider_instance.generate_image(
                        prompt=prompt,
                        model=model if model != "default" else "stabilityai/stable-diffusion-xl-base-1.0"
                    )
                except AttributeError:
                    # Provider doesn't support image generation
                    return templates.TemplateResponse(
                        "error.html",
                        {
                            "request": request,
                            "app_name": "AI Tool Hub",
                            "error_title": "Provider Not Supported",
                            "error_description": f"The provider '{provider}' does not support image generation.",
                            "user": session_user,
                            "user_credits": session_user.credits if session_user else 0,
                            "tools": TOOLS  # Include for consistent sidebar navigation
                        }
                    )
            elif result_type == "code":
                # Code generation tool
                result = provider_instance.generate_text(
                    prompt=prompt,
                    model=model if model != "default" else "gpt2",
                    max_tokens=1500,
                    temperature=0.5
                )
            else:
                return templates.TemplateResponse(
                    "error.html",
                    {
                        "request": request,
                        "app_name": "AI Tool Hub",
                        "error_title": "Tool Type Not Supported",
                        "error_description": f"The tool type '{result_type}' is not supported.",
                        "user": session_user,
                        "user_credits": session_user.credits if session_user else 0,
                        "tools": TOOLS  # Include for consistent sidebar navigation
                    }
                )
            
            # Deduct credits
            session_user.credits -= tool.cost
            
            # Return the result
            return templates.TemplateResponse(
                "result.html",
                {
                    "request": request,
                    "app_name": "AI Tool Hub",
                    "user": session_user,
                    "user_credits": session_user.credits,
                    "tool": tool,
                    "prompt": prompt,
                    "result": result,
                    "result_type": result_type,
                    "tools": TOOLS,  # Include all tools for sidebar navigation
                    "json_data": result.get("raw_response", {}) if isinstance(result, dict) else {}
                }
            )
        except Exception as generate_error:
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "app_name": "AI Tool Hub",
                    "error_title": "Generation Error",
                    "error_description": f"Error generating content: {str(generate_error)}",
                    "user": session_user,
                    "user_credits": session_user.credits,
                    "tools": TOOLS  # Include all tools for sidebar navigation
                }
            )
    except Exception as provider_error:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "app_name": "AI Tool Hub",
                "error_title": "Provider Error",
                "error_description": f"Error with provider: {str(provider_error)}",
                "user": session_user,
                "user_credits": session_user.credits,
                "tools": TOOLS  # Include all tools for sidebar navigation
            }
        )

@app.post("/register")
async def register(
    request: Request,
    response: Response,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    session_id: Optional[str] = Cookie(None)
):
    """Process registration"""
    # Check if username or email already exists (in production use a database)
    for session in SESSIONS.values():
        if session.get("user"):
            if session["user"].username.lower() == username.lower():
                return templates.TemplateResponse(
                    "register.html",
                    {
                        "request": request,
                        "app_name": "AI Tool Hub",
                        "error": "Username already exists",
                        "form_data": {"username": username, "email": email}
                    },
                    status_code=400
                )
            if session["user"].email.lower() == email.lower():
                return templates.TemplateResponse(
                    "register.html",
                    {
                        "request": request,
                        "app_name": "AI Tool Hub",
                        "error": "Email already exists",
                        "form_data": {"username": username, "email": email}
                    },
                    status_code=400
                )
    
    # Create user
    user_id = f"user_{username.lower().replace(' ', '_')}"
    
    # Check if there's an existing temporary session to convert
    is_converting_temp = False
    temp_credits = 0
    
    if session_id and session_id in SESSIONS:
        session = SESSIONS[session_id]
        if session.get("is_temporary", False):
            # Convert temporary session to permanent
            is_converting_temp = True
            temp_credits = session["user"].credits
            # Delete the temporary session
            del SESSIONS[session_id]
    
    # Create new user with starting credits (more if converting from temp)
    start_credits = 10.0 + temp_credits
    user = UserInfo(
        id=user_id,
        username=username,
        email=email,
        credits=start_credits,
        last_login=datetime.now().isoformat()
    )
    
    # In production, you would hash the password and store in database
    
    # Create new session
    new_session_id = secrets.token_urlsafe(32)
    SESSIONS[new_session_id] = {
        "user": user,
        "expires": datetime.now() + timedelta(hours=24)
    }
    
    # Set session cookie
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="session_id",
        value=new_session_id,
        max_age=86400,  # 24 hours
        httponly=True,
        samesite="lax"
    )
    
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)