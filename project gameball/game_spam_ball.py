"""
=============================================================================
SPAM BALL BREAKER (BBTAN / BALLZ STYLE) - PYTHON TKINTER VERSION
Game Pemecah Balok Klasik dengan Tembak Bola & Penambahan Bola (Spam Ball)
Berjalan 100% menggunakan library bawaan Python (Tkinter & Math), tanpa perlu pip install!
=============================================================================
Cara Menjalankan:
  python game_spam_ball.py
=============================================================================
"""

import math
import random
import tkinter as tk
from tkinter import messagebox

# --- Konfigurasi Game ---
WINDOW_WIDTH = 460
WINDOW_HEIGHT = 720
COLS = 7
ROWS = 9
BALL_RADIUS = 6
BASE_SPEED = 8.5
LAUNCH_DELAY_MS = 40  # Interval kemunculan bola saat menembak

STATE_AIMING = 0
STATE_SHOOTING = 1
STATE_ROUND_TRANSITION = 2
STATE_GAME_OVER = 3


class Ball:
    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.active = True
        self.landed = False


class SpamBallGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Spam Ball Breaker - Pemecah Balok")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, False)
        self.root.configure(bg="#0a0c16")

        # Game Variables
        self.round = 1
        self.high_score = 1
        self.total_balls = 10  # Jumlah awal bola (langsung seru!)
        self.extra_balls_collected = 0
        self.total_bricks_destroyed = 0

        self.current_launch_x = WINDOW_WIDTH / 2
        self.next_launch_x = self.current_launch_x
        self.launch_y = WINDOW_HEIGHT - 65
        self.has_first_landed = False

        self.state = STATE_AIMING
        self.speed_multiplier = 1  # 1x, 2x, 4x

        self.balls = []
        self.balls_to_spawn = 0
        self.balls_spawned = 0
        self.last_spawn_time = 0

        # Aiming Variables
        self.is_dragging = False
        self.aim_vector = (0, -1)
        self.mouse_pos = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)

        # Layout perhitungan kotak
        self.board_top = 70
        self.board_bottom = WINDOW_HEIGHT - 55
        self.cell_w = WINDOW_WIDTH / COLS
        self.cell_h = (self.board_bottom - self.board_top - 60) / ROWS

        self.grid = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.particles = []

        self.setup_ui()
        self.init_board()

        # Bindings
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # Loop animasi utama
        self.game_loop()

    def setup_ui(self):
        # Top HUD Panel
        self.hud_frame = tk.Frame(self.root, bg="#12182b", height=55)
        self.hud_frame.pack(fill=tk.X, side=tk.TOP)

        self.score_label = tk.Label(
            self.hud_frame,
            text=f"Ronde: {self.round}",
            font=("Segoe UI", 13, "bold"),
            fg="#00f0ff",
            bg="#12182b"
        )
        self.score_label.pack(side=tk.LEFT, padx=14, pady=8)

        self.high_score_label = tk.Label(
            self.hud_frame,
            text=f"Terbaik: {self.high_score}",
            font=("Segoe UI", 11, "bold"),
            fg="#ffd152",
            bg="#12182b"
        )
        self.high_score_label.pack(side=tk.LEFT, padx=10, pady=8)

        self.speed_btn = tk.Button(
            self.hud_frame,
            text="1x",
            font=("Segoe UI", 10, "bold"),
            fg="#00f0ff",
            bg="#1f2845",
            activebackground="#2a375e",
            activeforeground="#00f0ff",
            bd=0,
            padx=8,
            pady=2,
            command=self.toggle_speed
        )
        self.speed_btn.pack(side=tk.RIGHT, padx=6)

        self.recall_btn = tk.Button(
            self.hud_frame,
            text="⚡ Tarik",
            font=("Segoe UI", 10, "bold"),
            fg="#ff5277",
            bg="#2a1622",
            activebackground="#451f33",
            activeforeground="#ff5277",
            bd=0,
            padx=8,
            pady=2,
            command=self.recall_balls
        )
        self.recall_btn.pack(side=tk.RIGHT, padx=6)

        # Canvas Area
        self.canvas = tk.Canvas(
            self.root,
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT - 90,
            bg="#090c15",
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bottom Bar
        self.bottom_frame = tk.Frame(self.root, bg="#12182b", height=35)
        self.bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.ball_badge = tk.Label(
            self.bottom_frame,
            text=f"⚪ Bola: x{self.total_balls}",
            font=("Segoe UI", 11, "bold"),
            fg="#00f0ff",
            bg="#12182b"
        )
        self.ball_badge.pack(side=tk.LEFT, padx=14, pady=4)

        self.hint_label = tk.Label(
            self.bottom_frame,
            text="Geser & lepas untuk menembak",
            font=("Segoe UI", 9),
            fg="#8b9bb4",
            bg="#12182b"
        )
        self.hint_label.pack(side=tk.RIGHT, padx=14, pady=4)

    def toggle_speed(self):
        if self.speed_multiplier == 1:
            self.speed_multiplier = 2
            self.speed_btn.config(text="2x", bg="#004466")
        elif self.speed_multiplier == 2:
            self.speed_multiplier = 4
            self.speed_btn.config(text="4x", bg="#006688")
        else:
            self.speed_multiplier = 1
            self.speed_btn.config(text="1x", bg="#1f2845")

    def recall_balls(self):
        if self.state == STATE_SHOOTING:
            for b in self.balls:
                b.active = False
                b.landed = True
            self.balls_spawned = self.total_balls

    def get_brick_color(self, hp):
        ratio = min(hp / max(self.round * 1.5, 1), 1.0)
        if ratio < 0.25:
            return "#00f0ff", "#002b33"
        elif ratio < 0.5:
            return "#00ff88", "#00331a"
        elif ratio < 0.75:
            return "#ffd152", "#332600"
        elif ratio < 0.9:
            return "#ff8833", "#331500"
        return "#ff3366", "#330010"

    def init_board(self):
        self.grid = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.spawn_new_row()
        self.spawn_new_row()

    def spawn_new_row(self):
        # Geser seluruh baris ke bawah
        for r in range(ROWS - 1, 0, -1):
            for c in range(COLS):
                self.grid[r][c] = self.grid[r - 1][c]

        self.grid[0] = [None for _ in range(COLS)]

        # Cek Game Over (jika ada balok di baris terbawah ROWS - 1)
        for c in range(COLS):
            item = self.grid[ROWS - 1][c]
            if item and item.get("type") in ("brick", "triangle"):
                self.trigger_game_over()
                return

        # Tentukan kolom acak untuk spawn item
        num_items = random.randint(2, 4)
        cols = random.sample(range(COLS), num_items)

        # Selalu sertakan 1 powerup penambah bola (+1 ball) di setiap ronde
        add_ball_col = cols[0]
        self.grid[0][add_ball_col] = {"type": "add_ball"}

        for c in cols[1:]:
            roll = random.random()
            if roll < 0.15:
                # Laser pembersih baris / kolom
                self.grid[0][c] = {"type": "laser", "dir": random.choice(["row", "col"])}
            elif roll < 0.25:
                # Bom area 3x3
                self.grid[0][c] = {"type": "bomb"}
            else:
                # Balok biasa
                hp = self.round if random.random() > 0.25 else self.round * 2
                self.grid[0][c] = {"type": "brick", "hp": hp}

    def on_press(self, event):
        if self.state != STATE_AIMING:
            return
        self.is_dragging = True
        self.update_aim(event.x, event.y)

    def on_drag(self, event):
        if not self.is_dragging or self.state != STATE_AIMING:
            return
        self.update_aim(event.x, event.y)

    def on_release(self, event):
        if not self.is_dragging or self.state != STATE_AIMING:
            return
        self.is_dragging = False
        self.start_shooting()

    def update_aim(self, mx, my):
        self.mouse_pos = (mx, my)
        dx = mx - self.current_launch_x
        dy = my - self.launch_y

        # Slingshot: jika ditarik ke bawah, balik arah ke atas
        if dy > 10:
            dx = -dx
            dy = -dy

        dist = math.hypot(dx, dy)
        if dist > 15:
            angle = math.atan2(dy, dx)
            # Batasi sudut agar bola tidak memantul horizontal abadi
            min_ang = -math.pi * 0.94
            max_ang = -math.pi * 0.06
            if angle > 0:
                angle = -math.pi / 2
            angle = max(min_ang, min(max_ang, angle))
            self.aim_vector = (math.cos(angle), math.sin(angle))

    def start_shooting(self):
        self.state = STATE_SHOOTING
        self.balls = []
        self.balls_spawned = 0
        self.balls_to_spawn = self.total_balls
        self.extra_balls_collected = 0
        self.has_first_landed = False
        self.hint_label.config(text=f"Menembak {self.total_balls} bola...")

    def finish_turn(self):
        self.state = STATE_ROUND_TRANSITION
        self.total_balls += self.extra_balls_collected
        self.current_launch_x = self.next_launch_x

        self.round += 1
        if self.round > self.high_score:
            self.high_score = self.round

        self.score_label.config(text=f"Ronde: {self.round}")
        self.high_score_label.config(text=f"Terbaik: {self.high_score}")
        self.ball_badge.config(text=f"⚪ Bola: x{self.total_balls}")
        self.hint_label.config(text="Giliran Anda! Tarik & lepas")

        self.root.after(200, self.advance_round)

    def advance_round(self):
        if self.state != STATE_GAME_OVER:
            self.spawn_new_row()
            if self.state != STATE_GAME_OVER:
                self.state = STATE_AIMING

    def trigger_game_over(self):
        self.state = STATE_GAME_OVER
        messagebox.showinfo(
            "Game Over!",
            f"Permainan Berakhir!\n\n"
            f"Ronde Dicapai: {self.round}\n"
            f"Total Balok Hancur: {self.total_bricks_destroyed}\n"
            f"Jumlah Bola Terkumpul: {self.total_balls}\n"
            f"Skor Terbaik: {self.high_score}"
        )
        self.restart_game()

    def restart_game(self):
        self.round = 1
        self.total_balls = 10
        self.extra_balls_collected = 0
        self.total_bricks_destroyed = 0
        self.current_launch_x = WINDOW_WIDTH / 2
        self.next_launch_x = self.current_launch_x
        self.balls = []
        self.particles = []

        self.score_label.config(text=f"Ronde: {self.round}")
        self.high_score_label.config(text=f"Terbaik: {self.high_score}")
        self.ball_badge.config(text=f"⚪ Bola: x{self.total_balls}")
        self.hint_label.config(text="Geser & lepas untuk menembak")

        self.init_board()
        self.state = STATE_AIMING

    def trigger_laser(self, row, col, direction):
        if direction in ("row", "cross"):
            for c in range(COLS):
                item = self.grid[row][c]
                if item and item.get("type") == "brick":
                    item["hp"] -= max(1, math.ceil(self.round * 0.6))
                    if item["hp"] <= 0:
                        self.grid[row][c] = None
                        self.total_bricks_destroyed += 1

        if direction in ("col", "cross"):
            for r in range(ROWS):
                item = self.grid[r][col]
                if item and item.get("type") == "brick":
                    item["hp"] -= max(1, math.ceil(self.round * 0.6))
                    if item["hp"] <= 0:
                        self.grid[r][col] = None
                        self.total_bricks_destroyed += 1

    def trigger_bomb(self, row, col):
        for r in range(max(0, row - 1), min(ROWS, row + 2)):
            for c in range(max(0, col - 1), min(COLS, col + 2)):
                item = self.grid[r][c]
                if item and item.get("type") == "brick":
                    item["hp"] -= max(1, math.ceil(self.round * 0.8))
                    if item["hp"] <= 0:
                        self.grid[r][c] = None
                        self.total_bricks_destroyed += 1

    def spawn_particles(self, x, y, color, count=6):
        for _ in range(count):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(2, 5)
            self.particles.append({
                "x": x, "y": y,
                "vx": math.cos(ang) * spd,
                "vy": math.sin(ang) * spd,
                "color": color,
                "life": 12
            })

    def update_physics(self):
        # Spawn bola baru jika masih ada antrean
        if self.state == STATE_SHOOTING and self.balls_spawned < self.balls_to_spawn:
            vx = self.aim_vector[0] * BASE_SPEED
            vy = self.aim_vector[1] * BASE_SPEED
            self.balls.append(Ball(self.current_launch_x, self.launch_y, vx, vy))
            self.balls_spawned += 1

        substeps = 2
        dt = self.speed_multiplier / substeps

        for b in self.balls:
            if not b.active:
                if b.landed:
                    dx = self.next_launch_x - b.x
                    if abs(dx) > 1:
                        b.x += dx * 0.2
                continue

            for _ in range(substeps):
                b.x += b.vx * dt
                b.y += b.vy * dt

                # Pantulan dinding kiri & kanan
                if b.x - BALL_RADIUS <= 0:
                    b.x = BALL_RADIUS
                    b.vx = abs(b.vx)
                elif b.x + BALL_RADIUS >= WINDOW_WIDTH:
                    b.x = WINDOW_WIDTH - BALL_RADIUS
                    b.vx = -abs(b.vx)

                # Pantulan atap
                if b.y - BALL_RADIUS <= self.board_top:
                    b.y = self.board_top + BALL_RADIUS
                    b.vy = abs(b.vy)

                # Menyentuh lantai bawah (mendarat)
                if b.y + BALL_RADIUS >= self.board_bottom:
                    b.y = self.board_bottom - BALL_RADIUS
                    b.active = False
                    b.landed = True

                    if not self.has_first_landed:
                        self.has_first_landed = True
                        self.next_launch_x = max(20, min(WINDOW_WIDTH - 20, b.x))
                    break

                # Cek tabrakan balok
                pad = 2
                for r in range(ROWS):
                    for c in range(COLS):
                        item = self.grid[r][c]
                        if not item:
                            continue

                        bx = c * self.cell_w + pad
                        by = self.board_top + r * self.cell_h + pad
                        bw = self.cell_w - pad * 2
                        bh = self.cell_h - pad * 2
                        cx = bx + bw / 2
                        cy = by + bh / 2

                        if item["type"] == "brick":
                            near_x = max(bx, min(b.x, bx + bw))
                            near_y = max(by, min(b.y, by + bh))
                            dx = b.x - near_x
                            dy = b.y - near_y

                            if dx * dx + dy * dy < BALL_RADIUS * BALL_RADIUS:
                                # Tentukan normal pantulan
                                overlap_x = (bw / 2 + BALL_RADIUS) - abs(b.x - cx)
                                overlap_y = (bh / 2 + BALL_RADIUS) - abs(b.y - cy)

                                if overlap_x < overlap_y:
                                    b.vx = -b.vx
                                else:
                                    b.vy = -b.vy

                                item["hp"] -= 1
                                fill, _ = self.get_brick_color(item["hp"])
                                self.spawn_particles(near_x, near_y, fill, 3)

                                if item["hp"] <= 0:
                                    self.grid[r][c] = None
                                    self.total_bricks_destroyed += 1
                                    self.spawn_particles(cx, cy, fill, 12)
                                break

                        elif item["type"] == "add_ball":
                            dist = math.hypot(b.x - cx, b.y - cy)
                            if dist < 12 + BALL_RADIUS:
                                self.grid[r][c] = None
                                self.extra_balls_collected += 1
                                self.spawn_particles(cx, cy, "#00ff88", 8)
                                break

                        elif item["type"] == "laser":
                            dist = math.hypot(b.x - cx, b.y - cy)
                            if dist < 12 + BALL_RADIUS:
                                d = item["dir"]
                                self.grid[r][c] = None
                                self.trigger_laser(r, c, d)
                                self.spawn_particles(cx, cy, "#00f0ff", 14)
                                break

                        elif item["type"] == "bomb":
                            dist = math.hypot(b.x - cx, b.y - cy)
                            if dist < 12 + BALL_RADIUS:
                                self.grid[r][c] = None
                                self.trigger_bomb(r, c)
                                self.spawn_particles(cx, cy, "#ff4466", 20)
                                break

        # Cek apakah ronde tembak selesai
        if self.state == STATE_SHOOTING and self.balls_spawned >= self.balls_to_spawn:
            active_left = any(b.active for b in self.balls)
            if not active_left:
                self.finish_turn()

        # Update Partikel
        for p in self.particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 1
            if p["life"] <= 0:
                self.particles.remove(p)

    def draw(self):
        self.canvas.delete("all")

        # Garis batas bahaya bawah (merah putus-putus)
        self.canvas.create_line(
            0, self.board_bottom, WINDOW_WIDTH, self.board_bottom,
            fill="#ff4466", dash=(4, 4), width=1
        )

        # Gambar Balok & Item di Grid
        pad = 3
        for r in range(ROWS):
            for c in range(COLS):
                item = self.grid[r][c]
                if not item:
                    continue

                bx = c * self.cell_w + pad
                by = self.board_top + r * self.cell_h + pad
                bw = self.cell_w - pad * 2
                bh = self.cell_h - pad * 2
                cx = bx + bw / 2
                cy = by + bh / 2

                if item["type"] == "brick":
                    fill, text_col = self.get_brick_color(item["hp"])
                    self.canvas.create_rectangle(
                        bx, by, bx + bw, by + bh,
                        fill=fill, outline="#ffffff", width=1
                    )
                    self.canvas.create_text(
                        cx, cy,
                        text=str(item["hp"]),
                        font=("Segoe UI", 11, "bold"),
                        fill=text_col
                    )
                elif item["type"] == "add_ball":
                    # Lingkaran hijau penambah bola (+1)
                    self.canvas.create_oval(
                        cx - 10, cy - 10, cx + 10, cy + 10,
                        outline="#00ff88", width=2, fill="#051f12"
                    )
                    self.canvas.create_oval(
                        cx - 4, cy - 4, cx + 4, cy + 4,
                        fill="#ffffff", outline=""
                    )
                    self.canvas.create_text(
                        cx, cy - 14,
                        text="+1",
                        font=("Segoe UI", 8, "bold"),
                        fill="#00ff88"
                    )
                elif item["type"] == "laser":
                    self.canvas.create_rectangle(
                        bx + 4, by + 4, bx + bw - 4, by + bh - 4,
                        fill="#003344", outline="#00f0ff", width=1.5
                    )
                    symbol = "↔" if item["dir"] == "row" else "↕"
                    self.canvas.create_text(
                        cx, cy,
                        text=symbol,
                        font=("Segoe UI", 12, "bold"),
                        fill="#00f0ff"
                    )
                elif item["type"] == "bomb":
                    self.canvas.create_oval(
                        cx - 11, cy - 11, cx + 11, cy + 11,
                        fill="#330010", outline="#ff4466", width=2
                    )
                    self.canvas.create_text(
                        cx, cy,
                        text="💣",
                        font=("Segoe UI", 10)
                    )

        # Gambar Partikel
        for p in self.particles:
            self.canvas.create_oval(
                p["x"] - 2, p["y"] - 2, p["x"] + 2, p["y"] + 2,
                fill=p["color"], outline=""
            )

        # Gambar Garis Bidik Trajectory
        if self.state == STATE_AIMING and self.is_dragging:
            cur_x = self.current_launch_x
            cur_y = self.launch_y
            vx = self.aim_vector[0] * 12
            vy = self.aim_vector[1] * 12

            for i in range(25):
                cur_x += vx
                cur_y += vy

                if cur_x <= BALL_RADIUS or cur_x >= WINDOW_WIDTH - BALL_RADIUS:
                    vx = -vx
                if cur_y <= self.board_top:
                    vy = -vy

                self.canvas.create_oval(
                    cur_x - 2, cur_y - 2, cur_x + 2, cur_y + 2,
                    fill="#00f0ff", outline=""
                )

        # Gambar Bola
        for b in self.balls:
            if b.active or b.landed:
                self.canvas.create_oval(
                    b.x - BALL_RADIUS, b.y - BALL_RADIUS,
                    b.x + BALL_RADIUS, b.y + BALL_RADIUS,
                    fill="#ffffff", outline="#00f0ff"
                )

        # Base Peluncuran
        if self.state == STATE_AIMING:
            self.canvas.create_oval(
                self.current_launch_x - BALL_RADIUS - 2, self.launch_y - BALL_RADIUS - 2,
                self.current_launch_x + BALL_RADIUS + 2, self.launch_y + BALL_RADIUS + 2,
                outline="#00f0ff", width=2
            )
            self.canvas.create_oval(
                self.current_launch_x - BALL_RADIUS, self.launch_y - BALL_RADIUS,
                self.current_launch_x + BALL_RADIUS, self.launch_y + BALL_RADIUS,
                fill="#ffffff", outline=""
            )
            self.canvas.create_text(
                self.current_launch_x, self.launch_y - 15,
                text=f"x{self.total_balls}",
                font=("Segoe UI", 10, "bold"),
                fill="#00f0ff"
            )

        # Indikator pendaratan bola pertama
        if self.state == STATE_SHOOTING and self.has_first_landed:
            self.canvas.create_oval(
                self.next_launch_x - BALL_RADIUS, self.launch_y - BALL_RADIUS,
                self.next_launch_x + BALL_RADIUS, self.launch_y + BALL_RADIUS,
                outline="#00f0ff", fill="#003344"
            )

    def game_loop(self):
        self.update_physics()
        self.draw()
        self.root.after(16, self.game_loop)


if __name__ == "__main__":
    root = tk.Tk()
    app = SpamBallGame(root)
    root.mainloop()
