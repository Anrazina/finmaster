import tkinter as tk
from tkinter import messagebox
import threading
import time


class ClickerGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Spacebar Clicker Game")

        self.score = 0
        self.points_per_click = 1
        self.points_per_second = 0
        self.high_score = 0

        self.upgrade1_base_cost = 10
        self.upgrade2_base_cost = 50
        self.auto_clicker_base_cost = 100

        self.upgrade1_cost = self.upgrade1_base_cost
        self.upgrade2_cost = self.upgrade2_base_cost
        self.auto_clicker_cost = self.auto_clicker_base_cost

        self.score_label = tk.Label(root, text=f"Score: {self.score}", font=("Helvetica", 16))
        self.score_label.pack(pady=20)

        self.upgrade1_button = tk.Button(root, text=f"Upgrade 1 (+1 per click) - Cost: {self.upgrade1_cost}", command=self.upgrade1)
        self.upgrade1_button.pack(pady=10)

        self.upgrade2_button = tk.Button(root, text=f"Upgrade 2 (+5 per click) - Cost: {self.upgrade2_cost}", command=self.upgrade2)
        self.upgrade2_button.pack(pady=10)

        self.auto_clicker_button = tk.Button(root, text=f"Auto-clicker (+1 per second) - Cost: {self.auto_clicker_cost}", command=self.buy_auto_clicker)
        self.auto_clicker_button.pack(pady=10)

        self.high_score_label = tk.Label(root, text=f"High Score: {self.high_score}", font=("Helvetica", 16))
        self.high_score_label.pack(pady=20)

        self.root.bind('<KeyRelease-space>', self.on_spacebar_release)

        self.auto_clicker_active = False
        self.start_auto_clicker()

    def on_spacebar_release(self, event):
        self.score += self.points_per_click
        self.update_gui()
        self.show_feedback()

    def upgrade1(self):
        if self.score >= self.upgrade1_cost:
            self.score -= self.upgrade1_cost
            self.points_per_click += 1
            self.upgrade1_cost = int(self.upgrade1_cost * 1.5)
            self.update_gui()

    def upgrade2(self):
        if self.score >= self.upgrade2_cost:
            self.score -= self.upgrade2_cost
            self.points_per_click += 5
            self.upgrade2_cost = int(self.upgrade2_cost * 1.5)
            self.update_gui()

    def buy_auto_clicker(self):
        if self.score >= self.auto_clicker_cost:
            self.score -= self.auto_clicker_cost
            self.points_per_second += 1
            self.auto_clicker_cost = int(self.auto_clicker_cost * 1.5)
            self.update_gui()

    def start_auto_clicker(self):
        def auto_click():
            while True:
                if self.points_per_second > 0:
                    self.score += self.points_per_second
                    self.update_gui()
                time.sleep(1)

        threading.Thread(target=auto_click, daemon=True).start()

    def update_gui(self):
        self.score_label.config(text=f"Score: {self.score}")
        self.upgrade1_button.config(text=f"Upgrade 1 (+1 per click) - Cost: {self.upgrade1_cost}")
        self.upgrade2_button.config(text=f"Upgrade 2 (+5 per click) - Cost: {self.upgrade2_cost}")
        self.auto_clicker_button.config(text=f"Auto-clicker (+1 per second) - Cost: {self.auto_clicker_cost}")
        if self.score > self.high_score:
            self.high_score = self.score
            self.high_score_label.config(text=f"High Score: {self.high_score}")
        self.root.update()

    def show_feedback(self):
        feedback_label = tk.Label(self.root, text="+1", font=("Helvetica", 16), fg="green")
        feedback_label.place(x=200, y=100)
        self.root.after(500, feedback_label.destroy)  # Remove the label after 0.5 seconds


if __name__ == "__main__":
    root = tk.Tk()
    game = ClickerGame(root)
    root.mainloop()
