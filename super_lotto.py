import tkinter as tk
import random
import time

# =========================
# 大乐透配置
# =========================
FRONT_POOL = list(range(1, 36))   # 1..35（前区）
BACK_POOL = list(range(1, 13))    # 1..12（后区）

WINDOW_W = 900
WINDOW_H = 360

BALL_RADIUS = 34
BALL_GAP = 16

ANIM_FPS = 60
BASE_ROLL_TIME = 2.0
STEP_STOP_DELAY = 0.5

# 颜色
BG_COLOR = "#f7f7f7"
RED_COLOR = "#e53935"
BLUE_COLOR = "#1e88e5"
TEXT_COLOR = "white"
BUTTON_COLOR = "#4caf50"


def fmt(num):
    try:
        return f"{int(num):02d}"
    except:
        return str(num)


class Ball:
    def __init__(self, canvas, x, y, radius, fill):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.r = radius

        self.oval = canvas.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            fill=fill, outline=""
        )
        self.text = canvas.create_text(
            x, y, text="", fill=TEXT_COLOR,
            font=("Helvetica", 16, "bold")
        )

    def set_number(self, num):
        self.canvas.itemconfig(self.text, text=fmt(num))


class LotteryApp:
    def __init__(self, root):
        self.root = root
        root.title("大乐透模拟抽奖（5+2）")
        root.geometry(f"{WINDOW_W}x{WINDOW_H}")
        root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=WINDOW_W, height=WINDOW_H, bg=BG_COLOR)
        self.canvas.pack()

        self.canvas.create_text(
            WINDOW_W // 2, 28,
            text="大乐透模拟抽奖（5前区 + 2后区）",
            font=("Helvetica", 20, "bold")
        )

        y = 120

        # ===== 前区（5个红球）=====
        start_x = 120
        self.front_balls = []
        for i in range(5):
            x = start_x + i * (2 * BALL_RADIUS + BALL_GAP)
            b = Ball(self.canvas, x, y, BALL_RADIUS, RED_COLOR)
            b.set_number("--")
            self.front_balls.append(b)

        # ===== 后区（2个蓝球）=====
        start_x_back = start_x + 5 * (2 * BALL_RADIUS + BALL_GAP) + 60
        self.back_balls = []
        for i in range(2):
            x = start_x_back + i * (2 * BALL_RADIUS + BALL_GAP)
            b = Ball(self.canvas, x, y, BALL_RADIUS, BLUE_COLOR)
            b.set_number("--")
            self.back_balls.append(b)

        # 结果文本
        self.result_text = tk.StringVar()
        self.result_text.set("点击“抽奖”开始")
        tk.Label(root, textvariable=self.result_text, bg=BG_COLOR,
                 font=("Helvetica", 14)).place(x=20, y=220)

        # 按钮
        self.btn = tk.Button(root, text="抽奖",
                             command=self.start_draw,
                             bg=BUTTON_COLOR, fg="white",
                             font=("Helvetica", 14, "bold"))
        self.btn.place(x=WINDOW_W - 120, y=250, width=100, height=40)

        self.animating = False

    def start_draw(self):
        if self.animating:
            return

        self.animating = True
        self.btn.config(state=tk.DISABLED)
        self.result_text.set("抽奖进行中...")

        # ===== 随机结果 =====
        final_front = sorted(random.sample(FRONT_POOL, 5))
        final_back = sorted(random.sample(BACK_POOL, 2))

        start_time = time.time()

        # 停止时间
        front_stop = [BASE_ROLL_TIME + i * STEP_STOP_DELAY for i in range(5)]
        back_stop = [
            BASE_ROLL_TIME + 5 * STEP_STOP_DELAY + i * STEP_STOP_DELAY
            for i in range(2)
        ]

        frame_interval = 1.0 / ANIM_FPS

        while True:
            elapsed = time.time() - start_time

            all_stop = True

            # 前区动画
            for i, ball in enumerate(self.front_balls):
                if elapsed >= front_stop[i]:
                    ball.set_number(final_front[i])
                else:
                    all_stop = False
                    ball.set_number(random.choice(FRONT_POOL))

            # 后区动画
            for i, ball in enumerate(self.back_balls):
                if elapsed >= back_stop[i]:
                    ball.set_number(final_back[i])
                else:
                    all_stop = False
                    ball.set_number(random.choice(BACK_POOL))

            self.root.update()
            time.sleep(frame_interval)

            if all_stop:
                break

        # ===== 闪烁效果 =====
        for _ in range(6):
            for b in self.front_balls + self.back_balls:
                self.canvas.itemconfig(b.oval, outline="")
            self.root.update()
            time.sleep(0.1)

            for b in self.front_balls + self.back_balls:
                self.canvas.itemconfig(b.oval, outline="white", width=2)
            self.root.update()
            time.sleep(0.1)

        # ===== 显示结果 =====
        front_str = " ".join(fmt(x) for x in final_front)
        back_str = " ".join(fmt(x) for x in final_back)

        self.result_text.set(f"结果 — 前区: {front_str}   后区: {back_str}")

        self.btn.config(state=tk.NORMAL)
        self.animating = False


if __name__ == "__main__":
    root = tk.Tk()
    app = LotteryApp(root)
    root.mainloop()