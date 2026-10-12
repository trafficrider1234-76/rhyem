import json, math, os, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, DUR = 1080, 1920, 24, 60.0
SC = 3                                   # smooth edges ke liye supersampling
GX, GROUND = 200, 1290                   # garage ki dewaar, sarak ki line
DOOR_X, DOOR_TOP, DOOR_H = 110, 1110, 180
GY0 = 780
RET_T, RET_SPEED = 54.3, 520
OUT = "output_temp"
os.makedirs(OUT, exist_ok=True)

meta = json.load(open("scenes.json", encoding="utf-8"))
order = meta.get("order") or ["rocky", "blu", "zippy", "bolt"]


# ---------------- helpers ----------------
def font(px):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, int(px))
    return ImageFont.load_default()

def blank(w, h):
    return Image.new("RGBA", (int(w * SC), int(h * SC)), (0, 0, 0, 0))

def fin(im):
    return im.resize((max(1, im.width // SC), max(1, im.height // SC)), Image.LANCZOS)

def rr(d, box, r, fill):
    d.rounded_rectangle([int(v * SC) for v in box], radius=int(r * SC), fill=fill)

def poly(d, pts, fill):
    d.polygon([(int(x * SC), int(y * SC)) for x, y in pts], fill=fill)

def circ(d, cx, cy, r, fill):
    d.ellipse([int((cx - r) * SC), int((cy - r) * SC),
               int((cx + r) * SC), int((cy + r) * SC)], fill=fill)

def smooth(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)

DARK = (40, 40, 60, 255)

def text_sprite(text, px, fg, bg, pad=24):
    f = font(px * SC)
    probe = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    l, t, r, b = probe.textbbox((0, 0), text, font=f, stroke_width=3 * SC)
    w, h = r - l + 2 * pad * SC, b - t + 2 * pad * SC
    w -= w % SC
    h -= h % SC
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=int(h * 0.4), fill=bg + (255,),
                        outline=(255, 255, 255, 255), width=5 * SC)
    d.text((pad * SC - l, pad * SC - t), text, font=f, fill=fg,
           stroke_width=3 * SC, stroke_fill=DARK)
    return fin(im)

def badge_sprite(text, color, d_px):
    im = blank(d_px, d_px)
    d = ImageDraw.Draw(im)
    circ(d, d_px / 2, d_px / 2, d_px / 2, (255, 255, 255, 255))
    circ(d, d_px / 2, d_px / 2, d_px / 2 * 0.9, color + (255,))
    f = font(d_px * 0.62 * SC)
    l, t, r, b = d.textbbox((0, 0), text, font=f)
    d.text((d_px * SC / 2 - (l + r) / 2, d_px * SC / 2 - (t + b) / 2), text, font=f,
           fill=(255, 255, 255, 255), stroke_width=3 * SC, stroke_fill=DARK)
    return fin(im)


# ---------------- gaariyan ----------------
def make_car(w, body, accent):
    h = int(w * 0.6)
    r = int(w * 0.13)
    im = blank(w, h)
    d = ImageDraw.Draw(im)
    wc = [(0.24 * w, h - r), (0.76 * w, h - r)]
    rr(d, (0.02 * w, 0.40 * h, 0.98 * w, 0.80 * h), 0.14 * h, body + (255,))
    poly(d, [(0.26 * w, 0.44 * h), (0.38 * w, 0.08 * h), (0.68 * w, 0.08 * h),
             (0.82 * w, 0.44 * h)], body + (255,))
    poly(d, [(0.31 * w, 0.42 * h), (0.41 * w, 0.15 * h), (0.66 * w, 0.15 * h),
             (0.76 * w, 0.42 * h)], (190, 230, 255, 255))
    rr(d, (0.04 * w, 0.58 * h, 0.96 * w, 0.66 * h), 0.03 * h, accent + (255,))
    for ex in (0.50, 0.64):
        circ(d, ex * w, 0.28 * h, 0.055 * w, (255, 255, 255, 255))
        circ(d, ex * w + 0.012 * w, 0.29 * h, 0.03 * w, (20, 20, 30, 255))
    circ(d, 0.93 * w, 0.52 * h, 0.035 * w, (255, 240, 120, 255))
    circ(d, 0.06 * w, 0.52 * h, 0.025 * w, (230, 40, 40, 255))
    for cx, cy in wc:
        circ(d, cx, cy, r + 5, (40, 40, 50, 255))
    return fin(im), wc, r

def make_truck(w, cab, box):
    h = int(w * 0.62)
    r = int(w * 0.11)
    im = blank(w, h)
    d = ImageDraw.Draw(im)
    wc = [(0.17 * w, h - r), (0.45 * w, h - r), (0.84 * w, h - r)]
    rr(d, (0.01 * w, 0.04 * h, 0.66 * w, 0.76 * h), 0.04 * h, box + (255,))
    rr(d, (0.04 * w, 0.38 * h, 0.63 * w, 0.46 * h), 0.02 * h, (255, 255, 255, 120))
    rr(d, (0.66 * w, 0.30 * h, 0.99 * w, 0.80 * h), 0.08 * h, cab + (255,))
    rr(d, (0.72 * w, 0.37 * h, 0.95 * w, 0.58 * h), 0.03 * h, (190, 230, 255, 255))
    for ex in (0.80, 0.89):
        circ(d, ex * w, 0.475 * h, 0.034 * w, (255, 255, 255, 255))
        circ(d, ex * w + 0.007 * w, 0.485 * h, 0.018 * w, (20, 20, 30, 255))
    circ(d, 0.975 * w, 0.68 * h, 0.03 * w, (255, 240, 120, 255))
    rr(d, (0, 0.74 * h, w, 0.84 * h), 0.03 * h, (60, 60, 70, 255))
    for cx, cy in wc:
        circ(d, cx, cy, r + 5, (40, 40, 50, 255))
    return fin(im), wc, r

_wb, _wc = {}, {}
def wheel(r, ang):
    if r not in _wb:
        im = blank(2 * r, 2 * r)
        d = ImageDraw.Draw(im)
        circ(d, r, r, r, (35, 35, 40, 255))
        circ(d, r, r, r * 0.62, (205, 210, 220, 255))
        for k in range(4):
            a = k * math.pi / 2
            d.line([(r * SC, r * SC), (r * SC + r * 0.6 * SC * math.cos(a),
                                       r * SC + r * 0.6 * SC * math.sin(a))],
                   fill=(110, 115, 130, 255), width=int(r * 0.14 * SC))
        circ(d, r, r - r * 0.42, r * 0.12, (255, 200, 40, 255))   # ghoomta nishan
        circ(d, r, r, r * 0.2, (90, 95, 105, 255))
        _wb[r] = fin(im)
    a = int(ang % 360 // 6) * 6
    if (r, a) not in _wc:
        _wc[(r, a)] = _wb[r].rotate(a, resample=Image.BICUBIC)
    return _wc[(r, a)]

SPEC = {
    "rocky": dict(name="RED", color=(225, 45, 50), accent=(255, 255, 255), w=200),
    "blu": dict(name="BLUE", color=(40, 110, 230), accent=(255, 225, 60), w=200),
    "zippy": dict(name="YELLOW", color=(250, 200, 20), accent=(30, 30, 30), w=200),
    "bolt": dict(name="GREEN", color=(40, 170, 80), accent=(255, 140, 30), w=280, truck=True),
}
cars = {}
for i, (key, sp) in enumerate(SPEC.items()):
    if sp.get("truck"):
        spr, wc, r = make_truck(sp["w"], sp["color"], sp["accent"])
    else:
        spr, wc, r = make_car(sp["w"], sp["color"], sp["accent"])
    cars[key] = dict(key=key, spr=spr, sprf=spr.transpose(Image.FLIP_LEFT_RIGHT),
                     wc=wc, r=r, w=spr.width, h=spr.height,
                     color=sp["color"], name=sp["name"], ph=i * 1.3)

right = 1050                         # pehli gaari sab se door, aakhri garage ke qareeb
for k, key in enumerate(order):
    c = cars[key]
    c["exit"] = 12.6 + 6.0 * k
    c["final"] = right - c["w"]
    right = c["final"] + 10

def car_x(c, t):
    hidden = GX - c["w"]
    flip = t >= RET_T - 0.2
    if t >= RET_T:
        return max(c["final"] - RET_SPEED * (t - RET_T), hidden - 60), flip
    u = (t - c["exit"]) / 3.0
    if u <= 0:
        return hidden, flip
    u = min(u, 1.0)
    return hidden + (c["final"] - hidden) * (1 - (1 - u) ** 2), flip

def door_open(t):
    if t < 7: return 0.0
    if t < 10: return (t - 7) / 3
    if t < 56.3: return 1.0
    if t < 57.8: return 1 - (t - 56.3) / 1.5
    return 0.0


# ---------------- background ----------------
def make_sky():
    y = np.linspace(0, 1, H)[:, None, None] ** 1.3
    top, bot = np.array([110, 190, 255]), np.array([255, 240, 215])
    arr = np.broadcast_to(top + (bot - top) * y, (H, W, 3)).astype(np.uint8)
    return Image.fromarray(arr, "RGB")

def make_ground():
    im = blank(W, H)
    d = ImageDraw.Draw(im)
    def curve(base, a1, p1, a2, p2, col):
        pts = [(x, base - a1 * math.sin(x / p1) - a2 * math.sin(x / p2)) for x in range(0, W + 21, 20)]
        poly(d, pts + [(W + 20, H), (0, H)], col)
    curve(1000, 70, 170, 25, 60, (140, 208, 140, 255))
    curve(1085, 45, 210, 15, 70, (100, 190, 105, 255))
    rr(d, (0, 1110, W, H), 0, (88, 178, 98, 255))
    rr(d, (0, 1180, W, 1340), 0, (88, 90, 104, 255))
    rr(d, (0, 1180, W, 1192), 0, (235, 235, 240, 255))
    rr(d, (0, 1328, W, 1340), 0, (235, 235, 240, 255))
    for x in range(0, W, 120):
        rr(d, (x + 20, 1312, x + 80, 1320), 3, (255, 230, 90, 255))
    for x, y in [(160, 1480), (450, 1560), (760, 1500), (960, 1640)]:
        rr(d, (x - 12, y, x + 12, y + 90), 4, (120, 80, 50, 255))
        circ(d, x, y - 20, 75, (50, 150, 70, 255))
        circ(d, x - 22, y - 40, 30, (80, 185, 95, 255))
    rnd = random.Random(3)
    for _ in range(40):
        circ(d, rnd.randint(20, W - 20), rnd.randint(1380, 1860), 7,
             rnd.choice([(255, 120, 160, 255), (255, 255, 255, 255), (255, 210, 60, 255)]))
    # garage
    rr(d, (-20, 880, GX, GROUND), 0, (250, 205, 60, 255))
    rr(d, (GX - 8, 880, GX, GROUND), 0, (215, 170, 40, 255))
    poly(d, [(-30, 880), (GX + 30, 880), (GX + 10, 820), (-30, 820)], (200, 60, 60, 255))
    rr(d, (8, 905, GX - 12, 975), 12, (255, 255, 255, 255))
    f = font(30 * SC)
    l, t, r, b = d.textbbox((0, 0), "GARAGE", font=f)
    d.text(((8 + GX - 12) / 2 * SC - (l + r) / 2, 940 * SC - (t + b) / 2), "GARAGE",
           font=f, fill=(200, 60, 60, 255))
    rr(d, (DOOR_X - 6, DOOR_TOP - 6, GX, GROUND), 0, (110, 110, 125, 255))
    rr(d, (DOOR_X, DOOR_TOP, GX, GROUND), 0, (35, 28, 45, 255))
    return fin(im).crop((0, GY0, W, H))

def make_door():
    im = blank(GX - DOOR_X, DOOR_H)
    d = ImageDraw.Draw(im)
    rr(d, (0, 0, GX - DOOR_X, DOOR_H), 0, (185, 190, 205, 255))
    for y in range(0, DOOR_H, 30):
        rr(d, (0, y, GX - DOOR_X, y + 4), 0, (140, 145, 160, 255))
    return fin(im)

def make_cloud(s):
    im = blank(300 * s, 140 * s)
    d = ImageDraw.Draw(im)
    for cx, cy, r in [(90, 90, 55), (150, 70, 70), (215, 95, 50), (150, 100, 60)]:
        circ(d, cx * s, cy * s, r * s, (255, 255, 255, 235))
    return fin(im)

def make_sun():
    im = blank(360, 360)
    d = ImageDraw.Draw(im)
    circ(d, 180, 180, 170, (255, 240, 160, 90))
    circ(d, 180, 180, 120, (255, 220, 60, 255))
    return fin(im)

def make_star(size):
    im = blank(size, size)
    d = ImageDraw.Draw(im)
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        r = size / 2 * (1 if i % 2 == 0 else 0.45)
        pts.append((size / 2 + r * math.cos(a), size / 2 + r * math.sin(a)))
    poly(d, pts, (255, 225, 60, 255))
    return fin(im)

SKY, GROUND_IMG, DOOR, SUN = make_sky(), make_ground(), make_door(), make_sun()
CLOUDS = [(make_cloud(1.0), 230, 18, 100), (make_cloud(0.7), 470, 12, 600), (make_cloud(0.85), 640, 9, 900)]
STAR = make_star(90)
STARS = [(120, 700), (330, 560), (700, 640), (930, 540), (540, 420), (980, 820)]
BADGE = {n: badge_sprite(str(n), cars[order[n - 1]]["color"], 330) for n in range(1, 5)}
NUM = {n: badge_sprite(str(n), cars[order[n - 1]]["color"], 110) for n in range(1, 5)}
LABEL = {k: text_sprite(cars[k]["name"], 60, (255, 255, 255, 255), cars[k]["color"]) for k in cars}
HONK = text_sprite("HONK!", 64, (210, 30, 30, 255), (255, 255, 255))


# ---------------- frame ----------------
def draw_car(f, c, t):
    x, flip = car_x(c, t)
    if x >= W or x + c["w"] <= 0:
        return
    v = (car_x(c, t + 0.05)[0] - car_x(c, t - 0.05)[0]) / 0.1
    dy = 0
    if abs(v) > 40:
        dy = int(3 * math.sin(t * 30 + c["ph"]))
    if 48 <= t < 54:
        dy = -int(abs(14 * math.sin((t - 48) * 5 + c["ph"])))
    for t0 in (37.0, 38.2):
        if t0 <= t < t0 + 0.5:
            if c["key"] == "bolt":
                dy += int(5 * math.sin(t * 70))
            else:
                dy -= int(55 * abs(math.sin(math.pi * (t - t0) / 0.5)))
    spr = c["sprf"] if flip else c["spr"]
    y0 = GROUND - c["h"] + dy
    f.paste(spr, (int(x), int(y0)), spr)
    ang = -(x - (GX - c["w"])) / c["r"] * 57.2958
    if 48 <= t < 54:
        ang -= (t - 48) * 400
    for cx, cy in c["wc"]:
        if flip:
            cx = c["w"] - cx
        wi = wheel(c["r"], ang)
        f.paste(wi, (int(x + cx - c["r"]), int(y0 + cy - c["r"])), wi)

def paste_center(f, spr, cx, cy, s=1.0):
    w2, h2 = int(spr.width * s), int(spr.height * s)
    if w2 < 2 or h2 < 2:
        return
    img = spr.resize((w2, h2), Image.LANCZOS)
    f.paste(img, (int(cx - w2 / 2), int(cy - h2 / 2)), img)

def compose(t):
    f = SKY.copy()
    sy = int(1080 - 700 * smooth(t / 12.0))
    f.paste(SUN, (780 - SUN.width // 2, sy - SUN.height // 2), SUN)
    for cl, y, sp, x0 in CLOUDS:
        f.paste(cl, (int((x0 + sp * t) % (W + 600) - 300), y), cl)
    f.paste(GROUND_IMG, (0, GY0), GROUND_IMG)
    vis = int(DOOR_H * (1 - door_open(t)))
    if vis > 0:
        f.paste(DOOR.crop((0, 0, DOOR.width, vis)), (DOOR_X, DOOR_TOP))
    left = f.crop((0, 0, GX, H))
    for key in sorted(order, key=lambda k: cars[k]["final"]):
        draw_car(f, cars[key], t)
    f.paste(left, (0, 0))          # garage ke andar wala hissa chhup jata hai

    if 13.0 <= t < 54.0:           # bara ginti badge
        n, tc = 0, 0
        for k in order:
            if t >= cars[k]["exit"] + 1.2:
                n += 1
                tc = cars[k]["exit"] + 1.2
        if n:
            paste_center(f, BADGE[n], 540, 330, 0.8 * (1 + 0.25 * max(0, 1 - (t - tc) / 0.35)))

    for k, key in enumerate(order):
        c = cars[key]
        cx = c["final"] + c["w"] / 2
        cy = GROUND - c["h"] - 110
        if 43 + k <= t < 48.4:
            paste_center(f, LABEL[key], cx, cy, min(1, (t - 43 - k) / 0.25) ** 0.5)
        elif 49 + k <= t < 54:
            paste_center(f, NUM[k + 1], cx, cy, min(1, (t - 49 - k) / 0.25) ** 0.5)
    for t0 in (37.0, 38.2):
        if t0 <= t < t0 + 0.6:
            b = cars["bolt"]
            paste_center(f, HONK, b["final"] + b["w"] / 2, GROUND - b["h"] - 130)
    if t >= 58.3:
        for i, (sx, sy2) in enumerate(STARS):
            paste_center(f, STAR, sx, sy2, 0.7 + 0.3 * math.sin(t * 6 + i))
    return f


# ---------------- sound events (postprocess.py padhta hai) ----------------
ev = [[7.0, "whoosh"], [10.0, "bump"]]
for k in order:
    ev += [[cars[k]["exit"], "vroom"], [cars[k]["exit"] + 2.6, "sparkle"]]
ev += [[37.0, "horn"], [37.1, "boing"], [38.2, "horn"], [38.3, "boing"]]
ev += [[43.0 + i, "pop"] for i in range(4)] + [[48.2, "engine"]]
ev += [[49.0 + i, "pop"] for i in range(4)] + [[53.0, "sparkle"]]
ev += [[RET_T, "vroom"], [58.0, "bump"], [58.4, "sparkle"]]
json.dump(ev, open("events.json", "w"))

# ---------------- render ----------------
p = subprocess.Popen(
    ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
     "-i", "-", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p",
     f"{OUT}/output.mp4"], stdin=subprocess.PIPE)
total = int(DUR * FPS)
for n in range(total):
    p.stdin.write(compose(n / FPS).tobytes())
    if n % 120 == 0:
        print(f"frame {n}/{total}", flush=True)
p.stdin.close()
if p.wait() != 0:
    raise RuntimeError("ffmpeg encode fail")
print("output.mp4 tayyar")
