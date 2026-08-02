# ui_engine.py: Floating Siri-like circular desktop orb for Jarvis
import tkinter as tk
import threading
import math
import time

class UIEngine(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.state = "IDLE"      # IDLE, LISTENING, THINKING, SPEAKING
        self.amplitude = 0.0
        self.running = True
        self.root = None
        self.canvas = None
        
    def set_state(self, state: str):
        self.state = state
        
    def set_amplitude(self, amplitude: float):
        self.amplitude = amplitude

    def run(self):
        self.root = tk.Tk()
        self.root.title("Jarvis UI")
        
        # Borderless, floating on top
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        
        # Transparent window background on macOS
        self.root.configure(bg='systemTransparent')
        
        # Define window size
        self.width = 160
        self.height = 160
        
        # Center horizontally at the bottom of the screen (above Dock)
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - self.width) // 2
        y = sh - self.height - 120  # Adjusted to float nicely above standard macOS Dock
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")
        
        # Transparent Canvas
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, 
                                bg='systemTransparent', highlightthickness=0)
        self.canvas.pack()
        
        # Render first frames
        self.tick = 0
        self.animate()
        
        self.root.mainloop()

    def animate(self):
        if not self.running:
            return
            
        self.tick += 1
        try:
            self.canvas.delete("all")
            
            cx, cy = self.width / 2, self.height / 2
            
            if self.state == "IDLE":
                # Idle State: A small, soft breathing white/gray indicator
                pulse = 12 + 2 * math.sin(self.tick * 0.05)
                # Soft outer glow
                self.canvas.create_oval(cx - pulse - 4, cy - pulse - 4, cx + pulse + 4, cy + pulse + 4, 
                                        fill="", outline="#ffffff", width=1)
                # Inner solid core
                self.canvas.create_oval(cx - pulse, cy - pulse, cx + pulse, cy + pulse, 
                                        fill="#e0e0e0", outline="")
                
            elif self.state == "LISTENING":
                # Listening State: Pulsing cyan/blue orb
                pulse = 30 + 8 * math.sin(self.tick * 0.15)
                # Outer halo
                self.canvas.create_oval(cx - pulse - 12, cy - pulse - 12, cx + pulse + 12, cy + pulse + 12, 
                                        fill="", outline="#00a8ff", width=2)
                # Middle glow
                self.canvas.create_oval(cx - pulse - 6, cy - pulse - 6, cx + pulse + 6, cy + pulse + 6, 
                                        fill="", outline="#00f0ff", width=3)
                # Inner core
                self.canvas.create_oval(cx - pulse, cy - pulse, cx + pulse, cy + pulse, 
                                        fill="#00f3ff", outline="")
                
            elif self.state == "THINKING":
                # Thinking State: Rotating/shifting purple/magenta morphing orb
                pulse = 32 + 5 * math.sin(self.tick * 0.25)
                offset_x = 4 * math.cos(self.tick * 0.2)
                offset_y = 4 * math.sin(self.tick * 0.2)
                
                # Outer magic ring
                self.canvas.create_oval(cx - pulse - 10 + offset_x, cy - pulse - 10 + offset_y, 
                                        cx + pulse + 10 - offset_x, cy + pulse + 10 - offset_y, 
                                        fill="", outline="#bd00ff", width=2)
                # Inner morphing core
                self.canvas.create_oval(cx - pulse - offset_x, cy - pulse - offset_y, 
                                        cx + pulse + offset_x, cy + pulse + offset_y, 
                                        fill="#bf57ff", outline="")
                
            elif self.state == "SPEAKING":
                # Speaking State: Green/teal orb that dances to the real-time speech amplitude!
                # Amplitude values are typically 0.0 to 1.0
                amp_scale = min(self.amplitude, 1.0)
                pulse = 28 + (amp_scale * 45) + 3 * math.sin(self.tick * 0.1)
                
                # Dynamic outer voice ring
                self.canvas.create_oval(cx - pulse - 8, cy - pulse - 8, cx + pulse + 8, cy + pulse + 8, 
                                        fill="", outline="#00ffcc", width=2)
                # Dynamic core
                self.canvas.create_oval(cx - pulse, cy - pulse, cx + pulse, cy + pulse, 
                                        fill="#00ff66", outline="")
        except Exception:
            pass  # Handle window closing race conditions
            
        # Schedule next animation frame (approx 30 FPS)
        if self.running:
            self.root.after(33, self.animate)

    def close(self):
        self.running = False
        if self.root:
            try:
                self.root.destroy()
            except Exception:
                pass
