import os, json, random
from groq import Groq

NAMES = {"rocky": "Rocky the red car", "blu": "Blu the blue car",
         "zippy": "Zippy the yellow car", "bolt": "Big Bolt the green truck"}
order = random.sample(list(NAMES), 4)   # kaun pehle nikle ga

FALLBACK = [
    "Good morning, sunny day!", "The garage door opens wide.",
    "One car rolls out, vroom vroom!", "Two cars now, zoom zoom!",
    "Three cars lined up, beep beep!", "Four friends ready to go!",
    "HONK! Everybody jumps up!", "Red, blue, yellow, green so bright!",
    "Let's count: one, two, three, four!", "Back home now, goodnight, cars!",
]

USER = f"""Write 10 very short rhyming captions (maximum 8 words each) for a one-minute nursery rhyme video for small kids.
Cars come out of a garage one by one in this order: {', '.join(NAMES[k] for k in order)}.
Caption for each scene:
1 Sunny morning, garage still closed.
2 The garage door opens.
3 {NAMES[order[0]]} rolls out. Must contain the word ONE.
4 {NAMES[order[1]]} rolls out. Must contain the word TWO.
5 {NAMES[order[2]]} rolls out. Must contain the word THREE.
6 {NAMES[order[3]]} rolls out. Must contain the word FOUR.
7 Funny: the truck honks and everybody jumps.
8 Learning colors: say red, blue, yellow, green.
9 Count together: one, two, three, four cars.
10 All cars go back home, door closes, goodnight.
Return ONLY valid JSON, no extra text: {{"title": "short title", "captions": ["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "c10"]}}
Simple English, child-friendly, make it fun and rhyming."""

title, captions = "Cars in the Garage", FALLBACK
key = os.environ.get("GROQ_API_KEY")
if key:
    client = Groq(api_key=key)
    done = False
    for m in ["openai/gpt-oss-120b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
        for attempt in range(2):
            try:
                print(f"Trying {m} (attempt {attempt+1})")
                r = client.chat.completions.create(
                    model=m, temperature=0.9,
                    messages=[{"role": "user", "content": USER}])
                t = r.choices[0].message.content
                d = json.loads(t[t.index("{"): t.rindex("}") + 1])
                caps = [str(c).strip() for c in d["captions"]][:10]
                assert len(caps) == 10 and all(caps)
                title, captions, done = str(d.get("title", title)), caps, True
                break
            except Exception as e:
                print("Failed:", e)
        if done:
            break
    if not done:
        print("Groq fail, fallback captions istemal ho rahe hain")

scenes = [{"narration": c, "sfx": "none"} for c in captions]
json.dump({"title": title, "order": order, "scenes": scenes},
          open("scenes.json", "w", encoding="utf-8"), ensure_ascii=False)

lines = [f"Title: {title}", ""] + [f"Scene {i+1}: {c}" for i, c in enumerate(captions)]
open("story.txt", "w", encoding="utf-8").write("\n".join(lines))
print("scenes.json aur story.txt ban gayi, order:", order)
