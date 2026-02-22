import asyncio
import sys
from core.orchestrator.brain import handle

async def main():
    """Text-based interaction with VOX for testing personality and skills"""
    print("--- VOX TEXT CHAT MODE ---")
    print("Type your message to talk to Vox. Type 'exit' to quit.")
    
    while True:
        try:
            user_input = input("\nAlok: ")
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("Vox: See you later, Alok.")
                break
                
            if not user_input.strip():
                continue
                
            # Process through the unified brain
            reply = await handle(user_input)
            print(f"Vox: {reply.display_text}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
