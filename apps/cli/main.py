import asyncio
import sys
import threading
from core.io.hotword import wait_for_hotword
from core.io.stt import transcribe_once
from core.orchestrator.brain import handle
from core.orchestrator.proactive_engine import ProactiveEngine
from core.io.tts import speak
from apps.macos_gui.overlay import update_vox_ui

from apps.cli.tui import get_tui, get_console
from rich.live import Live

# Global TUI and Console
tui = get_tui()
console = get_console()

async def vox_speak(text: str):
    """Voice output helper using the VOX TTS engine"""
    tui.add_message("Vox", text)
    speak(text)

async def vox_logic():
    """Background logic loop for VOX"""
    tui.update_status("Logic Engine Online")
    
    # Initialize proactive engine
    proactive = ProactiveEngine(vox_speak)
    asyncio.create_task(proactive.run())
    
    try:
        while True:
            # Update system metrics in the UI
            sys_stats = proactive.system.get_system_status()
            tui.update_system(
                f"{sys_stats['cpu_percent']}%", 
                f"{sys_stats['battery_percent']}%",
                "Charging" if sys_stats['is_charging'] else "Stable"
            )
            
            tui.update_status("Waiting for wake word... (Or press Enter)")
            loop = asyncio.get_running_loop()
            word = await loop.run_in_executor(None, wait_for_hotword)
            
            if word == "hey_vox":
                tui.update_status("Listening to Alok...")
                proactive.notify_interaction()
                
                # Transcribe
                text = transcribe_once(timeout=7.0)
                if not text:
                    tui.update_status("Whisper error - falling back to text")
                    loop = asyncio.get_running_loop()
                    text = await loop.run_in_executor(None, input, "Alok (text): ")
                
                if not text or text.strip() == "":
                    tui.update_status("No input detected.")
                    continue
                    
                tui.add_message("Alok", text)
                tui.update_status("Vox is thinking...")
                
                # Process command
                reply = await handle(text)
                await vox_speak(reply.display_text)
                
    except Exception as e:
        tui.add_message("System", f"Logic Error: {e}")

def main():
    """TUI entry point"""
    from core.io.hotword import init_detector
    from core.io.stt import init_stt
    
    print("Starting VOX Engine Initialization...")
    try:
        init_detector() 
        init_stt() 
        print("Engines Ready.")
    except Exception as e:
        print(f"Startup Error: {e}")
        time.sleep(2)
        return

    # Now start the Live TUI
    with Live(tui.layout, console=console, refresh_per_second=4, screen=True) as live:
        tui.update_status("Ready.")
        
        # We need a background task to keep the layout updated from TUI state
        async def ui_refresher():
            while True:
                tui.render()
                await asyncio.sleep(0.2)
        
        async def run_all():
            asyncio.create_task(ui_refresher())
            await vox_logic()

        # Run logic directly in current event loop
        asyncio.run(run_all())

if __name__ == "__main__":
    main()
