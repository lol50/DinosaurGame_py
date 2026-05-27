import tkinter as tk
from PIL import Image, ImageTk
import random, os, json, sys
import time

BASE_W, BASE_H = 1200, 600
BASE_GROUND = BASE_H - 85
MIN_SPAWN_DELAY = 1800
MAX_SPAWN_DELAY = 3200

class ParallaxLayer:
    def __init__(self, canvas, path, speed, y=0, w=None, h=None, game=None):
        self.canvas = canvas
        self.game = game
        self.speed = speed
        self.w = w or game.W
        self.h = h or game.H - y
        self.y = y
        self.x1, self.x2 = 0, self.w
        try:
            img = Image.open(path).resize((self.w, self.h), Image.Resampling.LANCZOS)
            self.img = ImageTk.PhotoImage(img)
        except:
            self.img = None
            return
        self.id1 = canvas.create_image(0, self.y, image=self.img, anchor="nw")
        self.id2 = canvas.create_image(self.w, self.y, image=self.img, anchor="nw")

    def update(self, speed):
        if not self.img:
            return
        move = speed * self.speed / 8
        self.x1 -= move
        self.x2 -= move
        if self.x1 <= -self.w:
            self.x1 = self.x2 + self.w
        if self.x2 <= -self.w:
            self.x2 = self.x1 + self.w
        self.canvas.coords(self.id1, self.x1, self.y)
        self.canvas.coords(self.id2, self.x2, self.y)

    def reset(self):
        self.x1, self.x2 = 0, self.w
        self.canvas.coords(self.id1, 0, self.y)
        self.canvas.coords(self.id2, self.w, self.y)

class Dino:
    def __init__(self, canvas, x, y):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.dino_h = 85
        self.duck_h = 60
        self.ground = y + self.dino_h
        self.vy = 0
        self.jumping = False
        self.frame = 0
        self.counter = 0
        self.tex = {}
        self.ducking = False

        run1 = Image.open("assets/dinomove1.png").resize((100, 85))
        run2 = Image.open("assets/dinomove2.png").resize((100, 85))
        self.tex['run1'] = ImageTk.PhotoImage(run1)
        self.tex['run2'] = ImageTk.PhotoImage(run2)

        duck1 = Image.open("assets/dino2move1.png").resize((100, self.duck_h))
        duck2 = Image.open("assets/dino2move2.png").resize((100, self.duck_h))
        self.tex['duck1'] = ImageTk.PhotoImage(duck1)
        self.tex['duck2'] = ImageTk.PhotoImage(duck2)

        dead = Image.open("assets/dinodead.png").resize((100, self.dino_h))
        dead_duck = Image.open("assets/dino2dead.png").resize((100, self.duck_h))
        self.tex['dead'] = ImageTk.PhotoImage(dead)
        self.tex['dead_duck'] = ImageTk.PhotoImage(dead_duck)

        self.cur = self.tex['run1']
        self.id = canvas.create_image(x, y, image=self.cur, anchor="nw")

    def update_animation(self):
        self.counter += 1
        if self.counter >= 6:
            self.counter = 0
            self.frame += 1
            if self.ducking:
                self.cur = self.tex['duck2'] if self.frame % 2 else self.tex['duck1']
            else:
                self.cur = self.tex['run2'] if self.frame % 2 else self.tex['run1']
            self.canvas.itemconfig(self.id, image=self.cur)

    def jump(self):
        if not self.jumping and not self.ducking:
            self.jumping = True
            self.vy = -18

    def start_duck(self):
        if not self.jumping:
            self.ducking = True
            self.canvas.coords(self.id, self.x, self.ground - self.dino_h + (self.dino_h - self.duck_h))
            self.cur = self.tex['duck1']
            self.canvas.itemconfig(self.id, image=self.cur)

    def stop_duck(self):
        if not self.jumping:
            self.ducking = False
            self.canvas.coords(self.id, self.x, self.ground - self.dino_h)
            self.cur = self.tex['run1']
            self.canvas.itemconfig(self.id, image=self.cur)

    def set_dead(self):
        if self.ducking:
            self.cur = self.tex['dead_duck']
        else:
            self.cur = self.tex['dead']
        self.canvas.itemconfig(self.id, image=self.cur)
        self.jumping = False
        self.ducking = False

    def update(self):
        if self.jumping:
            self.vy += 1.2
            self.y += self.vy
            if self.y >= self.ground - self.dino_h:
                self.y = self.ground- self.dino_h
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
        if self.ducking:
            return (self.x + 10, self.ground - self.duck_h + 10, self.x + 90, self.ground - self.duck_h + 50)
        return (self.x + 10, self.y + 10, self.x + 90, self.y + 75)

    def reset(self):
        self.y = self.ground - self.dino_h
        self.vy = 0
        self.jumping = False
        self.ducking = False
        self.frame = 0
        self.counter = 0
        self.cur = self.tex['run1']
        self.canvas.itemconfig(self.id, image=self.cur)
        self.canvas.coords(self.id, self.x, self.y)

class Obstacle:
    def __init__(self, canvas, x, y, img, w, h, speed):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.speed = speed
        self.img = img
        self.id = canvas.create_image(x, y, image=self.img, anchor="nw")
        self.width = w
        self.height = h

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

        self.bg_layers = [
            ParallaxLayer(self.canvas, "assets/back101.png", 1, 0, BASE_W, BASE_H, self),
            ParallaxLayer(self.canvas, "assets/back102.png", 2, 0, BASE_W, BASE_H, self),
            ParallaxLayer(self.canvas, "assets/back103.png", 3, 0, BASE_W, BASE_H, self),
            ParallaxLayer(self.canvas, "assets/back104.png", 4, 0, BASE_W, BASE_H, self),
        ]

        self.ground_img = ImageTk.PhotoImage(Image.open("assets/ground102.png").resize((BASE_W, 100)))
        self.canvas.create_image(0, BASE_GROUND - 10, image=self.ground_img, anchor="nw")

        self.menu = Menu(self.canvas, self)

        self.dino = None
        self.obstacles = []
        self.tex = {}
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

        self.load_obstacle_tex()

        self.menu.show()

        self.root.bind("<space>", self.on_space)
        self.root.bind("<Up>", self.on_space)
        self.root.bind("<Down>", self.handle_down)
        self.root.bind("<KeyRelease-Down>", self.handle_down_release)

    def load_obstacle_tex(self):
        sizes = {
            'cactus1': (50, 85),
            'cactus2': (90, 85),
            'cactus3': (130, 85),
            'bird': (75, 55)
        }
        for name, file in [('cactus1', 'cactus.png'), ('cactus2', 'cactus2.png'),
                           ('cactus3', 'cactus3.png'), ('bird', 'bird.png')]:
            try:
                w, h = sizes[name]
                img = Image.open(f"assets/{file}").resize((w, h), Image.Resampling.LANCZOS)
                self.tex[name] = ImageTk.PhotoImage(img)
            except:
                pass

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

    def handle_down(self, e):
        if not self.game_over and self.dino:
            self.dino.start_duck()

    def handle_down_release(self, e):
        if not self.game_over and self.dino:
            self.dino.stop_duck()

    def spawn_obstacle(self):
        if self.game_over:
            return

        r = random.randint(1, 100)

        if self.score >= 500 and r <= 30:
            img = self.tex['bird']
            w = self.tex['bird'].width()
            h = 55
            y = BASE_GROUND - random.choice([170, 140, 110])
        else:
            typ = random.choice(['cactus1', 'cactus2', 'cactus3'])
            img = self.tex[typ]
            w = self.tex[typ].width()
            y = BASE_GROUND - 85
            h = 85

        self.obstacles.append(Obstacle(self.canvas, BASE_W, y, img, w, h, self.speed))
        delay = max(800, random.randint(MIN_SPAWN_DELAY, MAX_SPAWN_DELAY) - int(self.speed * 3))
        self.spawn_id = self.root.after(delay, self.spawn_obstacle)

    def update(self):
        if not self.game_over and self.dino:
            for layer in self.bg_layers:
                layer.update(self.speed)

            self.dino.update()
            for obs in self.obstacles[:]:
                if obs.update():
                    self.obstacles.remove(obs)

            dl, dt, dr, db = self.dino.hitbox()
            for obs in self.obstacles:
                ol, ot, or_, ob = obs.hitbox()
                if dl < or_ and dr > ol and dt < ob and db > ot:
                    self.game_over = True
                    self.dino.set_dead()
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

        for layer in self.bg_layers:
            layer.reset()

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