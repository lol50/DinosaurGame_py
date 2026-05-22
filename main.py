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
        self.ground = y
        self.vy = 0
        self.jumping = False
        self.frame = 0
        self.counter = 0
        self.tex = {}

        run1 = Image.open("assets/dinomove1.png").resize((100, 85))
        run2 = Image.open("assets/dinomove2.png").resize((100, 85))
        self.tex['run1'] = ImageTk.PhotoImage(run1)
        self.tex['run2'] = ImageTk.PhotoImage(run2)

        self.cur = self.tex['run1']
        self.id = canvas.create_image(x, y, image=self.cur, anchor="nw")

    def update_animation(self):
        self.counter += 1
        if self.counter >= 6:
            self.counter = 0
            self.frame += 1
            self.cur = self.tex['run2'] if self.frame % 2 else self.tex['run1']
            self.canvas.itemconfig(self.id, image=self.cur)

    def jump(self):
        if not self.jumping:
            self.jumping = True
            self.vy = -18

    def update_physics(self):
         if self.jumping:
    def update(self):
        if self.jumping:
            self.vy += 1.2
            self.y += self.vy
            if self.y >= self.ground_y:
                self.y = self.ground_y
            if self.y >= self.ground:
                self.y = self.ground
                self.jumping = False
                self.vy = 0
                self.frame = 0
                self.counter = 0
                self.cur = self.tex['run1']
                self.canvas.itemconfig(self.id, image=self.cur)
            self.canvas.coords(self.id, self.x, self.y)
        else:
            self.update_animation()


    def hitbox(self):
        return (self.x + 10, self.y + 10, self.x + 90, self.y + 75)

    def reset(self):
        self.y = self.ground_y
        self.y = self.ground
        self.vy = 0
        self.jumping = False
        self.frame = 0
        self.counter = 0
        self.cur = self.tex['run1']
        self.canvas.itemconfig(self.id, image=self.cur)
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

class Menu:
    def __init__(self, canvas, game):
        self.canvas = canvas
        self.game = game
        self.images = {}
        self.items = []

    def load(self):
        try:
            self.images['back'] = ImageTk.PhotoImage(
                Image.open("assets/back.png").resize((BASE_W, BASE_H), Image.Resampling.LANCZOS))
            self.images['title'] = ImageTk.PhotoImage(
                Image.open("assets/dinosaurgamemenu.png").resize((500, 200), Image.Resampling.LANCZOS))
            self.images['play'] = ImageTk.PhotoImage(
                Image.open("assets/playmenu.png").resize((200, 50), Image.Resampling.LANCZOS))
            self.images['exit'] = ImageTk.PhotoImage(
                Image.open("assets/gooutmenu.png").resize((200, 50), Image.Resampling.LANCZOS))
            return True
        except:
            return False

    def show(self):
        if not self.load():
            return
        self.bg = self.canvas.create_image(0, 0, image=self.images['back'], anchor="nw")
        cx = BASE_W // 2
        self.title = self.canvas.create_image(cx, 200, image=self.images['title'], anchor="center")
        self.play_btn = self.canvas.create_image(cx, 440, image=self.images['play'], anchor="center")
        self.exit_btn = self.canvas.create_image(cx, 500, image=self.images['exit'], anchor="center")
        self.canvas.tag_bind(self.play_btn, "<Button-1>", self.game.start_game)
        self.canvas.tag_bind(self.exit_btn, "<Button-1>", lambda e: sys.exit())
        self.items = [self.bg, self.title, self.play_btn, self.exit_btn]

    def hide(self):
        for item in self.items:
            self.canvas.delete(item)
        self.items.clear()

class DinoGame:
    def __init__(self, root):
        self.root = root
        root.title("Dinosaur Game")
        root.geometry(f"{BASE_W}x{BASE_H}")
        self.canvas = tk.Canvas(root, width=BASE_W, height=BASE_H, bg="#87CEEB")
        self.canvas.pack()

        self.ground_img = ImageTk.PhotoImage(Image.open("assets/ground102.png").resize((BASE_W, 100)))
        self.canvas.create_image(0, BASE_GROUND - 10, image=self.ground_img, anchor="nw")

        self.menu = Menu(self.canvas, self)

        self.dino = None
        self.obstacles = []
        self.speed = 10
        self.max_speed = 30
        self.next_speed_increase = 500
        self.score = 0
        self.high_score = 0
        self.spawn_id = None
        self.load_high_score()

        self.score_text = None
        self.high_score_text = None
        self.game_over = False
        self.game_over_text = None

        self.root.bind("<space>", self.on_space)
        self.root.bind("<Up>", self.on_jump)
        self.menu.show()

        self.root.bind("<space>", self.on_space)
        self.root.bind("<Up>", self.on_space)

    def load_high_score(self):
        if os.path.exists("high_score.json"):
            with open("high_score.json", "r") as f:
                data = json.load(f)
                self.high_score = data.get("high_score", 0)

    def save_high_score(self):
        with open("high_score.json", "w") as f:
            json.dump({"high_score": self.high_score}, f)

    def start_game(self, event=None):
        self.menu.hide()

        self.dino = Dino(self.canvas, 150, BASE_GROUND - 85)

        self.score = 0
        self.speed = 10
        self.next_speed_increase = 500
        self.obstacles.clear()
        self.game_over = False

        if self.game_over_text:
            self.canvas.delete(self.game_over_text)
            self.game_over_text = None
        if self.spawn_id:
            self.root.after_cancel(self.spawn_id)
            self.spawn_id = None

        self.score_text = self.canvas.create_text(BASE_W - 80, 30, text=f"Счёт: {self.score}",
                                                  font=("Arial", 18, "bold"), fill="black")
        self.high_score_text = self.canvas.create_text(BASE_W - 80, 60, text=f"Рекорд: {self.high_score}",
                                                       font=("Arial", 14, "bold"), fill="black")

        self.spawn_obstacle()
        self.update()

    def update_score(self):
        if self.game_over:
            return
        self.score += 1
        if self.score_text:
            self.canvas.itemconfig(self.score_text, text=f"Счёт: {self.score}")
        if self.score > self.high_score:
            self.high_score = self.score
            if self.high_score_text:
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

    def update(self):
        if not self.game_over and self.dino:
            self.dino.update()
            for obs in self.obstacles[:]:
                if obs.update():
                    self.obstacles.remove(obs)

            dl, dt, dr, db = self.dino.hitbox()
            for obs in self.obstacles:
                ol, ot, or_, ob = obs.hitbox()
                if dl < or_ and dr > ol and dt < ob and db > ot:
                    self.game_over = True
                    self.game_over_text = self.canvas.create_text(BASE_W // 2, BASE_H // 2,
                                                                  text="GAME OVER - PRESS SPACE",
                                                                  font=("Arial", 36, "bold"), fill="red")
                    break

            self.score += 1
            if self.score_text:
                self.canvas.itemconfig(self.score_text, text=f"Счёт: {self.score}")
            if self.score > self.high_score:
                self.high_score = self.score
                if self.high_score_text:
                    self.canvas.itemconfig(self.high_score_text, text=f"Рекорд: {self.high_score}")
                self.save_high_score()
            if self.score >= self.next_speed_increase and self.speed < self.max_speed:
                self.speed += 3
                self.next_speed_increase += 500

        self.root.after(50, self.update)

    def restart_game(self):
        if self.spawn_id:
            self.root.after_cancel(self.spawn_id)
            self.spawn_id = None

        for obs in self.obstacles[:]:
            self.canvas.delete(obs.id)
        self.obstacles.clear()

        if self.dino:
            self.dino.reset()

        self.score = 0
        self.speed = 10
        self.next_speed_increase = 500
        self.game_over = False

        if self.score_text:
            self.canvas.itemconfig(self.score_text, text=f"Счёт: {self.score}")

        if self.game_over_text:
            self.canvas.delete(self.game_over_text)
            self.game_over_text = None

        self.spawn_obstacle()

    def on_space(self, event):
        if self.game_over:
            self.restart_game()
        elif self.dino:
            self.dino.jump()

if __name__ == "__main__":
    root = tk.Tk()
    game = DinoGame(root)
    root.mainloop()