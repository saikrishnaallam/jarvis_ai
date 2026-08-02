# ui_engine.py: Floating Siri-like circular desktop orb for Jarvis
import tkinter as tk
import math
import time
import os

class UIEngine:
    def __init__(self):
        self.state = "IDLE"      # IDLE, LISTENING, THINKING, SPEAKING
        self.amplitude = 0.0
        self.running = True
        
        # Instantiate Tkinter on the main thread
        self.root = tk.Tk()
        self.root.title("Jarvis UI")
        
        # Borderless, floating on top
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        
        # Transparent window background on macOS
        self.root.configure(bg='systemTransparent')
        
        # Define window size
        self.width = 200
        self.height = 200
        
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
        
        # Make the window moveable (click and drag)
        self.root.bind("<Button-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.drag)
        self.drag_x = 0
        self.drag_y = 0
        
        # Load the avatar image
        avatar_path = "avatar.png"
        if os.path.exists(avatar_path):
            try:
                # Subsample 998x1024 by 10 to fit in 100x100 area
                self.avatar_img = tk.PhotoImage(file=avatar_path).subsample(10, 10)
            except Exception as e:
                print(f"[UI Warning] Failed to load avatar image: {e}")
                self.avatar_img = None
        else:
            print("[UI Warning] avatar.png not found.")
            self.avatar_img = None
            
        # Render first frames
        self.tick = 0
        self.animate()
        
    def start_drag(self, event):
        self.drag_x = event.x
        self.drag_y = event.y
        
    def drag(self, event):
        deltax = event.x - self.drag_x
        deltay = event.y - self.drag_y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")
        
    def start(self):
        """Starts the Tkinter main loop (must be called on the main thread)."""
        self.root.mainloop()

    def set_state(self, state: str):
        self.state = state
        
    def set_amplitude(self, amplitude: float):
        self.amplitude = amplitude

    def animate(self):
        if not self.running:
            return
            
        self.tick += 1
        try:
            self.canvas.delete("all")
            cx, cy = self.width / 2, self.height / 2
            
            # 1. Draw glowing background rings based on current state
            if self.state == "IDLE":
                # Idle State: A soft breathing white/gray glow ring behind the face
                pulse = 58 + 2 * math.sin(self.tick * 0.05)
                self.canvas.create_oval(cx - pulse, cy - pulse, cx + pulse, cy + pulse, 
                                        fill="", outline="#ffffff", width=2)
                
            elif self.state == "LISTENING":
                # Listening State: Pulsing cyan/blue glowing rings
                pulse = 62 + 8 * math.sin(self.tick * 0.15)
                # Outer ring
                self.canvas.create_oval(cx - pulse - 8, cy - pulse - 8, cx + pulse + 8, cy + pulse + 8, 
                                        fill="", outline="#00a8ff", width=2)
                # Inner glow ring
                self.canvas.create_oval(cx - pulse, cy - pulse, cx + pulse, cy + pulse, 
                                        fill="", outline="#00f0ff", width=3)
                
            elif self.state == "THINKING":
                # Thinking State: Rotating/shifting purple/magenta morphing rings
                pulse = 64 + 5 * math.sin(self.tick * 0.25)
                offset_x = 4 * math.cos(self.tick * 0.2)
                offset_y = 4 * math.sin(self.tick * 0.2)
                
                # Outer ring
                self.canvas.create_oval(cx - pulse - 6 + offset_x, cy - pulse - 6 + offset_y, 
                                        cx + pulse + 6 - offset_x, cy + pulse + 6 - offset_y, 
                                        fill="", outline="#bd00ff", width=2)
                # Inner ring
                self.canvas.create_oval(cx - pulse - offset_x, cy - pulse - offset_y, 
                                        cx + pulse + offset_x, cy + pulse + offset_y, 
                                        fill="", outline="#bf57ff", width=3)
                
            elif self.state == "SPEAKING":
                # Speaking State: Green/teal dynamic rings dancing to real-time speech amplitude!
                amp_scale = min(self.amplitude, 1.0)
                pulse = 58 + (amp_scale * 35) + 3 * math.sin(self.tick * 0.1)
                
                # Dynamic outer ring
                self.canvas.create_oval(cx - pulse - 6, cy - pulse - 6, cx + pulse + 6, cy + pulse + 6, 
                                        fill="", outline="#00ffcc", width=2)
                # Dynamic inner ring
                self.canvas.create_oval(cx - pulse, cy - pulse, cx + pulse, cy + pulse, 
                                        fill="", outline="#00ff66", width=3)
            
            # 2. Draw the Avatar Image in the center (on top of the glowing rings)
            if self.avatar_img:
                img_x = cx
                img_y = cy
                
                # Apply dynamic, lifelike animations based on the current state
                if self.state == "SPEAKING":
                    amp_scale = min(self.amplitude, 1.0)
                    # Bouncy talking bobbing + amplitude jump
                    img_y += math.sin(self.tick * 0.3) * (2 + amp_scale * 10)
                    # Horizontal talking wiggle
                    img_x += math.cos(self.tick * 0.45) * (amp_scale * 3)
                elif self.state == "LISTENING":
                    # Slow, calm breathing bob while listening
                    img_y += math.sin(self.tick * 0.08) * 1.5
                elif self.state == "THINKING":
                    # Slow pondering side-to-side sway
                    img_x += math.cos(self.tick * 0.1) * 2.0
                    img_y += math.sin(self.tick * 0.05) * 1.0
                    
                self.canvas.create_image(img_x, img_y, image=self.avatar_img)
            else:
                # Fallback: draw a basic circle representing the face if avatar.png is missing
                self.canvas.create_oval(cx - 50, cy - 50, cx + 50, cy + 50, 
                                        fill="#ff4444", outline="#ffffff", width=4)
                
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
