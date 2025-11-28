import tkinter as tk
from tkinter import messagebox
import subprocess
import json
import os
import math
import threading
import time
import sys

# === CONFIGURATION ===
ANSWER_HASHES = {'task1.py': 'f57e5cb1f4532c008183057ecc94283801fcb5afe2d1c190e3dfd38c4da08042', 'task2.py': 'ef2d127de37b942baad06145e54b0c619a1f22327b2ebbcfbec78f5564afe39d', 'task3.py': '5f9c4ab08cac7457e9111a30e4664920607ea2c115a1433d7be98e97e64244ca', 'task4.py': '1fd4a3c41baa4c9d3fe0a2cd3a1af358108a16b3cdf250ad7f69b94eb2660bd6', 'task5.py': 'd3553347c81305670f0f7d034c1a8680518cb723d76dd40f7cc40e267b97fb69', 'task6.py': '095950c5b4c5cb0f9ee19ec9792dd1069a2b24bc5ce7a678ce60ca7f780d47ec', 'task7.py': '09824c32451fa519dd87d18219e430ec629439e72bc9ab173f2d537800bc3772', 'task8.py': '0b918943df0962bc7a1824c0555a389347b4febdc7cf9d1254406d80ce44e3f9', 'task9.py': 'c37191f186288f5097a7af278d3ff3d0c152f8674a0893eb48f79a417e2e4b8d', 'task10.py': '9bdb2af6799204a299c603994b8e400e4b1fd625efdb74066cc869fee42c9df3'}

CONFIG_FILE = "exam_config.json"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Система проверки задач")
        self.geometry("600x500")
        self.resizable(False, False)
        
        self.load_state()
        self.setup_ui()
        
    def load_state(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self.state = json.load(f)
            except:
                self.state = {"can_take_exam": True}
        else:
            self.state = {"can_take_exam": True}
            self.save_state()
            
    def save_state(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.state, f)
            
    def disable_exam_forever(self):
        self.state["can_take_exam"] = False
        self.save_state()
        self.setup_ui()

    def setup_ui(self):
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()
            
        # Main Container
        container = tk.Frame(self)
        container.pack(expand=True, fill="both", padx=20, pady=20)
        
        tk.Label(container, text="Менеджер проверки заданий", font=("Arial", 20, "bold")).pack(pady=20)
        
        if self.state["can_take_exam"]:
            # Exam Button
            btn_exam = tk.Button(container, text="Проверить на оценку", 
                               font=("Arial", 14, "bold"), bg="#ffcccc", fg="red",
                               command=self.start_exam)
            btn_exam.pack(pady=10, fill="x", ipady=10)
            
            tk.Label(container, text="Внимание! Одна попытка. После нажатия оценка будет выставлена.", 
                   font=("Arial", 10), fg="gray").pack(pady=5)

        # Practice Button
        btn_practice = tk.Button(container, text="Проверить не на оценку", 
                               font=("Arial", 14), bg="#ccffcc",
                               command=self.start_practice)
        btn_practice.pack(pady=10, fill="x", ipady=10)
        
        if self.state["can_take_exam"]:
             tk.Label(container, text="Если вы нажмете эту кнопку, возможность сдать на оценку пропадет навсегда.", 
                   font=("Arial", 10), fg="red").pack(pady=5)
        
        # Output Area
        self.output_text = tk.Text(container, height=10, width=60, state="disabled", font=("Consolas", 10))
        self.output_text.pack(pady=20, expand=True, fill="both")

    def run_script(self, script_name):
        if not os.path.exists(script_name):
            return None
        try:
            result = subprocess.run(
                [sys.executable, script_name], 
                capture_output=True, 
                text=True, 
                timeout=2
            )
            return result.stdout.strip()
        except Exception as e:
            return str(e)

    def check_all_tasks(self):
        correct_count = 0
        results = []
        
        for i in range(1, 11):
            script = f"task{i}.py"
            expected_hash = ANSWER_HASHES.get(script)
            
            user_output = self.run_script(script)
            
            import hashlib
            # Hash user output
            if user_output:
                # Normalize: replace commas with spaces, split, sort, join
                # This handles "112 113" vs "112, 113" vs "113 112"
                parts = user_output.replace(",", " ").split()
                parts.sort()
                normalized = " ".join(parts)
                user_hash = hashlib.sha256(normalized.encode()).hexdigest()
            else:
                user_hash = ""

            if user_hash == expected_hash:
                results.append(f"{script}: ВЕРНО")
                correct_count += 1
            else:
                # We cannot show expected answer anymore!
                results.append(f"{script}: НЕВЕРНО (Получено: {user_output})")
                    
        return correct_count, results

    def log_output(self, text):
        self.output_text.config(state="normal")
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, text)
        self.output_text.config(state="disabled")

    def start_practice(self):
        if self.state["can_take_exam"]:
            if not messagebox.askyesno("Подтверждение", "Вы уверены? Кнопка 'Проверить на оценку' исчезнет навсегда."):
                return
            self.disable_exam_forever()
            
        score, details = self.check_all_tasks()
        report = f"Результат тренировки: {score}/10\n\n" + "\n".join(details)
        self.log_output(report)

    def start_exam(self):
        if not messagebox.askyesno("Экзамен", "Начать проверку на оценку? Это действие нельзя отменить."):
            return

        # Run checks FIRST to calculate score
        score, _ = self.check_all_tasks()
        
        # Create a commit "Try" to trap cheats using the CALCULATED score
        try:
            subprocess.run(["git", "add", "."], capture_output=True)
            commit_message = f"Try ({score}/10)"
            subprocess.run(["git", "commit", "-m", commit_message, "--allow-empty"], capture_output=True)
        except Exception:
            pass
        
        # Disable exam forever immediately
        self.disable_exam_forever()
        
        # Launch Wheel of Fortune
        WheelWindow(self, score)


class WheelWindow(tk.Toplevel):
    def __init__(self, parent, final_score):
        super().__init__(parent)
        self.title("Оценка")
        self.geometry("400x400")
        self.resizable(False, False)
        self.final_score = final_score
        
        self.canvas = tk.Canvas(self, width=400, height=400, bg="white")
        self.canvas.pack()
        
        self.angle = 0
        self.speed = 20 # Initial speed
        self.is_spinning = True
        
        # Calculate target angle
        # 11 sectors (0..10). Each sector is 360/11 degrees.
        # We want the needle to point to the number.
        # Let's put 0 at top (270 deg), then 1, 2 clockwise.
        sector_angle = 360 / 11
        
        # Randomize stop position within the correct sector
        # Score 0 is at index 0.
        # We rotate the WHEEL, pointer is fixed at top (270 deg / -90 deg).
        # If we want score S to be at top, we need to rotate wheel such that S is at -90.
        # Initial: 0 is at -90.
        # To get S to -90, we rotate counter-clockwise by S * sector_angle.
        # Or clockwise by -S * sector_angle.
        
        self.target_rotation = -(self.final_score * sector_angle) 
        # Add multiple full rotations for effect
        self.target_rotation -= 360 * 5 
        
        # Current drawing angle offset
        self.current_offset = 0
        
        self.draw_wheel()
        self.spin()
        
    def draw_wheel(self):
        self.canvas.delete("all")
        cx, cy = 200, 200
        r = 150
        sectors = 11
        angle_per_sector = 360 / sectors
        
        # Draw Pointer (Fixed at top - Triangle pointing down)
        self.canvas.create_polygon(190, 20, 210, 20, 200, 50, fill="red", width=2)
        
        for i in range(sectors):
            # Calculate angles
            start_angle = i * angle_per_sector + self.current_offset
            end_angle = (i + 1) * angle_per_sector + self.current_offset
            
            # Convert to radians for text placement
            mid_angle_rad = math.radians(start_angle + angle_per_sector/2 - 90) # -90 adjustment for tkinter coords
            
            # Draw sector line (visual only, not filled arcs for simplicity, just lines)
            # self.canvas.create_line(cx, cy, ... ) 
            
            # Text position
            tx = cx + r * 0.8 * math.cos(mid_angle_rad)
            ty = cy + r * 0.8 * math.sin(mid_angle_rad)
            
            # Draw number
            color = "black"
            font = ("Arial", 12, "bold")
            if not self.is_spinning:
                 # Highlight winner
                 # To check winner, we need to check which sector is at top (-90 deg or 270 deg)
                 # Normalize angle to 0-360
                 norm_mid = (start_angle + angle_per_sector/2) % 360
                 # Top is 270 (or -90). In tkinter arc logic, 0 is East (3 o'clock), 90 is North (12 o'clock)?
                 # Wait, math.cos/sin uses standard math (0 is East).
                 # My calculation above used -90 offset.
                 # Let's simplify: Pointer is at 12 o'clock.
                 pass

            self.canvas.create_text(tx, ty, text=str(i), font=font, fill=color)
            
            # Draw ticks
            rad_line = math.radians(start_angle - 90)
            lx = cx + r * math.cos(rad_line)
            ly = cy + r * math.sin(rad_line)
            self.canvas.create_line(cx, cy, lx, ly, fill="gray")
            
        # Circle border
        self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, width=2)

    def spin(self):
        if not self.is_spinning:
            return

        # Simple linear deceleration logic simulation
        # We want to stop at target_rotation in ~5 seconds (5000ms)
        # But creating a physics-based spin is hard to land exactly on target without pre-calc.
        # Let's use an easing function.
        
        start_time = getattr(self, 'start_time', None)
        if start_time is None:
            self.start_time = time.time()
            self.duration = 10.0
            self.start_angle = 0
            self.final_angle = abs(self.target_rotation) 
            
            sector_angle = 360 / 11
            # Calculate target for Clockwise rotation (positive offset)
            # Sector S starts at S * sector_angle (relative to Top/0 at offset 0).
            # We want Sector S to end up at Top (0 degrees relative).
            # If we rotate Wheel CW (offset increases), Sector S moves further CW (away from Top).
            # Wait, if we rotate Wheel CW, the IMAGE rotates CW.
            # Sector S is at `Top + S*angle`.
            # If we rotate CW by `offset`, new pos is `Top + S*angle + offset`.
            # We want new pos to be `Top` (modulo 360).
            # `S*angle + offset = 0` => `offset = -S*angle`.
            # Or `offset = 360 - S*angle` (positive equivalent).
            # Also subtract half sector to align CENTER of sector to top.
            
            dist_to_0 = 360 - (self.final_score * sector_angle) - (sector_angle / 2)
            
            # Add 5 full spins
            self.final_val = dist_to_0 + 360 * 5
            self.current_val = 0
            
        elapsed = time.time() - self.start_time
        if elapsed >= self.duration:
            self.current_offset = self.final_val
            self.is_spinning = False
            self.draw_wheel()
            messagebox.showinfo("Результат", f"Ваша оценка: {self.final_score}")
            return
            
        # Easing: EaseOutCubic
        t = elapsed / self.duration
        t = t - 1
        ease = (t * t * t + 1)
        
        self.current_offset = self.current_val + (self.final_val - self.current_val) * ease
        
        self.draw_wheel()
        self.after(20, self.spin)

if __name__ == "__main__":
    app = App()
    app.mainloop()

