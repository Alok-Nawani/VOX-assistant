from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Optional, Dict
import psutil
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# JWT Config
SECRET_KEY = os.getenv("JWT_SECRET", "vox_secret_key_8899")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day

# Import Vox core
from core.orchestrator.brain import handle, _brain, Orchestrator
from core.system.controller import SystemController

system_controller = SystemController()

app = FastAPI(title="Vox Core API")
security = HTTPBearer()

# Enable CORS for the React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

system_controller = SystemController()

class ChatRequest(BaseModel):
    text: str
    image: Optional[str] = None
    language: Optional[str] = "en"
    tone: Optional[str] = "Jarvis"

class SaveImageRequest(BaseModel):
    image: str
    prefix: Optional[str] = "Capture"

class AuthRequest(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = ""

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"id": int(user_id)}
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

@app.on_event("startup")
async def startup_event():
    global _brain
    try:
        _brain = Orchestrator()
        print("Vox Brain & Auth Engine: Online")
    except Exception as e:
        print(f"CRITICAL ERROR: Vox Brain failed to initialize: {e}")
        # Initialize an empty object to prevent downstream crashes
        _brain = None

@app.post("/api/auth/signup")
async def signup(request: AuthRequest):
    global _brain
    if _brain is None: _brain = Orchestrator()
    user_id = _brain.sign_up(request.username, request.password, full_name=request.full_name)
    if user_id == -1:
        raise HTTPException(status_code=400, detail="Username already exists")
    token = create_access_token(data={"sub": str(user_id)})
    return {"access_token": token, "token_type": "bearer", "user": {"id": user_id, "username": request.username, "full_name": request.full_name}}

@app.post("/api/auth/login")
async def login(request: AuthRequest):
    global _brain
    if _brain is None: _brain = Orchestrator()
    user = _brain.authenticate(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(data={"sub": str(user['id'])})
    return {"access_token": token, "token_type": "bearer", "user": user}

@app.get("/api/status")
def get_status():
    """Return real-time system metrics (Public for now or shared)"""
    base_stats = system_controller.get_system_status()
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    return {
        "cpu": base_stats.get("cpu_percent", 0),
        "ram": ram.percent,
        "disk": disk.percent,
        "battery": base_stats.get("battery_percent", 100),
        "is_charging": base_stats.get("is_charging", True),
        "has_google_creds": os.path.exists("configs/google_credentials.json")
    }

@app.get("/api/history")
async def get_history(user = Depends(get_current_user)):
    """Get recent conversation history for authenticated user"""
    global _brain
    if _brain is None: _brain = Orchestrator()
    return _brain.memory.get_recent_context(user['id'])

@app.post("/api/history/clear")
async def clear_user_history(user = Depends(get_current_user)):
    """Clear history for authenticated user"""
    from core.orchestrator.brain import clear_history
    clear_history(user['id'])
    return {"success": True, "message": "History cleared"}

@app.get("/api/facts")
async def get_facts(user = Depends(get_current_user)):
    """Get all stored facts about the user"""
    global _brain
    if _brain is None: _brain = Orchestrator()
    return _brain.memory.get_all_facts(user['id'])

@app.get("/api/calendar")
async def get_calendar(user = Depends(get_current_user)):
    """Get upcoming calendar events"""
    global _brain
    if _brain is None: _brain = Orchestrator()
    try:
        skill = _brain.router.skills.get("calendar")
        if skill:
            result = await skill._handle_list("what's on my schedule today", {"user_id": user['id']})
            return result
        return {"success": False, "message": "Calendar skill not available"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/chat")
async def chat(request: ChatRequest, user = Depends(get_current_user)):
    """Process a natural language command"""
    try:
        response = await handle(request.text, user_id=user['id'], image=request.image, language=request.language, tone=request.tone)
        return {
            "response": response.display_text,
            "data": response.data
        }
    except Exception as e:
        return {"error": str(e), "response": f"Error: {e}"}

@app.post("/api/system/save-image")
async def save_image(request: SaveImageRequest, user = Depends(get_current_user)):
    """Save an image (capture or screenshot) to the local filesystem"""
    success, path = system_controller.save_image(request.image, request.prefix)
    if success:
        return {"success": True, "path": path}
    return {"success": False, "message": path}

class AvatarRequest(BaseModel):
    avatar_url: str

@app.post("/api/user/avatar")
async def update_avatar(request: AvatarRequest, user = Depends(get_current_user)):
    """Update user's profile avatar"""
    global _brain
    if _brain is None: _brain = Orchestrator()
    _brain.memory.update_user_avatar(user['id'], request.avatar_url)
    return {"success": True}

# Run with: uvicorn apps.api.main:app --host 0.0.0.0 --port 8000
