import Cocoa
import objc
from Foundation import NSObject, NSTimer
from AppKit import (NSWindow, NSWindowStyleMaskBorderless, NSColor, 
                   NSScreen, NSView, NSBezierPath, NSFont, 
                   NSForegroundColorAttributeName, NSFontAttributeName)

class VoxOverlayView(NSView):
    def initWithFrame_(self, frame):
        self = objc.super(VoxOverlayView, self).initWithFrame_(frame)
        if self:
            self.message = "Vox is listening..."
        return self

    def drawRect_(self, rect):
        path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(self.bounds(), 20, 20)
        
        # Glassmorphic background
        NSColor.colorWithDeviceRed_green_blue_alpha_(0.1, 0.1, 0.1, 0.8).set()
        path.fill()
        
        # Subtle border
        NSColor.colorWithDeviceRed_green_blue_alpha_(1, 1, 1, 0.2).set()
        path.setLineWidth_(1.5)
        path.stroke()
        
        # Message text
        attributes = {
            NSFontAttributeName: NSFont.fontWithName_size_("Helvetica-Bold", 14),
            NSForegroundColorAttributeName: NSColor.whiteColor()
        }
        
        text_rect = Cocoa.NSMakeRect(20, self.bounds().size.height/2 - 10, self.bounds().size.width - 40, 20)
        self.message.drawInRect_withAttributes_(text_rect, attributes)

    def setMessage_(self, msg):
        self.message = msg
        self.display()

class VoxOverlayController(NSObject):
    def initWithCallback_(self, callback):
        self = objc.super(VoxOverlayController, self).init()
        if self:
            self.logic_callback = callback
        return self

    def applicationDidFinishLaunching_(self, notification):
        screen_frame = NSScreen.mainScreen().frame()
        width, height = 300, 80
        x = (screen_frame.size.width - width) / 2
        y = 100 # Position near bottom
        
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            Cocoa.NSMakeRect(x, y, width, height),
            NSWindowStyleMaskBorderless,
            Cocoa.NSBackingStoreBuffered,
            False
        )
        
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(NSColor.clearColor())
        self.window.setLevel_(Cocoa.NSStatusWindowLevel)
        self.window.setIgnoresMouseEvents_(True)
        self.window.setHasShadow_(True)
        
        self.view = VoxOverlayView.alloc().initWithFrame_(self.window.contentView().bounds())
        self.window.setContentView_(self.view)
        self.window.makeKeyAndOrderFront_(None)
        # self.startPulse() # Temporarily disabled for stability
        
        # Start background logic only after window is ready
        if hasattr(self, 'logic_callback') and self.logic_callback:
            self.logic_callback()

    def updateMessage_(self, msg):
        self.view.setMessage_(msg)

    # def startPulse(self): ...
    # def pulse_(self, timer): ...

# Global controller
_overlay = None

def start_overlay(callback=None):
    global _overlay
    from PyObjCTools import AppHelper
    
    app = Cocoa.NSApplication.sharedApplication()
    app.setActivationPolicy_(Cocoa.NSApplicationActivationPolicyAccessory)
    
    _overlay = VoxOverlayController.alloc().initWithCallback_(callback)
    app.setDelegate_(_overlay)

def update_vox_ui(text):
    if _overlay:
        _overlay.performSelectorOnMainThread_withObject_waitUntilDone_(
            "updateMessage:", text, False
        )

if __name__ == "__main__":
    from PyObjCTools import AppHelper
    start_overlay()
    AppHelper.runEventLoop()
