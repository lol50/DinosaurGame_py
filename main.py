import tkinter as tk
from PIL import Image, ImageTk
import random, os, json, sys
import time

BASE_W, BASE_H = 1200, 600
BASE_GROUND = BASE_H - 85
BASE_SPEED = 28
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
            img = Image.open(path)
            if "ground" in path and h is not None:
                new_h = int(self.h * 1.05)
                img = img.resize((self.w, new_h), Image.Resampling.LANCZOS)
                self.y = y - (new_h - self.h)
                self.h = new_h
            else:
                img = img.resize((self.w, self.h), Image.Resampling.LANCZOS)
            self.img = ImageTk.PhotoImage(img)
        except:
            self.img = None
            return
        self.id1 = canvas.create_image(0, self.y, image=self.img, anchor="nw")
        self.id2 = canvas.create_image(self.w, self.y, image=self.img, anchor="nw")

    def update(self, speed):
        if not self.img: return
        move = speed * self.speed / 8
        self.x1 -= move
        self.x2 -= move
        if self.x1 <= -self.w: self.x1 = self.x2 + self.w
        if self.x2 <= -self.w: self.x2 = self.x1 + self.w
        self.canvas.coords(self.id1, self.x1, self.y)
        self.canvas.coords(self.id2, self.x2, self.y)

    def reset(self):
        self.x1, self.x2 = 0, self.w
        self.canvas.coords(self.id1, 0, self.y)
        self.canvas.coords(self.id2, self.w, self.y)

class Dino:
    def __init__(self, canvas, x, ground, game):
        self.canvas = canvas
        self.game = game
        self.x = x
        self.ground = ground
        self.dino_h = int(85 * game.scale_y)
        self.duck_h = int(60 * game.scale_y)
        self.y = ground - self.dino_h
        self.vy = 0
        self.jumping = False
        self.ducking = False
        self.frame = 0
        self.counter = 0
        self.tex = {}
        sizes = {
            'run1': (int(100 * game.scale_x), self.dino_h),
            'run2': (int(100 * game.scale_x), self.dino_h),
            'duck1': (int(100 * game.scale_x), self.duck_h),
            'duck2': (int(100 * game.scale_x), self.duck_h),
            'dead': (int(100 * game.scale_x), self.dino_h),
            'dead_duck': (int(100 * game.scale_x), self.duck_h)
        }
        for name, file in [('run1', 'dinomove1.png'), ('run2', 'dinomove2.png'), ('duck1', 'dino2move1.png'),
                           ('duck2', 'dino2move2.png'), ('dead', 'dinodead.png'), ('dead_duck', 'dino2dead.png')]:
            try:
                w, h = sizes[name]
                img = Image.open(f"assets/{file}").resize((w, h), Image.Resampling.LANCZOS)
                self.tex[name] = ImageTk.PhotoImage(img)
            except:
                pass
        self.cur = self.tex.get('run1')
        self.id = canvas.create_image(x, self.y, image=self.cur, anchor="nw")

    def jump(self):
        if not self.jumping:
            if self.ducking:
                self.ducking = False
                self.canvas.coords(self.id, self.x, self.ground - self.dino_h)
                self.cur = self.tex.get('run1')
                self.canvas.itemconfig(self.id, image=self.cur)
            self.jumping = True
            self.vy = -18 * self.game.scale_y

    def start_duck(self):
        if not self.jumping:
            self.ducking = True
            self.canvas.coords(self.id, self.x, self.ground - self.duck_h)
            self.cur = self.tex.get('duck1')
            self.canvas.itemconfig(self.id, image=self.cur)

    def stop_duck(self):
        if not self.jumping:
            self.ducking = False
            self.canvas.coords(self.id, self.x, self.ground - self.dino_h)
            self.cur = self.tex.get('run1')
            self.canvas.itemconfig(self.id, image=self.cur)

    def update_physics(self):
        if self.jumping:
            self.vy += 1.2 * self.game.scale_y
            self.y += self.vy
            if self.y >= self.ground - self.dino_h:
                self.y = self.ground - self.dino_h
                self.jumping = False
                self.vy = 0
                self.ducking = False
                self.canvas.coords(self.id, self.x, self.ground - self.dino_h)
                self.cur = self.tex.get('run1')
                self.canvas.itemconfig(self.id, image=self.cur)
                self.frame = self.counter = 0
            self.canvas.coords(self.id, self.x, self.y)

    def update_animation(self):
        if not self.jumping:
            self.counter += 1
            if self.counter >= 6:
                self.counter = 0
                self.frame += 1
                if self.ducking:
                    self.cur = self.tex.get('duck2') if self.frame % 2 else self.tex.get('duck1')
                else:
                    self.cur = self.tex.get('run2') if self.frame % 2 else self.tex.get('run1')
                self.canvas.itemconfig(self.id, image=self.cur)

    def set_dead(self):
        self.cur = self.tex.get('dead_duck') if self.ducking else self.tex.get('dead')
        self.canvas.itemconfig(self.id, image=self.cur)

    def hitbox(self):
        back_off = int(10 * self.game.scale_x)
        front_off = int(2 * self.game.scale_x)
        if self.ducking:
            return (self.x + back_off, self.ground - self.duck_h + 2, self.x + int(85 * self.game.scale_x) - front_off,
                    self.ground - self.duck_h + self.duck_h - 2)
        return (self.x + back_off, self.y + 2, self.x + int(85 * self.game.scale_x) - front_off,
                self.y + self.dino_h - 2)

    def reset(self):
        self.y = self.ground - self.dino_h
        self.vy = 0
        self.jumping = self.ducking = False
        self.frame = self.counter = 0
        self.cur = self.tex.get('run1')
        self.canvas.coords(self.id, self.x, self.y)
        self.canvas.itemconfig(self.id, image=self.cur)

class Obstacle:
    def __init__(self, canvas, x, y, img, w, h, typ, game):
        self.canvas = canvas
        self.game = game
        self.id = canvas.create_image(x, y, image=img, anchor="nw")
        self.x, self.y, self.w, self.h, self.typ = x, y, w, h, typ

    def update(self, speed):
        self.canvas.move(self.id, -speed, 0)
        self.x -= speed
        return self.x < -150

    def hitbox(self):
        off = int(2 * self.game.scale_x)
        return (self.x + off, self.y + 22, self.x + self.w - off, self.y + self.h - 22)

    def delete(self):
        self.canvas.delete(self.id)

class Menu:
    def __init__(self, canvas, game):
        self.canvas = canvas
        self.game = game
        self.images = {}

    def load(self):
        try:
            self.images['back'] = ImageTk.PhotoImage(
                Image.open("assets/back.png").resize((self.game.W, self.game.H), Image.Resampling.LANCZOS))
            self.images['title'] = ImageTk.PhotoImage(Image.open("assets/dinosaurgamemenu.png").resize(
                (int(550 * self.game.scale_x), int(220 * self.game.scale_y)), Image.Resampling.LANCZOS))
            btn_w = int(168 * self.game.scale_x)
            btn_h = int(34 * self.game.scale_y)
            self.images['play'] = ImageTk.PhotoImage(
                Image.open("assets/playmenu.png").resize((btn_w, btn_h), Image.Resampling.LANCZOS))
            self.images['exit'] = ImageTk.PhotoImage(
                Image.open("assets/gooutmenu.png").resize((btn_w, btn_h), Image.Resampling.LANCZOS))
            return True
        except:
            return False

    def show(self):
        if not self.load(): return
        self.bg = self.canvas.create_image(0, 0, image=self.images['back'], anchor="nw")
        cx = self.game.W // 2
        self.title = self.canvas.create_image(cx, int(self.game.H // 3 - 30 * self.game.scale_y),
                                              image=self.images['title'], anchor="center")
        self.play = self.canvas.create_image(cx, int(self.game.H // 2 + 121 * self.game.scale_y),
                                             image=self.images['play'], anchor="center")
        self.exit = self.canvas.create_image(cx, int(self.game.H // 2 + 165 * self.game.scale_y),
                                             image=self.images['exit'], anchor="center")
        self.canvas.tag_bind(self.play, "<Button-1>", self.game.start_game)
        self.canvas.tag_bind(self.exit, "<Button-1>", lambda e: sys.exit())

    def hide(self):
        for attr in ['bg', 'title', 'play', 'exit']:
            if hasattr(self, attr): self.canvas.delete(getattr(self, attr))

class GameOver:
    def __init__(self, canvas, game):
        self.canvas = canvas
        self.game = game
        self.images = {}

    def load(self):
        try:
            bg_w = int(500 * self.game.scale_x)
            bg_h = int(300 * self.game.scale_y)
            btn_w = int(180 * self.game.scale_x)
            btn_h = int(40 * self.game.scale_y)
            self.images['bg'] = ImageTk.PhotoImage(
                Image.open("assets/gameovercanvas.png").resize((bg_w, bg_h), Image.Resampling.LANCZOS))
            self.images['restart'] = ImageTk.PhotoImage(
                Image.open("assets/go.png").resize((btn_w, btn_h), Image.Resampling.LANCZOS))
            self.images['menu'] = ImageTk.PhotoImage(
                Image.open("assets/gomenu.png").resize((btn_w, btn_h), Image.Resampling.LANCZOS))
            return True
        except: return False

    def show(self):
        if not self.load():
            return
        cx, cy = self.game.W // 2, self.game.H // 2
        self.bg_id = self.canvas.create_image(cx, cy, image=self.images['bg'], anchor="center")
        self.restart_id = self.canvas.create_image(cx, cy + int(60 * self.game.scale_y), image=self.images['restart'],
                                                   anchor="center")
        self.menu_id = self.canvas.create_image(cx, cy + int(105 * self.game.scale_y), image=self.images['menu'],
                                                anchor="center")
        self.canvas.tag_bind(self.restart_id, "<Button-1>", self.game.restart_from_game_over)
        self.canvas.tag_bind(self.menu_id, "<Button-1>", self.game.menu_from_game_over)

    def hide(self):
        for attr in ['bg_id', 'restart_id', 'menu_id']:
            if hasattr(self, attr):
                self.canvas.delete(getattr(self, attr))

class PauseMenu:
    def __init__(self, canvas, game):
        self.canvas = canvas
        self.game = game
        self.images = {}

    def load(self):
        try:
            icon_size = int(35 * self.game.scale_x)
            self.images['icon_pause'] = ImageTk.PhotoImage(
                Image.open("assets/pause.png").resize((icon_size, icon_size), Image.Resampling.LANCZOS))
            self.images['icon_play'] = ImageTk.PhotoImage(
                Image.open("assets/pause2.png").resize((icon_size, icon_size), Image.Resampling.LANCZOS))
            bg_w = int(500 * self.game.scale_x)
            bg_h = int(300 * self.game.scale_y)
            btn_w = int(180 * self.game.scale_x)
            btn_h = int(40 * self.game.scale_y)
            self.images['bg'] = ImageTk.PhotoImage(
                Image.open("assets/pausecanvas.png").resize((bg_w, bg_h), Image.Resampling.LANCZOS))
            self.images['cont'] = ImageTk.PhotoImage(
                Image.open("assets/letsgo.png").resize((btn_w, btn_h), Image.Resampling.LANCZOS))
            self.images['menu'] = ImageTk.PhotoImage(
                Image.open("assets/pausegomenu.png").resize((btn_w, btn_h), Image.Resampling.LANCZOS))
            return True
        except: return False

    def show_button(self):
        if not self.images:
            self.load()
        self.btn = self.canvas.create_image(self.game.W // 2, int(25 * self.game.scale_y),
                                            image=self.images['icon_pause'], anchor="center")
        self.canvas.tag_bind(self.btn, "<Button-1>", self.game.toggle_pause)

    def hide_button(self):
        if hasattr(self, 'btn'): self.canvas.delete(self.btn)

    def set_pause_icon(self):
        if hasattr(self, 'btn') and self.btn: self.canvas.itemconfig(self.btn, image=self.images['icon_play'])

    def set_play_icon(self):
        if hasattr(self, 'btn') and self.btn: self.canvas.itemconfig(self.btn, image=self.images['icon_pause'])

    def show_screen(self):
        if not self.images: self.load()
        cx, cy = self.game.W // 2, self.game.H // 2
        self.bg_id = self.canvas.create_image(cx, cy, image=self.images['bg'], anchor="center")
        self.cont_id = self.canvas.create_image(cx, cy + int(60 * self.game.scale_y), image=self.images['cont'],
                                                anchor="center")
        self.menu_id = self.canvas.create_image(cx, cy + int(105 * self.game.scale_y), image=self.images['menu'],
                                                anchor="center")
        self.canvas.tag_bind(self.cont_id, "<Button-1>", self.game.resume_from_pause)
        self.canvas.tag_bind(self.menu_id, "<Button-1>", self.game.menu_from_pause)

    def hide_screen(self):
        for attr in ['bg_id', 'cont_id', 'menu_id']:
            if hasattr(self, attr):
                self.canvas.delete(getattr(self, attr))

class DinoGame:
    def __init__(self, root):
        self.root = root
        root.title("Динозавр игра")
        root.attributes("-fullscreen", True)
        root.configure(bg="#2d5a27")

        self.W = root.winfo_screenwidth()
        self.H = root.winfo_screenheight()
        self.scale_x = self.W / BASE_W
        self.scale_y = self.H / BASE_H

        self.canvas = tk.Canvas(root, width=self.W, height=self.H, bg="#87CEEB", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.ground_y = self.H - int(85 * self.scale_y)

        self.bg = [
            ParallaxLayer(self.canvas, f"assets/back10{i}.png", i, 0, self.W, self.H, self)
            for i in range(1, 5)
        ]
        self.ground = ParallaxLayer(self.canvas, "assets/ground102.png", 8, self.ground_y - 10, self.W,
                                    int(100 * self.scale_y), self)

        self.menu = Menu(self.canvas, self)
        self.game_over = GameOver(self.canvas, self)
        self.pause_menu = PauseMenu(self.canvas, self)

        self.dino = None
        self.obstacles = []
        self.tex = {}
        self.score = 0
        self.game_over_flag = False
        self.paused = False
        self.speed = BASE_SPEED
        self.next_up = 500
        self.update_id = None
        self.spawn_id = None
        self.next_spawn_time = 0
        self.pause_remaining = 0
        self.frame = 0
        self.high_score = self.load_high_score()
        self.score_text = None
        self.high_score_text = None

        self.load_obstacle_tex()
        self.menu.show()
        self.root.bind("<Escape>", self.toggle_pause)
        self.root.bind("<F11>", self.toggle_fullscreen)

    def toggle_fullscreen(self, event=None):
        self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen"))

    def load_obstacle_tex(self):
        sizes = {
            'cactus1': (int(50 * self.scale_x), int(85 * self.scale_y)),
            'cactus2': (int(90 * self.scale_x), int(85 * self.scale_y)),
            'cactus3': (int(130 * self.scale_x), int(85 * self.scale_y)),
            'bird': (int(75 * self.scale_x), int(55 * self.scale_y))
        }
        for name, file in [('cactus1', 'cactus.png'), ('cactus2', 'cactus2.png'), ('cactus3', 'cactus3.png'),
                           ('bird', 'bird.png')]:
            try:
                w, h = sizes[name]
                img = Image.open(f"assets/{file}").resize((w, h), Image.Resampling.LANCZOS)
                self.tex[name] = ImageTk.PhotoImage(img)
            except: pass

    def load_high_score(self):
        try:
            if os.path.exists("high_score.json"):
                with open("high_score.json", "r") as f:
                    return json.load(f).get("high_score", 0)
        except: pass
        return 0

    def save_high_score(self):
        try:
            with open("high_score.json", "w") as f:
                json.dump({"high_score": self.high_score}, f)
        except: pass

    def start_game(self, event=None):
        self.full_restart()
        self.menu.hide()
        self.dino = Dino(self.canvas, int(150 * self.scale_x), self.ground_y, self)
        self.canvas.tag_raise(self.dino.id)
        self.score_text = self.canvas.create_text(self.W - int(80 * self.scale_x), int(30 * self.scale_y),
                                                  text=f"Счет: {self.score}",
                                                  font=("Arial", int(18 * self.scale_y), "bold"), fill="black")
        self.high_score_text = self.canvas.create_text(self.W - int(80 * self.scale_x), int(60 * self.scale_y),
                                                       text=f"Рекорд: {self.high_score}",
                                                       font=("Arial", int(14 * self.scale_y), "bold"), fill="black")
        self.pause_menu.show_button()
        self.root.bind("<space>", self.handle_space)
        self.root.bind("<Up>", self.handle_space)
        self.root.bind("<Down>", self.handle_down)
        self.root.bind("<KeyRelease-Down>", self.handle_down_release)
        self.spawn_obstacle()
        self.update()

    def handle_down(self, e):
        if not self.game_over_flag and not self.paused and self.dino:
            self.dino.start_duck()

    def handle_down_release(self, e):
        if not self.game_over_flag and not self.paused and self.dino:
            self.dino.stop_duck()

    def handle_space(self, e):
        if self.game_over_flag:
            self.restart_from_game_over(e)
        elif not self.paused and self.dino:
            self.dino.jump()

    def toggle_pause(self, e=None):
        if self.game_over_flag: return
        if not self.paused:
            self.paused = True
            self.pause_menu.set_pause_icon()
            if self.spawn_id:
                self.root.after_cancel(self.spawn_id)
                self.spawn_id = None
                now = time.time() * 1000
                self.pause_remaining = max(0, self.next_spawn_time - now)
            self.pause_menu.show_screen()
        else: self.resume_from_pause(None)

    def resume_from_pause(self, e):
        self.pause_menu.hide_screen()
        self.paused = False
        self.pause_menu.set_play_icon()
        if not self.game_over_flag and self.spawn_id is None:
            if self.pause_remaining > 0:
                self.spawn_id = self.root.after(int(self.pause_remaining), self.spawn_obstacle)
            else:
                self.spawn_obstacle()
            self.pause_remaining = 0

    def menu_from_pause(self, e):
        self.pause_menu.hide_screen()
        self.full_restart()
        self.menu.show()

    def restart_from_game_over(self, e):
        self.game_over.hide()
        self.full_restart()
        self.start_game()

    def menu_from_game_over(self, e):
        self.game_over.hide()
        self.full_restart()
        self.menu.show()

    def full_restart(self):
        if self.update_id:
            self.root.after_cancel(self.update_id)
            self.update_id = None
        if self.spawn_id:
            self.root.after_cancel(self.spawn_id)
            self.spawn_id = None
        for o in self.obstacles:
            o.delete()
        self.obstacles.clear()
        for l in self.bg:
            l.reset()
        self.ground.reset()
        if self.dino:
            self.dino.reset()
        if self.score_text:
            self.canvas.delete(self.score_text)
            self.score_text = None
        if self.high_score_text:
            self.canvas.delete(self.high_score_text)
            self.high_score_text = None
        self.game_over_flag = False
        self.paused = False
        self.score = 0
        self.speed = BASE_SPEED
        self.next_up = 500
        self.frame = 0
        self.pause_menu.hide_button()
        self.pause_menu.hide_screen()
        self.game_over.hide()
        self.spawn_id = None
        self.next_spawn_time = 0
        self.pause_remaining = 0

    def spawn_obstacle(self):
        if not self.game_over_flag and not self.paused:
            r = random.randint(1, 100)
            if r <= 70:
                typ = random.choice(['cactus1', 'cactus2', 'cactus3'])
                img = self.tex[typ]
                w = self.tex[typ].width()
                y = self.ground_y - int(85 * self.scale_y)
                h = int(85 * self.scale_y)
            else:
                img = self.tex['bird']
                w = self.tex['bird'].width()
                h = int(55 * self.scale_y)
                y = self.ground_y - random.choice(
                    [int(170 * self.scale_y), int(140 * self.scale_y), int(110 * self.scale_y)])
            self.obstacles.append(Obstacle(self.canvas, self.W, y, img, w, h, "cactus" if r <= 70 else "bird", self))
            d = max(800, random.randint(MIN_SPAWN_DELAY, MAX_SPAWN_DELAY) - int(self.speed * 3))
            self.next_spawn_time = time.time() * 1000 + d
            self.spawn_id = self.root.after(d, self.spawn_obstacle)

    def update(self):
        if not self.paused and not self.game_over_flag:
            for l in self.bg:
                l.update(self.speed)
            self.ground.update(self.speed)
            if self.dino:
                self.dino.update_physics()
                self.dino.update_animation()
            for o in self.obstacles[:]:
                if o.update(self.speed):
                    self.obstacles.remove(o)
                    o.delete()
            self.frame += 1
            if self.frame % 2 == 0:
                if not self.game_over_flag:
                    self.score += 1
                    if self.score_text:
                        self.canvas.itemconfig(self.score_text, text=f"Счет: {self.score}")
                    if self.score > self.high_score:
                        self.high_score = self.score
                        if self.high_score_text:
                            self.canvas.itemconfig(self.high_score_text, text=f"Рекорд: {self.high_score}")
                        self.save_high_score()
                    if self.score >= self.next_up:
                        self.speed += 2
                        self.next_up += 500
            self.check_collisions()
        self.update_id = self.root.after(25, self.update)

    def check_collisions(self):
        if not self.dino or self.game_over_flag:
            return
        dl, dt, dr, db = self.dino.hitbox()
        for o in self.obstacles:
            ol, ot, or_, ob = o.hitbox()
            if dl < or_ and dr > ol and dt < ob and db > ot:
                self.game_over_flag = True
                self.dino.set_dead()
                if self.spawn_id:
                    self.root.after_cancel(self.spawn_id)
                    self.spawn_id = None
                self.pause_menu.hide_button()
                self.game_over.show()
                return

if __name__ == "__main__":
    DinoGame(tk.Tk()).root.mainloop()