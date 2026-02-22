import asyncio
import os
import sys

# Add the project root to path
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

from core.skills.whatsapp_skill import WhatsAppSkill

async def test_vox_dispatch():
    skill = WhatsAppSkill()
    params = {
        "raw_text": "Hey Nidhi, what's the plan for lunch? send this to nidhi in whatsapp",
        "history": [],
        "facts": {}
    }
    
    print("STAGING: Initiating Vox Dispatch Test...")
    result = await skill.execute(params)
    print(f"RESULT: {result}")

if __name__ == "__main__":
    asyncio.run(test_vox_dispatch())
