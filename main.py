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

class Obstacle:
    def __init__(self, canvas, x, y, speed):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.speed = speed
        self.img = ImageTk.PhotoImage(Image.open("assets/cactus.png").resize((50, 85)))
        self.id = canvas.create_image(x, y, image=self.img, anchor="nw")
        self.width = 50

    def update(self):
        self.x -= self.speed
        self.canvas.coords(self.id, self.x, self.y)
        if self.x + self.width < 0:
            self.canvas.delete(self.id)
            return True
        return False

root = tk.Tk()
root.geometry(f"{BASE_W}x{BASE_H}")

canvas = tk.Canvas(root, width=BASE_W, height=BASE_H, bg="#87CEEB")
canvas.pack()

ground_img = ImageTk.PhotoImage(Image.open("assets/ground102.png").resize((BASE_W, 100)))
canvas.create_image(0, BASE_GROUND - 10, image=ground_img, anchor="nw")

dino = Dino(canvas, 150, BASE_GROUND - 85)

obstacles = []
speed = 10

def spawn_obstacle():
    obs = Obstacle(canvas, BASE_W, BASE_GROUND - 85, speed)
    obstacles.append(obs)
    delay = random.randint(MIN_SPAWN_DELAY, MAX_SPAWN_DELAY)
    root.after(delay, spawn_obstacle)

def game_loop():
    dino.update_physics()
    for obs in obstacles[:]:
        if obs.update():
            obstacles.remove(obs)
    root.after(50, game_loop)

def on_jump(event):
    dino.jump()

root.bind("<space>", on_jump)
root.bind("<Up>", on_jump)

spawn_obstacle()
game_loop()
root.mainloop()