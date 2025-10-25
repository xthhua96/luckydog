import tkinter as tk
import random
import time

# 配置
RED_POOL = list(range(1, 34))   # 1..33
BLUE_POOL = list(range(1, 17))  # 1..16

WINDOW_W = 800
WINDOW_H = 360

BALL_RADIUS = 34
BALL_GAP = 16

ANIM_FPS = 60  # 动画帧率参考
# 每个球的滚动持续时间 (秒)，我们会让每个球在不同时间停止，产生阶梯停止效果
BASE_ROLL_TIME = 2.0
STEP_STOP_DELAY = 0.6  # 每个后续球比前一个多等待多少秒

# 颜色
BG_COLOR = "#f7f7f7"
RED_COLOR = "#e53935"
BLUE_COLOR = "#1e88e5"
TEXT_COLOR = "white"
BUTTON_COLOR = "#4caf50"

# 工具函数：格式化号码为两位
def fmt(num):
    """
    把 num 格式化为两位整数字符串（例如 1 -> "01"）。
    如果 num 无法转换为整数（比如 "--"），则原样返回字符串表示。
    """
    try:
        return f"{int(num):02d}"
    except (ValueError, TypeError):
        return str(num)


class Ball:
    def __init__(self, canvas, x, y, radius, fill, tag):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.r = radius
        self.fill = fill
        self.tag = tag
        self.oval = canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=fill, outline="")
        self.text = canvas.create_text(x, y, text="", fill=TEXT_COLOR, font=("Helvetica", 16, "bold"))

    def set_number(self, number):
        self.canvas.itemconfig(self.text, text=fmt(number))

    def flash_number(self, number, offset_x=0):
        """直接将数字显示在球上（可以用于最后停下），offset_x 保留扩展空间"""
        self.set_number(number)

    def move_to(self, x, y):
        dx = x - self.x
        dy = y - self.y
        self.canvas.move(self.oval, dx, dy)
        self.canvas.move(self.text, dx, dy)
        self.x = x
        self.y = y

class DoubleBallApp:
    def __init__(self, root):
        self.root = root
        root.title("双色球模拟抽奖（6红+1蓝）")
        root.geometry(f"{WINDOW_W}x{WINDOW_H}")
        root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=WINDOW_W, height=WINDOW_H, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack()

        # 标题
        self.canvas.create_text(WINDOW_W // 2, 28, text="双色球模拟抽奖（6红 + 1蓝）", font=("Helvetica", 20, "bold"))

        # 布局：6个红球水平居中，蓝球在右侧单独显示
        total_width = 6 * (2 * BALL_RADIUS) + 5 * BALL_GAP
        start_x = (WINDOW_W - total_width - 120) // 2 + BALL_RADIUS  # 留 120px 给蓝球区域
        y = 120

        self.red_balls = []
        for i in range(6):
            x = start_x + i * (2 * BALL_RADIUS + BALL_GAP)
            b = Ball(self.canvas, x, y, BALL_RADIUS, RED_COLOR, tag=f"red{i}")
            b.set_number("--")
            self.red_balls.append(b)

        # 蓝球位置（在右侧）
        blue_x = start_x + total_width + 80
        blue_y = y
        self.blue_ball = Ball(self.canvas, blue_x, blue_y, BALL_RADIUS, BLUE_COLOR, tag="blue")
        self.blue_ball.set_number("--")

        # 显示最终结果文本
        self.result_text = tk.StringVar()
        self.result_text.set("点击“抽奖”开始")
        self.result_label = tk.Label(root, textvariable=self.result_text, font=("Helvetica", 14), bg=BG_COLOR)
        # place under canvas
        self.result_label.place(x=20, y=220)

        # 抽奖按钮
        self.draw_btn = tk.Button(root, text="抽奖", command=self.start_draw, bg=BUTTON_COLOR, fg="white", font=("Helvetica", 14, "bold"))
        self.draw_btn.place(x=WINDOW_W - 120, y=250, width=100, height=40)

        # 防止重复点击
        self.animating = False

    def start_draw(self):
        if self.animating:
            return
        self.animating = True
        self.draw_btn.config(state=tk.DISABLED)
        self.result_text.set("抽奖进行中...")
        self.root.update()

        # 随机决定结果
        final_reds = random.sample(RED_POOL, 6)
        final_reds.sort()
        final_blue = random.choice(BLUE_POOL)

        # 决定每个球的停止时间（秒，从开始动画计时）
        stop_times = []
        for i in range(6):
            stop_times.append(BASE_ROLL_TIME + i * STEP_STOP_DELAY)
        blue_stop = BASE_ROLL_TIME + 6 * STEP_STOP_DELAY + 0.6  # 蓝球最后停

        # 每个球在滚动时可以从对应池中随机取数显示（红球取 1..33，蓝球取 1..16）
        start_time = time.time()
        lasts = [stop_times[i] for i in range(6)]
        blue_last = blue_stop

        # animation loop
        # 我们以固定帧率刷新，每帧更新仍在滚动的球显示的数字
        frame_interval = 1.0 / ANIM_FPS

        # 为了让每个球显得“独立”，我们为每个红球维护自己的随机滚动序列（从池中随机选数）
        # 但最后必须停到 final_reds[i]
        red_final_iter = iter(final_reds)  # 顺序对应球的位置（红球已经排序）
        # However we want the visual stop order to be left->right mapping to sorted final reds.
        # final_reds is sorted, so ball 0 gets final_reds[0], etc.

        while True:
            now = time.time()
            elapsed = now - start_time

            # Update red balls
            all_reds_stopped = True
            for i, ball in enumerate(self.red_balls):
                if elapsed >= lasts[i]:
                    # 已停止，显示最终号码（按索引）
                    ball.set_number(final_reds[i])
                else:
                    all_reds_stopped = False
                    # 还在滚动，随机显示
                    # 为更真实的滚动感：滚动时数字频率逐渐变快 -> 使用 elapsed fraction to bias display? 
                    # 这里每帧随机一个数即可
                    num = random.choice(RED_POOL)
                    ball.set_number(num)

            # Update blue ball
            if elapsed >= blue_last:
                self.blue_ball.set_number(final_blue)
                blue_stopped = True
            else:
                blue_stopped = False
                self.blue_ball.set_number(random.choice(BLUE_POOL))

            self.root.update_idletasks()
            self.root.update()

            if all_reds_stopped and blue_stopped:
                break

            time.sleep(frame_interval)

        # 最后微小动画：高亮闪烁最后结果几下
        for flash_i in range(6):
            for b in self.red_balls:
                self.canvas.itemconfig(b.oval, outline="")
            self.canvas.itemconfig(self.blue_ball.oval, outline="")
            self.root.update()
            time.sleep(0.12)
            for b in self.red_balls:
                self.canvas.itemconfig(b.oval, outline="white", width=2)
            self.canvas.itemconfig(self.blue_ball.oval, outline="white", width=2)
            self.root.update()
            time.sleep(0.12)

        # 显示结果文本
        reds_str = "  ".join(fmt(n) for n in final_reds)
        self.result_text.set(f"结果 — 红球: {reds_str}   蓝球: {fmt(final_blue)}")
        self.draw_btn.config(state=tk.NORMAL)
        self.animating = False

if __name__ == "__main__":
    root = tk.Tk()
    app = DoubleBallApp(root)
    root.mainloop()
