import os
import time
import pyautogui
import pyperclip
import platform
import logging
from typing import Optional

class WhatsAppAutomation:
    """Automates WhatsApp Desktop using GUI automation"""
    
    def __init__(self):
        """Initialize WhatsApp automation"""
        # Set up safety nets
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort
        pyautogui.PAUSE = 0.5  # Add small delay between actions
        
    def open_whatsapp(self) -> bool:
        """Opens/Activates WhatsApp Desktop using AppleScript for reliable focus"""
        try:
            if platform.system() == "Darwin":  # macOS
                # Use AppleScript to activate and bring to front
                script = 'tell application "WhatsApp" to activate'
                os.system(f"osascript -e '{script}'")
                time.sleep(2) # Give it time to focus
                return True
            elif platform.system() == "Windows":
                os.system("start WhatsApp")
                time.sleep(3)
                return True
            return False
        except Exception as e:
            logging.error(f"Error opening WhatsApp: {e}")
            return False
            
    def search_contact(self, contact_name: str) -> bool:
        """Search for a contact in WhatsApp
        
        Args:
            contact_name: Name of the contact to search for
            
        Returns:
            bool: True if contact was found and selected
        """
        try:
            # Click on search button (at the top)
            pyautogui.click(x=200, y=50)
            time.sleep(1)
            
            # Clear any existing search
            if platform.system() == "Darwin":
                pyautogui.hotkey("command", "a")
            else:
                pyautogui.hotkey("ctrl", "a")
            pyautogui.press("backspace")
            time.sleep(0.5)
            
            # Type contact name
            pyperclip.copy(contact_name)
            if platform.system() == "Darwin":
                pyautogui.hotkey("command", "v")
            else:
                pyautogui.hotkey("ctrl", "v")
            time.sleep(2)  # Wait for search results
            
            # Click first contact in results
            pyautogui.click(x=200, y=120)
            time.sleep(2)  # Wait for chat to open
            return True
            
        except Exception as e:
            logging.error(f"Error searching for contact: {e}")
            return False
            
    def send_message(self, message: str) -> bool:
        """Type and send a message
        
        Args:
            message: The message text to send
            
        Returns:
            bool: True if message was sent successfully
        """
        try:
            # Click on message input area (bottom of window)
            pyautogui.click(x=400, y=700)
            time.sleep(1)
            
            # Type message
            pyperclip.copy(message)
            if platform.system() == "Darwin":
                pyautogui.hotkey("command", "v")
            else:
                pyautogui.hotkey("ctrl", "v")
            time.sleep(1)
            
            # Send message
            pyautogui.press("enter")
            time.sleep(1)
            return True
            
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            return False
            
    async def send_whatsapp_message(self, contact_name: str, message: str) -> bool:
        """Atomic WhatsApp transmission using unified, high-reliability AppleScript"""
        try:
            print(f"Vox Engine: Executing high-priority dispatch to '{contact_name}'...")
            
            # Step 1: Focus application
            if not self.open_whatsapp():
                return False
            
            is_mac = platform.system() == "Darwin"
            if not is_mac:
                # Windows fallback (Keep for cross-platform support)
                pyperclip.copy(contact_name)
                pyautogui.hotkey("ctrl", "n")
                time.sleep(1.5)
                pyautogui.hotkey("ctrl", "v")
                time.sleep(2)
                pyautogui.press("enter")
                time.sleep(1.5)
                pyperclip.copy(message)
                pyautogui.hotkey("ctrl", "v")
                time.sleep(1)
                pyautogui.press("enter")
                return True

            # macOS Ultra-Reliable Unified Script
            # Escape for AppleScript (No backslashes directly in f-string expressions for legacy python)
            contact_esc = contact_name.replace('\\', '\\\\').replace('"', '\\"')
            message_esc = message.replace('\\', '\\\\').replace('"', '\\"')
            
            import subprocess
            
            script_content = f'''
            tell application "WhatsApp" to activate
            delay 1
            tell application "System Events"
                tell process "WhatsApp"
                    set frontmost to true
                    -- 1. Trigger New Chat (Cmd+N) - Cleaner than global search
                    keystroke "n" using command down
                    delay 1.0
                    
                    -- 2. Clear Search Box just in case
                    keystroke "a" using command down
                    delay 0.2
                    key code 51 -- Backspace
                    delay 0.3
                    
                    -- 3. Type Contact Name slowly for UI to catch up
                    set the clipboard to "{contact_esc}"
                    keystroke "v" using command down
                    delay 2.5 -- Critical wait for list filter
                    
                    -- 4. Select the first contact in the results
                    keystroke return
                    delay 0.8
                    key code 36 -- Extra Return for safety
                    delay 1.5 -- Wait for chat window to transition
                    
                    -- 5. Deliver Message Content
                    set the clipboard to "{message_esc}"
                    keystroke "v" using command down
                    delay 0.5
                    
                    -- 6. Final Dispatch
                    keystroke return
                    delay 0.2
                    key code 36
                end tell
            end tell
            '''
            
            try:
                # Use subprocess with a safety timeout to avoid blocking the whole backend
                subprocess.run(["osascript", "-e", script_content], check=True, timeout=20)
                print(f"Vox Engine: Dispatch success for {contact_name}.")
                return True
            except subprocess.CalledProcessError as e:
                print(f"Vox Engine: Primary AppleScript failed or blocked ({e}). Triggering Hardware-Level Fallback...")
                # HARDWARE FALLBACK: Use PyAutoGUI for the final strokes if AppleScript is blocked
                time.sleep(1)
                pyautogui.press("enter")
                time.sleep(0.5)
                pyautogui.press("enter")
                return True
            
        except Exception as e:
            print(f"Vox Engine: Dispatch critical failure: {e}")
            return False
            
        except Exception as e:
            print(f"Vox Engine: Dispatch critical failure: {e}")
            return False
            
        except Exception as e:
            print(f"Vox Engine: Dispatch critical failure: {e}")
            return False
            
        except Exception as e:
            print(f"Error in send_whatsapp_message: {e}")
            return False
