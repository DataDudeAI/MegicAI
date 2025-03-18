class Tool:
    def __init__(self, id, name, description, icon, cost, example_prompts, providers):
        self.id = id
        self.name = name
        self.description = description
        self.icon = icon
        self.cost = cost
        self.example_prompts = example_prompts
        self.providers = providers

    def get_info(self):
        """Return a summary of the tool's information."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "cost": self.cost,
            "example_prompts": self.example_prompts,
            "providers": self.providers,
        }

# Define the tools with associated prompts
TOOLS = [
    Tool(
        id="text-generation",
        name="Text Generation",
        description="Generate text using AI models",
        icon="text.svg",
        cost=1.0,
        example_prompts=[
            "Write a short story about a robot learning to paint.",
            "Create a product description for a new smartphone.",
            "Explain quantum computing to a 10-year-old."
        ],
        providers=["openai", "deepseek", "openrouter", "huggingface"]
    ),
    Tool(
        id="image-generation",
        name="Image Generation",
        description="Generate images from text descriptions",
        icon="image.svg",
        cost=5.0,
        example_prompts=[
            "A futuristic city with flying cars and tall buildings.",
            "A photorealistic portrait of a cyberpunk character.",
            "A peaceful mountain landscape at sunset."
        ],
        providers=["openai", "huggingface"]
    ),
    Tool(
        id="code-generation",
        name="Code Generation",
        description="Generate code in various programming languages",
        icon="code.svg",
        cost=2.0,
        example_prompts=[
            "Write a Python function to calculate Fibonacci numbers.",
            "Create a React component for a login form.",
            "Generate a SQL query to find customers who made purchases last month."
        ],
        providers=["openai", "deepseek", "openrouter"]
    ),
    Tool(
        id="ai-copywriter",
        name="AI Copywriter",
        description="Generates product descriptions and creative content.",
        icon="copywriter.svg",
        cost=0.20,
        example_prompts=[
            "Generate a product description for a new gadget.",
            "Create a catchy tagline for a marketing campaign."
        ],
        providers=["huggingface", "openrouter"]
    ),
    Tool(
        id="email-generator",
        name="Email Generator",
        description="Drafts professional or marketing emails.",
        icon="email.svg",
        cost=0.18,
        example_prompts=[
            "Draft a follow-up email for a job application.",
            "Create a marketing email for a new product launch."
        ],
        providers=["huggingface", "deepseek"]
    ),
    Tool(
        id="blog-writer",
        name="Blog Writer",
        description="Writes detailed blog posts with SEO optimization.",
        icon="blog.svg",
        cost=0.30,
        example_prompts=[
            "Write a blog post about the benefits of meditation.",
            "Create a travel blog post about Paris."
        ],
        providers=["huggingface", "deepseek"]
    ),
    Tool(
        id="resume-builder",
        name="AI Resume Builder",
        description="Creates professional resumes tailored to job roles.",
        icon="resume.svg",
        cost=0.25,
        example_prompts=[
            "Create a resume for a software engineer.",
            "Draft a resume for a marketing manager."
        ],
        providers=["huggingface", "openrouter"]
    ),
    Tool(
        id="cover-letter-creator",
        name="Cover Letter Creator",
        description="Generates customized cover letters.",
        icon="cover_letter.svg",
        cost=0.20,
        example_prompts=[
            "Generate a cover letter for a data analyst position.",
            "Create a cover letter for a graphic designer role."
        ],
        providers=["huggingface", "openrouter"]
    ),
    Tool(
        id="script-generator",
        name="Script Generator",
        description="Writes engaging video or movie scripts.",
        icon="script.svg",
        cost=0.30,
        example_prompts=[
            "Write a script for a 5-minute promotional video.",
            "Create a movie script for a romantic comedy."
        ],
        providers=["huggingface", "deepseek"]
    ),
    Tool(
        id="storytelling",
        name="AI Storytelling",
        description="Develops creative and compelling stories.",
        icon="storytelling.svg",
        cost=0.20,
        example_prompts=[
            "Create a fantasy story about a dragon.",
            "Write a mystery story set in a small town."
        ],
        providers=["huggingface", "openrouter"]
    ),
    Tool(
        id="chatbot-assistant",
        name="Chatbot Assistant",
        description="Provides conversational responses for support.",
        icon="chatbot.svg",
        cost=0.18,
        example_prompts=[
            "Provide support for a customer inquiry.",
            "Answer frequently asked questions about a product."
        ],
        providers=["huggingface", "deepseek"]
    ),
    Tool(
        id="ai-image-generator",
        name="AI Image Generator",
        description="Creates visuals from text prompts.",
        icon="ai_image.svg",
        cost=2.50,
        example_prompts=[
            "Generate an image of a sunset over the mountains.",
            "Create an illustration of a futuristic city."
        ],
        providers=["huggingface", "replicate"]
    ),
    Tool(
        id="ai-logo-creator",
        name="AI Logo Creator",
        description="Designs logos for startups and businesses.",
        icon="logo.svg",
        cost=1.50,
        example_prompts=[
            "Create a logo for a new tech startup.",
            "Design a logo for a coffee shop."
        ],
        providers=["huggingface", "replicate"]
    ),
    Tool(
        id="ai-avatar-generator",
        name="AI Avatar Generator",
        description="Generates custom avatars for gaming or profiles.",
        icon="avatar.svg",
        cost=2.00,
        example_prompts=[
            "Generate an avatar for a gaming profile.",
            "Create a custom avatar for a social media account."
        ],
        providers=["huggingface", "replicate"]
    ),
    Tool(
        id="ai-face-swap",
        name="AI Face Swap",
        description="Swaps faces in images or videos seamlessly.",
        icon="face_swap.svg",
        cost=2.00,
        example_prompts=[
            "Swap faces in a family photo.",
            "Create a fun face swap for a video."
        ],
        providers=["huggingface", "replicate"]
    ),
    Tool(
        id="ai-meme-creator",
        name="AI Meme Creator",
        description="Generates memes with custom captions.",
        icon="meme.svg",
        cost=0.40,
        example_prompts=[
            "Create a meme about cats.",
            "Generate a funny meme for social media."
        ],
        providers=["huggingface", "replicate"]
    ),
    Tool(
        id="ai-video-editor",
        name="AI Video Editor",
        description="Automates video edits, transitions, and effects.",
        icon="video_editor.svg",
        cost=10.00,
        example_prompts=[
            "Edit a video for a YouTube channel.",
            "Create a highlight reel from a sports event."
        ],
        providers=["huggingface", "replicate"]
    ),
    Tool(
        id="ai-video-script-writer",
        name="AI Video Script Writer",
        description="Generates structured video content ideas.",
        icon="video_script.svg",
        cost=0.30,
        example_prompts=[
            "Write a script for a cooking tutorial.",
            "Create a script for a travel vlog."
        ],
        providers=["huggingface", "deepseek"]
    ),
    Tool(
        id="ai-video-dubbing",
        name="AI Video Dubbing",
        description="Dubs videos in multiple languages with natural voices.",
        icon="video_dubbing.svg",
        cost=5.00,
        example_prompts=[
            "Dub a video in Spanish.",
            "Create a multilingual version of a promotional video."
        ],
        providers=["huggingface", "replicate"]
    ),
    Tool(
        id="ai-data-analyzer",
        name="AI Data Analyzer",
        description="Analyzes datasets for insights and trends.",
        icon="data_analyzer.svg",
        cost=3.00,
        example_prompts=[
            "Analyze sales data for trends.",
            "Generate insights from customer feedback data."
        ],
        providers=["huggingface", "deepseek"]
    ),
    Tool(
        id="ai-code-optimizer",
        name="AI Code Optimizer",
        description="Enhances Python, JavaScript, and SQL code.",
        icon="code_optimizer.svg",
        cost=0.60,
        example_prompts=[
            "Optimize this Python function for performance.",
            "Improve the readability of this SQL query."
        ],
        providers=["huggingface", "deepseek"]
    ),
    Tool(
        id="ai-debugging-assistant",
        name="AI Debugging Assistant",
        description="Identifies and corrects coding errors.",
        icon="debugging.svg",
        cost=1.00,
        example_prompts=[
            "Find and fix errors in this JavaScript code.",
            "Debug this Python script for syntax issues."
        ],
        providers=["huggingface", "deepseek"]
    ),
    Tool(
        id="ai-quiz-generator",
        name="AI Quiz Generator",
        description="Creates quizzes with multiple-choice options.",
        icon="quiz.svg",
        cost=0.40,
        example_prompts=[
            "Generate a quiz on world history.",
            "Create a multiple-choice quiz for a science topic."
        ],
        providers=["huggingface", "deepseek"]
    ),
    Tool(
        id="ai-poetry-generator",
        name="AI Poetry Generator",
        description="Crafts unique poetry on various themes.",
        icon="poetry.svg",
        cost=0.20,
        example_prompts=[
            "Write a poem about love.",
            "Create a haiku about nature."
        ],
        providers=["huggingface", "openrouter"]
    ),
    Tool(
        id="ai-meditation-coach",
        name="AI Meditation Coach",
        description="Guides users through relaxation exercises.",
        icon="meditation.svg",
        cost=1.00,
        example_prompts=[
            "Guide a user through a breathing exercise.",
            "Provide a meditation session for stress relief."
        ],
        providers=["huggingface", "replicate"]
    )
]

def get_tool_by_id(tool_id):
    """Retrieve a tool by its ID."""
    for tool in TOOLS:
        if tool.id == tool_id:
            return tool.get_info()
    return None

def get_tool_by_id(tool_id):
    """Retrieve a tool by its ID."""
    for tool in TOOLS:
        if tool.id == tool_id:
            return tool.get_info()
    return None