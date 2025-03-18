from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "app_name": "MegicAI Test",
            "user_credits": 100,
            "tools": [
                {
                    "id": "text_gen",
                    "name": "Text Generator",
                    "description": "Generate creative text",
                    "icon": "fas fa-font",
                    "category": "text",
                    "credits": 5
                },
                {
                    "id": "image_gen",
                    "name": "Image Creator",
                    "description": "Create images from text",
                    "icon": "fas fa-image",
                    "category": "image",
                    "credits": 10
                }
            ]
        }
    )

@app.get("/hello")
def read_root():
    return {"message": "Hello World"} 