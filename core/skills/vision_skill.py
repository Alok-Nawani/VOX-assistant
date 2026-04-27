import os
import google.generativeai as genai
from typing import Dict, Any
from ..system.controller import SystemController

class VisionSkill:
    """Uses Gemini Vision to analyze the user's screen"""
    
    def __init__(self):
        self.controller = SystemController()
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if not self.model:
            return {"success": False, "message": "My visual cortex is offline. Missing API key."}
            
        raw_text = params.get("raw_text", "What is on this screen?")
        
        # 1. Take a screenshot
        success, path_or_err = self.controller.take_screenshot()
        if not success:
            return {"success": False, "message": "I failed to capture the screen."}
            
        # 2. Upload to Gemini and Analyze
        try:
            import PIL.Image
            img = PIL.Image.open(path_or_err)
            
            prompt = f"The user asked: '{raw_text}'. Look at this screenshot of their desktop and provide a concise, helpful answer. Don't start by saying 'This is a screenshot' or 'I see'. Just answer directly like a smart assistant."
            
            response = self.model.generate_content([prompt, img])
            text_resp = response.text.strip()
            
            # 3. Clean up the screenshot
            try:
                os.remove(path_or_err)
            except:
                pass
                
            return {"success": True, "message": text_resp}
            
        except Exception as e:
            # Clean up on error
            try:
                if os.path.exists(path_or_err):
                    os.remove(path_or_err)
            except:
                pass
            return {"success": False, "message": f"I had trouble analyzing the image: {e}"}
