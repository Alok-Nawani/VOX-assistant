import os
import subprocess
import platform
import pyautogui
from pathlib import Path
from typing import Optional, List, Tuple, Dict
from datetime import datetime, timedelta
import shutil
import psutil

class SystemController:
    """Unified controller for system operations on macOS"""
    
    def __init__(self):
        self.os_type = platform.system().lower()
        if self.os_type == 'win32': self.os_type = 'windows'
        
        # Detect if we're running in a headless (server) environment
        self.is_headless = False
        if self.os_type == 'linux' and not os.environ.get('DISPLAY'):
            self.is_headless = True
        elif os.environ.get('VOX_SERVER_MODE') == 'true':
            self.is_headless = True
            
        if self.is_headless:
            print("Vox Core: Running in Headless/Server mode. Physical UI commands will be simulated.")
        
        pyautogui.FAILSAFE = True
        
    def check_permissions(self) -> Tuple[bool, str]:
        """Check if Vox has necessary system permissions (Accessibility on macOS)"""
        if self.os_type == 'darwin':
            # Check for Accessibility permissions using a harmless AppleScript
            script = 'tell application "System Events" to get name of first process'
            try:
                subprocess.run(['osascript', '-e', script], capture_output=True, check=True, timeout=5)
                return True, "Accessibility permissions granted."
            except subprocess.CalledProcessError:
                return False, "Accessibility permissions missing. Please grant Vox access in System Settings > Privacy & Security > Accessibility."
            except Exception as e:
                return False, f"Permission check failed: {e}"
        return True, "No specific permissions required for this platform."

    def open_app(self, app_name: str) -> Tuple[bool, str]:
        """Open a macOS application"""
        try:
            # Common app name mapping
            apps = {
                'browser': 'Safari',
                'safari': 'Safari',
                'chrome': 'Google Chrome',
                'calculator': 'Calculator',
                'calendar': 'Calendar',
                'mail': 'Mail',
                'music': 'Music',
                'photos': 'Photos',
                'terminal': 'Terminal',
                'settings': 'System Settings',
                'vscode': 'Visual Studio Code',
                'spotify': 'Spotify',
                'finder': 'Finder',
                'notes': 'Notes',
                'reminders': 'Reminders'
            }
            
            app_query = app_name.lower().strip()
            target = apps.get(app_query, app_name)
            
            print(f"Vox System: Attempting to open application '{target}'...")
            
            if self.os_type == 'darwin':
                # Try opening by name first
                result = subprocess.run(['open', '-a', target], capture_output=True, text=True)
                if result.returncode == 0:
                    return True, f"Opening {target}"
                
                print(f"Vox System: Primary open failed for '{target}': {result.stderr.strip()}")

                # Try common path
                path = f"/Applications/{target}.app"
                if os.path.exists(path):
                    subprocess.run(['open', path])
                    return True, f"Opening {target}"
                
                # Final attempt: try opening as a raw string (sometimes works for non-app binaries)
                result = subprocess.run(['open', target], capture_output=True, text=True)
                if result.returncode == 0:
                    return True, f"Opening {target}"
                    
                return False, f"Could not find application: {target}. Error: {result.stderr.strip()}"
            elif self.os_type == 'windows':
                os.system(f"start {target}")
                return True, f"Opening {target}"
            return False, "Unsupported OS for app opening"
        except Exception as e:
            print(f"Vox System Error: {e}")
            return False, f"Error opening {app_name}: {str(e)}"

    def close_app(self, app_name: str) -> Tuple[bool, str]:
        """Close a macOS application using AppleScript"""
        try:
            if self.os_type == 'darwin':
                subprocess.run(['osascript', '-e', f'tell application "{app_name}" to quit'], check=False)
                return True, f"Closing {app_name}"
            elif self.os_type == 'windows':
                subprocess.run(['taskkill', '/F', '/IM', f'{app_name}.exe'], check=False)
                return True, f"Closing {app_name}"
            return False, "Unsupported OS for app closing"
        except Exception as e:
            return False, f"Error closing {app_name}: {str(e)}"

    def control_volume(self, action: str, level: Optional[int] = None) -> Tuple[bool, str]:
        """Control system volume"""
        try:
            if action == "up":
                pyautogui.press('volumeup')
                return True, "Volume increased"
            elif action == "down":
                pyautogui.press('volumedown')
                return True, "Volume decreased"
            elif action == "mute":
                pyautogui.press('volumemute')
                return True, "Volume muted"
            elif action == "set" and level is not None:
                level = max(0, min(100, level))
                subprocess.run(['osascript', '-e', f'set volume output volume {level}'], check=False)
                return True, f"Volume set to {level}%"
            return False, "Invalid volume action"
        except Exception as e:
            return False, f"Error controlling volume: {str(e)}"
    def set_brightness(self, level: int) -> Tuple[bool, str]:
        """Set screen brightness using AppleScript"""
        try:
            if self.os_type == 'darwin':
                level = max(0, min(100, level))
                steps = int(level * 16 / 100)
                script = f'''
                tell application "System Events"
                    repeat 16 times
                        key code 145
                    end repeat
                    repeat {steps} times
                        key code 144
                    end repeat
                end tell
                '''
                subprocess.run(['osascript', '-e', script], check=False)
                return True, f"Brightness set to {level}%"
            return False, "Unsupported OS for brightness control"
        except Exception as e:
            return False, f"Error setting brightness: {str(e)}"

    def system_power(self, action: str) -> Tuple[bool, str]:
        """Control system power states"""
        try:
            if self.os_type == 'darwin':
                if action == "sleep":
                    os.system("pmset sleepnow")
                    return True, "Putting system to sleep"
                elif action == "lock":
                    subprocess.run(['pmset', 'displaysleepnow'], check=False)
                    return True, "Locking system"
            elif self.os_type == 'windows':
                if action == "sleep":
                    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                    return True, "System sleeping"
                elif action == "lock":
                    os.system("rundll32.exe user32.dll,LockWorkStation")
                    return True, "System locked"
            return False, "Unsupported OS or action"
        except Exception as e:
            return False, f"Error with system power: {str(e)}"

    def take_screenshot(self) -> Tuple[bool, str]:
        """Capture a screenshot"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            folder = os.path.join(str(Path.home()), "Pictures", "Vox")
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, f"Screenshot_{timestamp}.png")
            
            if self.os_type == 'darwin':
                result = subprocess.run(['screencapture', '-x', path], check=False)
                if result.returncode != 0:
                    pyautogui.screenshot(path)
            else:
                pyautogui.screenshot(path)
                
            if os.path.exists(path):
                return True, path
            else:
                return False, "Screenshot file was not created."
        except Exception as e:
            return False, f"Error taking screenshot: {str(e)}"

    def save_image(self, base64_data: str, prefix: str = "Capture") -> Tuple[bool, str]:
        """Save a base64 encoded image to the local filesystem"""
        try:
            import base64
            from io import BytesIO
            from PIL import Image
            
            # Clean data URL if present
            if "base64," in base64_data:
                base64_data = base64_data.split("base64,")[1]
            
            # Decode and open image
            img_data = base64.b64decode(base64_data)
            img = Image.open(BytesIO(img_data))
            
            # Define save path
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            folder = os.path.join(str(Path.home()), "Pictures", "Vox")
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, f"{prefix}_{timestamp}.png")
            
            # Save
            img.save(path)
            
            location_type = "Cloud Storage" if self.is_headless else "Local System"
            return True, f"{location_type}@{path}"
        except Exception as e:
            return False, f"Failed to secure optical data: {str(e)}"

    def get_system_status(self) -> Dict:
        """Get current system metrics (CPU, Battery)"""
        status = {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "battery_percent": 100,
            "is_charging": True
        }
        
        try:
            battery = psutil.sensors_battery()
            if battery:
                status["battery_percent"] = battery.percent
                status["is_charging"] = battery.power_plugged
        except:
            pass
            
        return status

    def get_usb_devices(self) -> List[str]:
        """Get list of connected USB devices"""
        try:
            result = subprocess.run(['system_profiler', 'SPUSBDataType'], capture_output=True, text=True)
            devices = []
            for line in result.stdout.split('\n'):
                if "Product ID:" in line: # Simple heuristic for new device entries
                    devices.append(line.strip())
            return devices
        except:
            return []
