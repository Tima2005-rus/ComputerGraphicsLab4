import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import math, re

def clamp_coord(x, w): return max(0, min(w - 1, int(x)))
def sign(v): return 1 if v > 0 else (-1 if v < 0 else 0)
def set_pixel(img, x, y, color):
    w, h = img.size
    if 0 <= x < w and 0 <= y < h:
        img.putpixel((x, y), color)

# Линии (можно использовать DDA)
def dda_line(img, x1, y1, x2, y2, color):
    dx, dy = x2 - x1, y2 - y1
    L = max(abs(dx), abs(dy))
    if L == 0: set_pixel(img, round(x1), round(y1), color); return
    dx_step, dy_step = dx / L, dy / L
    x, y = x1, y1
    for _ in range(int(L)+1):
        set_pixel(img, round(x), round(y), color)
        x += dx_step; y += dy_step

# --- Окружности ---
def circle_equation(img, xc, yc, r, color):
    for x in range(int(xc-r), int(xc+r)+1):
        y_sq = r**2 - (x-xc)**2
        if y_sq >= 0:
            y = int(math.sqrt(y_sq))
            set_pixel(img, x, yc+y, color)
            set_pixel(img, x, yc-y, color)

def circle_parametric(img, xc, yc, r, color):
    step = 0.01
    t = 0
    while t <= 2*math.pi:
        x = int(xc + r*math.cos(t))
        y = int(yc + r*math.sin(t))
        set_pixel(img, x, y, color)
        t += step

def circle_bresenham(img, xc, yc, r, color):
    x = 0
    y = r
    d = 3 - 2*r
    plot_circle_points(img, xc, yc, x, y, color)
    while y >= x:
        x += 1
        if d > 0:
            y -= 1
            d += 4*(x - y) + 10
        else:
            d += 4*x + 6
        plot_circle_points(img, xc, yc, x, y, color)

def plot_circle_points(img, xc, yc, x, y, color):
    points = [(xc+x,yc+y),(xc-x,yc+y),(xc+x,yc-y),(xc-x,yc-y),
              (xc+y,yc+x),(xc-y,yc+x),(xc+y,yc-x),(xc-y,yc-x)]
    for px, py in points:
        set_pixel(img, px, py, color)

def circle_builtin(img, xc, yc, r, color):
    draw = ImageDraw.Draw(img)
    draw.ellipse((xc-r, yc-r, xc+r, yc+r), outline=color)

# --- SVG / Треугольник ---
def parse_svg(filename):
    with open(filename, "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(r'points="([\d ,.-]+)"', text)
    if not m:
        return None
    nums = list(map(float, re.findall(r'[-]?\d+\.?\d*', m.group(1))))
    if len(nums) < 6: return None
    return nums[:6]

def draw_triangle(img, vertices, color=(0,0,255)):
    x1,y1,x2,y2,x3,y3 = vertices
    dda_line(img, x1,y1,x2,y2,color)
    dda_line(img, x2,y2,x3,y3,color)
    dda_line(img, x3,y3,x1,y1,color)

# --- Вписанная и описанная окружности ---
def circumcircle(vertices):
    x1,y1,x2,y2,x3,y3 = vertices
    D = 2*(x1*(y2-y3)+x2*(y3-y1)+x3*(y1-y2))
    Ux = ((x1**2+y1**2)*(y2-y3)+(x2**2+y2**2)*(y3-y1)+(x3**2+y3**2)*(y1-y2))/D
    Uy = ((x1**2+y1**2)*(x3-x2)+(x2**2+y2**2)*(x1-x3)+(x3**2+y3**2)*(x2-x1))/D
    r = math.sqrt((Ux-x1)**2 + (Uy-y1)**2)
    return int(Ux), int(Uy), int(r)

def incircle(vertices):
    x1,y1,x2,y2,x3,y3 = vertices
    a = math.hypot(x2-x3,y2-y3)
    b = math.hypot(x1-x3,y1-y3)
    c = math.hypot(x1-x2,y1-y2)
    px = (a*x1 + b*x2 + c*x3)/(a+b+c)
    py = (a*y1 + b*y2 + c*y3)/(a+b+c)
    s = (a+b+c)/2
    r = math.sqrt((s-a)*(s-b)*(s-c)/s)
    return int(px), int(py), int(r)

# --- PPM ---
def save_ppm_ascii(image, path):
    w,h = image.size
    with open(path,"w") as f:
        f.write("P3\n")
        f.write(f"{w} {h}\n255\n")
        for y in range(h):
            row=[]
            for x in range(w):
                r,g,b = image.getpixel((x,y))
                row.append(f"{r} {g} {b}")
            f.write(" ".join(row)+"\n")

# --- GUI ---
class App:
    def __init__(self, root):
        self.root = root
        root.title("Треугольник и окружности")
        self.W,self.H=600,600
        self.img = Image.new("RGB",(self.W,self.H),(255,255,255))
        self.photo = ImageTk.PhotoImage(self.img)
        self.vertices = None

        ctrl = tk.Frame(root); ctrl.pack(side=tk.LEFT, fill=tk.Y,padx=6,pady=6)
        tk.Button(ctrl,text="Открыть SVG",command=self.load_svg).pack(fill="x",pady=2)

        tk.Label(ctrl,text="Метод окружности:").pack(pady=(8,0))
        self.method_var=tk.StringVar(value="equation")
        for t,v in [("Уравнение","equation"),("Параметрическое","param"),
                    ("Брезенхем","bresenham"),("Встроенный","builtin")]:
            tk.Radiobutton(ctrl,text=t,variable=self.method_var,value=v).pack(anchor="w")

        tk.Button(ctrl,text="Нарисовать",command=self.draw).pack(fill="x",pady=2)
        tk.Button(ctrl,text="Очистить",command=self.clear_canvas).pack(fill="x",pady=2)
        tk.Button(ctrl,text="Сохранить PPM",command=self.save_ppm).pack(fill="x",pady=2)

        self.canvas = tk.Label(root,image=self.photo)
        self.canvas.pack(side=tk.RIGHT,padx=6,pady=6)

    def load_svg(self):
        path = filedialog.askopenfilename(filetypes=[("SVG files","*.svg")])
        if not path: return
        vertices = parse_svg(path)
        if not vertices:
            messagebox.showerror("Ошибка","Не найден <polygon points=...>")
            return
        self.vertices = vertices
        messagebox.showinfo("SVG",f"Загружены вершины: {self.vertices}")

    def draw(self):
        if not self.vertices:
            messagebox.showerror("Ошибка","Сначала загрузите SVG")
            return
        self.img = Image.new("RGB",(self.W,self.H),(255,255,255))
        draw_func = dda_line
        draw_triangle(self.img,self.vertices)

        # Описанная окружность
        xc,yc,r = circumcircle(self.vertices)
        method = self.method_var.get()
        if method=="equation": circle_equation(self.img,xc,yc,r,(255,0,0))
        elif method=="param": circle_parametric(self.img,xc,yc,r,(0,255,0))
        elif method=="bresenham": circle_bresenham(self.img,xc,yc,r,(0,0,255))
        else: circle_builtin(self.img,xc,yc,r,(0,0,0))

        # Вписанная окружность
        xi,yi,ri = incircle(self.vertices)
        circle_builtin(self.img,xi,yi,ri,(255,165,0)) # оранжевая

        self.update_canvas()

    def clear_canvas(self):
        self.img = Image.new("RGB",(self.W,self.H),(255,255,255))
        self.update_canvas()

    def update_canvas(self):
        self.photo = ImageTk.PhotoImage(self.img)
        self.canvas.configure(image=self.photo)
        self.canvas.image = self.photo

    def save_ppm(self):
        path = filedialog.asksaveasfilename(defaultextension=".ppm",
                                            filetypes=[("PPM ASCII","*.ppm")])
        if not path: return
        save_ppm_ascii(self.img,path)
        messagebox.showinfo("Сохранено",f"PPM файл: {path}")

if __name__=="__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
