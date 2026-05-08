import tkinter as tk
from PIL import Image, ImageTk
import random, os, json, sys
import time

BASE_W, BASE_H = 1200, 600
BASE_GROUND = BASE_H - 85

class Dino:
    def __init__(self, canvas, x, y):
        self.canvas = canvas
        self.img = ImageTk.PhotoImage(Image.open("assets/dino.png").resize((100, 85)))
        self.id = canvas.create_image(x, y, image=self.img, anchor="nw")

class Obstacle:
    def __init__(self, canvas, x, y):
        self.canvas = canvas
        self.img = ImageTk.PhotoImage(Image.open("assets/cactus.png").resize((50, 85)))
        self.id = canvas.create_image(x, y, image=self.img, anchor="nw")

root = tk.Tk()
root.geometry(f"{BASE_W}x{BASE_H}")

canvas = tk.Canvas(root, width=BASE_W, height=BASE_H, bg="#87CEEB")
canvas.pack()

ground_img = ImageTk.PhotoImage(Image.open("assets/ground102.png").resize((BASE_W, 100)))
canvas.create_image(0, BASE_GROUND - 10, image=ground_img, anchor="nw")

dino = Dino(canvas, 150, BASE_GROUND - 85)
obstacle = Obstacle(canvas, 800, BASE_GROUND - 85)

root.mainloop()