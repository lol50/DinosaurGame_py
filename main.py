import tkinter as tk
from PIL import Image, ImageTk
import random, os, json, sys
import time

BASE_W, BASE_H = 1200, 600
BASE_GROUND = BASE_H - 85
MIN_SPAWN_DELAY = 1800
MAX_SPAWN_DELAY = 3200

class Dino:
    def __init__(self, canvas, x, y):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.ground_y = y
        self.vy = 0
        self.jumping = False
        self.img = ImageTk.PhotoImage(Image.open("assets/dino.png").resize((100, 85)))
        self.id = canvas.create_image(x, y, image=self.img, anchor="nw")

    def jump(self):
        if not self.jumping:
            self.jumping = True
            self.vy = -18

    def update_physics(self):
         if self.jumping:
            self.vy += 1.2
            self.y += self.vy
            if self.y >= self.ground_y:
                self.y = self.ground_y
                self.jumping = False
                self.vy = 0
            self.canvas.coords(self.id, self.x, self.y)

    def hitbox(self):
        return (self.x + 10, self.y + 10, self.x + 90, self.y + 75)

class Obstacle:
    def __init__(self, canvas, x, y, speed):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.speed = speed
        self.img = ImageTk.PhotoImage(Image.open("assets/cactus.png").resize((50, 85)))
        self.id = canvas.create_image(x, y, image=self.img, anchor="nw")
        self.width = 50
        self.height = 85

    def update(self):
        self.x -= self.speed
        self.canvas.coords(self.id, self.x, self.y)
        if self.x + self.width < 0:
            self.canvas.delete(self.id)
            return True
        return False

    def hitbox(self):
        return (self.x + 10, self.y + 10, self.x + self.width - 10, self.y + self.height - 10)

class DinoGame:
    def __init__(self, root):
        self.root = root
        root.title("Dinosaur Game")
        root.geometry(f"{BASE_W}x{BASE_H}")
        self.canvas = tk.Canvas(root, width=BASE_W, height=BASE_H, bg="#87CEEB")
        self.canvas.pack()

        self.ground_img = ImageTk.PhotoImage(Image.open("assets/ground102.png").resize((BASE_W, 100)))
        self.canvas.create_image(0, BASE_GROUND - 10, image=self.ground_img, anchor="nw")

        self.dino = Dino(self.canvas, 150, BASE_GROUND - 85)

        self.obstacles = []
        self.speed = 10
        self.max_speed = 30
        self.next_speed_increase = 500

        self.score = 0
        self.high_score = 0
        self.load_high_score()

        self.score_text = self.canvas.create_text(BASE_W - 80, 30, text=f"Счёт: {self.score}",
                                                  font=("Arial", 18, "bold"), fill="black")
        self.high_score_text = self.canvas.create_text(BASE_W - 80, 60, text=f"Рекорд: {self.high_score}",
                                                       font=("Arial", 14, "bold"), fill="black")

        self.game_over = False

        self.root.bind("<space>", self.on_jump)
        self.root.bind("<Up>", self.on_jump)

        self.spawn_obstacle()
        self.update_score()
        self.game_loop()

    def load_high_score(self):
        if os.path.exists("high_score.json"):
            with open("high_score.json", "r") as f:
                data = json.load(f)
                self.high_score = data.get("high_score", 0)

    def save_high_score(self):
        with open("high_score.json", "w") as f:
            json.dump({"high_score": self.high_score}, f)

    def update_score(self):
        if self.game_over:
            return
        self.score += 1
        self.canvas.itemconfig(self.score_text, text=f"Счёт: {self.score}")
        if self.score > self.high_score:
            self.high_score = self.score
            self.canvas.itemconfig(self.high_score_text, text=f"Рекорд: {self.high_score}")
            self.save_high_score()

        if self.score >= self.next_speed_increase and self.speed < self.max_speed:
            self.speed += 3
            self.next_speed_increase += 500

        self.root.after(500, self.update_score)

    def spawn_obstacle(self):
        if self.game_over:
            return
        obs = Obstacle(self.canvas, BASE_W, BASE_GROUND - 85, self.speed)
        self.obstacles.append(obs)
        delay = random.randint(MIN_SPAWN_DELAY, MAX_SPAWN_DELAY)
        self.root.after(delay, self.spawn_obstacle)

    def check_collisions(self):
        dino_box = self.dino.hitbox()
        for obs in self.obstacles:
            obs_box = obs.hitbox()
            if (dino_box[0] < obs_box[2] and dino_box[2] > obs_box[0] and
                dino_box[1] < obs_box[3] and dino_box[3] > obs_box[1]):
                self.game_over = True
                return True
        return False

    def game_loop(self):
        if not self.game_over:
            self.dino.update_physics()
            for obs in self.obstacles[:]:
                if obs.update():
                    self.obstacles.remove(obs)
            self.check_collisions()
            self.root.after(50, self.game_loop)

    def on_jump(self, event):
        if not self.game_over:
            self.dino.jump()

if __name__ == "__main__":
    root = tk.Tk()
    game = DinoGame(root)
    root.mainloop()