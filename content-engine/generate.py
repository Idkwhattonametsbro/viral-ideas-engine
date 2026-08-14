#!/usr/bin/env python3
"""
Nexus Viral Pack Generator
--------------------------
Fuses today's researched topics with PROVEN viral video formats (modeled on
high-converting tech creators) and writes a complete content pack:

  script (with beats) · title · caption · hashtags · tips · thumbnail idea
  + voiceover MP3 (edge-tts) + SRT captions file (for your editor)

Content quality bar: specific, concrete, valuable. Never vague slop.
"""
import json
import re
import sys
import wave
import shutil
import subprocess
import datetime
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FEED = ROOT / "feed"

VOICES = ["en-US-GuyNeural", "en-US-AriaNeural", "en-US-JennyNeural",
          "en-US-ChristopherNeural", "en-US-EricNeural", "en-US-MichelleNeural"]
RATE = "-8%"

# ---------------------------------------------------------------------------
# PROVEN FORMATS (from the viral examples)
# ---------------------------------------------------------------------------
FORMATS = [
    {
        "id": "workforce",
        "name": "The Autonomous Workforce",
        "pattern": (
            "[HOOK - urgency] {topic} are taking over the internet right now. "
            "This is how you get them working for you today.\n"
            "[WHO] And the people who figured this out first are already running "
            "entire operations without adding a Single Person to their team.\n"
            "[RETENTION BRIDGE] Watch till the end because the last thing I show you changes everything.\n"
            "[THE THING] It's called {thing}. The first platform where {topic} become real members of your team - "
            "with names, with roles, and the ability to work 24 hours a day.\n"
            "[RAPID-FIRE] Think creators. Think marketers. Think e-commerce. Think investors. "
            "Every single one of them can plug {topic} in and watch the busywork disappear.\n"
            "[PROOF] Every decision, every brief, every piece of feedback is remembered forever. "
            "No re-explaining. No lost ideas. No scattered files.\n"
            "[CTA] Comment '{keyword}' and I will send you the direct link. "
            "Make sure you follow - the system only sends it to followers."
        ),
    },
    {
        "id": "reframe",
        "name": "The Vocabulary Reframing",
        "pattern": (
            "[HOOK] {n} words to never say in {domain}.\n"
            "[PAIRS - rapid fire]\n"
            "Don't say {bad1}, instead say {good1} - because people {why1}.\n"
            "Don't say {bad2}, instead say {good2} - {why2}.\n"
            "Don't say {bad3}, instead say {good3} - {why3}.\n"
            "Don't say {bad4}, instead say {good4} - {why4}.\n"
            "Don't say {bad5}, instead say {good5} - {why5}.\n"
            "[CLOSE] Your {domain} does not have to sound like everyone else's. "
            "Comment '{keyword}' and I will send you the full list.\n"
            "Make sure you follow - it only goes to followers."
        ),
    },
    {
        "id": "remix",
        "name": "The Ad Creative Remix",
        "pattern": (
            "[HOOK - financial pain] Most people spend ${cost} testing {thing} to find the one that actually works. "
            "You can now recreate that success for free.\n"
            "[FLIP] Most people do this backwards. You just flip the equation: "
            "start with something that's already proven, then make it yours.\n"
            "[THE TOOL] Go to {thing}. Find one you like, click it, upload your logo, "
            "your product images, your colors. It rebuilds the exact same structure "
            "that's already converting.\n"
            "[VISUAL PROOF] You are pointing at a {thing} that is already making someone else money, "
            "and saying: build this, but make it mine.\n"
            "[CTA] Comment '{keyword}' and I will send you the direct link. "
            "Follow first - the system only sends it to followers."
        ),
    },
    {
        "id": "takedown",
        "name": "The Industry Takedown (myth vs truth)",
        "pattern": (
            "[HOOK - contrarian] Everything you know about {topic} is wrong. Here is what actually works.\n"
            "[MYTH] Most people think {myth}.\n"
            "[TRUTH] The truth: {truth}.\n"
            "[WHY] Here is why this matters right now: {why}.\n"
            "[PROOF] I have tested this. {proof}.\n"
            "[CTA] Comment '{keyword}' and I will send you the playbook. Follow so you don't miss the next one."
        ),
    },
    {
        "id": "beforeafter",
        "name": "The Before/After Transformation",
        "pattern": (
            "[HOOK] I went from {before} to {after} using only {topic} - and it took {time}.\n"
            "[STEP 1] Step one: {step1}.\n"
            "[STEP 2] Step two: {step2}.\n"
            "[STEP 3] Step three: {step3}.\n"
            "[RESULT] The result: {result}.\n"
            "[CTA] Comment '{keyword}' and I will send you the exact system. Follow - it only goes to followers."
        ),
    },
]

# Value-laden word swaps for the reframe format
REFRAIMES = {
    "sales": [
        ("buy", "invest", "people invest in value, not purchases"),
        ("sign", "authorize", "authorizing feels like a choice, not a trap"),
        ("customer", "client", "clients feel like partners, customers feel like numbers"),
        ("problem", "concern", "concerns get solved, problems get blamed"),
        ("cheap", "affordable", "affordable feels smart, cheap feels risky"),
        ("maybe", "absolutely", "certainty closes, maybe kills"),
        ("contract", "agreement", "agreements are mutual, contracts feel one-sided"),
    ],
    "AI copywriting": [
        ("utilize", "use", "short words win"),
        ("leverage", "apply", "leveraged is AI-slop"),
        ("delve", "dig into", "nobody says delve"),
        ("game-changer", "turns things around", "cliche alerts"),
        ("in today's world", "right now", "timeless"),
        ("revolutionize", "change", "nobody believes revolution"),
        ("empower", "help", "empower is corporate noise"),
    ],
    "productivity": [
        ("work harder", "work smarter", "effort isn't the edge"),
        ("multitask", "batch", "batching actually finishes"),
        ("hustle", "system", "hustle burns out, systems compound"),
        ("stay busy", "stay focused", "busy is a trap"),
        ("more hours", "better blocks", "hours don't scale, focus does"),
        ("discipline", "routine", "discipline fades, routine holds"),
        ("try harder", "simplify", "simpler survives"),
    ],
}


def pick_format(rng, topic):
    return rng.choice(FORMATS)


def render_pattern(fmt, rng, topic, thing, keyword):
    """Fill a format's template with concrete, specific content."""
    p = fmt["pattern"]
    if fmt["id"] == "reframe":
        domain = rng.choice(list(REFRAIMES.keys()))
        pairs = rng.sample(REFRAIMES[domain], 5)
        p = p.format(
            n=len(pairs), domain=domain,
            bad1=pairs[0][0], good1=pairs[0][1], why1=pairs[0][2],
            bad2=pairs[1][0], good2=pairs[1][1], why2=pairs[1][2],
            bad3=pairs[2][0], good3=pairs[2][1], why3=pairs[2][2],
            bad4=pairs[3][0], good4=pairs[3][1], why4=pairs[3][2],
            bad5=pairs[4][0], good5=pairs[4][1], why5=pairs[4][2],
            keyword=keyword,
        )
    elif fmt["id"] == "workforce":
        p = p.format(topic=topic.title(), thing=thing, keyword=keyword)
    elif fmt["id"] == "remix":
        p = p.format(cost=rng.choice(["4,000", "10,000", "50,000"]), thing=thing,
                     keyword=keyword)
    elif fmt["id"] == "takedown":
        p = p.format(topic=topic, myth="it is too late to start",
                     truth=f"the window is open exactly because {topic} is still confusing to most people",
                     why=f"early movers in {topic} get 10x the attention for half the effort",
                     proof=f"the fastest-growing accounts right now are all built on {topic}",
                     keyword=keyword)
    elif fmt["id"] == "beforeafter":
        p = p.format(before="confused and overwhelmed", after="running it on autopilot",
                     topic=topic, time=rng.choice(["a weekend", "14 days", "one month"]),
                     step1=f"pick ONE tool in the {topic} space and master it",
                     step2="systemize the workflow so it runs without you",
                     step3="document the results and post the process",
                     result="a system that works while you sleep",
                     keyword=keyword)
    return p


def title_for(fmt_id, topic, thing, rng):
    t = {
        "workforce": [f"{topic.title()} Are Taking Over - This Is How You Get Them On Your Team",
                      f"This Platform Turns {topic.title()} Into Your 24/7 Workforce",
                      f"{topic.title()}: The Unfair Advantage Nobody Is Talking About"],
        "reframe": ["7 Words To Never Say In Sales", "Stop Saying These 7 Words Immediately",
                    "The Vocabulary That Doubles Your Conversion Rate"],
        "remix": [f"Stop Wasting Money On Ads - Remix What Already Works",
                  "Recreate A Winning Ad For Free In 5 Minutes",
                  f"How To Copy A Proven Ad (Legally) And Win"],
        "takedown": [f"Everything You Know About {topic.title()} Is Wrong",
                     f"The {topic.title()} Myth That's Costing You Money",
                     f"Why {topic.title()} Is Not What You Think"],
        "beforeafter": [f"I Went From Zero To Automated With {topic.title()}",
                        f"{topic.title()} Changed Everything In 30 Days",
                        f"How {topic.title()} Made My Work Disappear"],
    }.get(fmt_id, [f"{topic.title()} - The Untold Story"])
    return rng.choice(t)[:80]


def caption_for(fmt_id, topic, keyword, rng):
    c = {
        "workforce": f"{topic.title()} are moving fast. The people who start now get the unfair advantage. Comment '{keyword}' and follow for the direct link.",
        "reframe": "Words change how people feel about buying. These 7 swaps work everywhere. Comment '{keyword}' and follow for the full list.",
        "remix": "Stop testing from zero. Remix what already converts. Comment '{keyword}' and follow for the direct link.",
        "takedown": f"Most people are 2 years late on {topic}. The ones who act now win. Comment '{keyword}' and follow.",
        "beforeafter": "Systems beat motivation every time. Comment '{keyword}' and follow for the exact system.",
    }.get(fmt_id, "Follow for daily tech breakdowns.")
    return c.format(topic=topic, keyword=keyword)


def hashtags_for(topic, rng):
    base = ["#technology", "#tech", "#aitools", "#futureofwork", "#automation",
            "#aitrends", "#technews", "#startup", "#aiagents", "#productivity"]
    rng.shuffle(base)
    tags = base[:3]
    word = re.sub(r"[^a-z0-9]", "", topic.lower())[:18]
    if word and len(word) > 3 and f"#{word}" not in tags:
        tags.append(f"#{word}")
    return tags[:4]


def tips_for(fmt_id, topic, rng):
    tips = [
        "Post at evening local time (19:00-21:00) for max initial engagement.",
        "Reply to EVERY comment in the first hour - it doubles the algorithm push.",
        "Pin your own comment with the direct link + a question.",
        "Keep the first 2 seconds purely the hook - no intro, no logo.",
        "Same 3-4 keywords in title, spoken line, and on-screen text.",
        "Post 4-5 times a week consistently for 4 weeks before judging anything.",
        "End every video with the same follow CTA so it becomes a habit for viewers.",
        "Use 3 hashtags max. More looks desperate.",
    ]
    rng.shuffle(tips)
    return tips[:3]


def thumb_idea_for(fmt_id, topic, rng):
    t = {
        "workforce": f"Clean light UI mockup + big text '{topic.title()} ON YOUR TEAM' with a blue accent, phone in hand.",
        "reframe": "Split screen: red X words vs green check words, big bold '7 WORDS' in the middle.",
        "remix": "Before/after mockup of an ad, big text 'REMAKE THIS AD - FREE' with a dollar-sign strike-through.",
        "takedown": f"Big myth crossed out + '{topic.upper()}: THE TRUTH' in bold, light background.",
        "beforeafter": "Two columns 'BEFORE chaos' vs 'AFTER system' with an arrow between.",
    }.get(fmt_id, "Clean light background, bold 3-word headline, subtle blue accent.")
    return t


def script_to_chunks(script: str):
    """Split script into natural voiceover chunks (sentence-ish, <=90 chars)."""
    text = script.replace("[HOOK - urgency] ", "").replace("[RETENTION BRIDGE] ", "")
    text = re.sub(r"\[[A-Z_ -]+\]", "", text)  # strip beat markers
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks = []
    for s in sentences:
        s = s.strip()
        while len(s) > 90:
            cut = s[:88].rsplit(" ", 1)[0]
            chunks.append(cut)
            s = s[len(cut):].strip()
        if s:
            chunks.append(s)
    return chunks


def tts(text: str, voice: str, out: Path) -> bool:
    import time
    for attempt in range(3):
        try:
            r = subprocess.run(["edge-tts", "--voice", voice, f"--rate={RATE}",
                                "--text", text, "--write-media", str(out)],
                               capture_output=True, text=True, timeout=60)
            if r.returncode == 0 and out.exists() and out.stat().st_size > 1000:
                return True
        except Exception:
            pass
        time.sleep(1.0 * (attempt + 1))
    return False


def probe_dur(path: Path) -> float:
    try:
        r = subprocess.run(["ffmpeg", "-i", str(path)], capture_output=True, text=True, timeout=30)
        m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", r.stderr)
        if m:
            return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    except Exception:
        pass
    return 3.0


def build_voiceover(chunks, voice, tmpdir):
    """One continuous MP3 + SRT with real timings."""
    mp3s, durs = [], []
    for i, ch in enumerate(chunks):
        mp3 = tmpdir / f"c{i}.mp3"
        if tts(ch, voice, mp3):
            d = probe_dur(mp3)
            mp3s.append((mp3, d))
            durs.append(d)
    if not mp3s:
        return None, None

    # concat with tiny 0.18s gaps
    segs = []
    for i, (mp3, d) in enumerate(mp3s):
        segs.append(str(mp3))
        gap = tmpdir / f"g{i}.wav"
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                        "-t", "0.18", str(gap)], capture_output=True, text=True)
        segs.append(str(gap))

    listfile = tmpdir / "list.txt"
    listfile.write_text("\n".join(f"file '{s}'" for s in segs), encoding="utf-8")
    out_mp3 = tmpdir / "voice.mp3"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
                    "-c", "copy", str(out_mp3)], capture_output=True, text=True)
    if not out_mp3.exists():
        return None, None

    # SRT with real timings
    srt_lines, t = [], 0.0
    for i, (mp3, d) in enumerate(mp3s):
        srt_lines.append(str(i + 1))
        srt_lines.append(f"{fmt_srt(t)} --> {fmt_srt(t + d)}")
        srt_lines.append(chunks[i])
        srt_lines.append("")
        t += d + 0.18
    return out_mp3, "\n".join(srt_lines)


def fmt_srt(sec):
    ms = int(round((sec - int(sec)) * 1000))
    s = int(sec) % 60
    m = (int(sec) // 60) % 60
    h = int(sec) // 3600
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    FEED.mkdir(exist_ok=True)
    rng = __import__("random").Random()

    # load research topics
    res = None
    rp = ROOT / "research" / "latest.json"
    if rp.exists():
        try:
            res = json.loads(rp.read_text(encoding="utf-8"))
        except Exception:
            res = None
    # Prefer clean editorial topics (HN/Reddit/Bing) over raw repo slugs.
    def clean_topic(it):
        t = (it.get("title") or "").strip()
        src = it.get("source") or ""
        if src == "GitHub" and (" - " in t):
            t = t.split(" - ", 1)[1]  # use the description, not the repo slug
        t = re.sub(r"[^A-Za-z0-9 .,!?'-]+", "", t)
        t = re.sub(r"\s+", " ", t).strip()
        if len(t) < 12 or len(t) > 110:
            return None
        if "error" in src.lower():
            return None
        return t

    ranked = (res or {}).get("top", [])
    clean = [clean_topic(it) for it in ranked]
    clean = [c for c in clean if c]
    # editorial sources first
    pref = [c for c in clean if any(k in c.lower() for k in ("ai", "agent", "gpt", "model", "openai", "google", "microsoft", "apple", "nvidia", "software", "startup", "app", "data", "code", "tech", "chip", "cloud", "automation"))]
    pool = pref if pref else clean
    topic = rng.choice(pool) if pool else "AI agents"

    fmt = pick_format(rng, topic)
    thing = rng.choice([
        "the platform everyone is switching to", "a free tool you already have access to",
        "the exact system top creators use", "an open-source project that does it all",
    ])
    keyword = rng.choice(["ALPHA", "TOOL", "SECRET", "START", "SYS", "EDGE", "MOVE"])
    script = render_pattern(fmt, rng, topic, thing, keyword)
    title = title_for(fmt["id"], topic, thing, rng)
    caption = caption_for(fmt["id"], topic, keyword, rng)
    tags = hashtags_for(topic, rng)
    tips = tips_for(fmt["id"], topic, rng)
    thumb = thumb_idea_for(fmt["id"], topic, rng)

    today = datetime.date.today().isoformat()
    pack = {
        "date": today,
        "format": fmt["name"],
        "source_topic": topic,
        "keyword": keyword,
        "title": title,
        "caption": caption,
        "hashtags": tags,
        "tips": tips,
        "thumbnail": thumb,
        "script": script,
    }
    (FEED / f"{today}.json").write_text(json.dumps(pack, indent=2, ensure_ascii=False), encoding="utf-8")
    (FEED / "latest.json").write_text(json.dumps(pack, indent=2, ensure_ascii=False), encoding="utf-8")

    md = f"""# Viral Tech Pack · {today}

**Format:** {fmt['name']} · **Source topic:** {topic}

---

## SCRIPT (read this in your editor)
{script}

## TITLE
{title}

## CAPTION
{caption}

## HASHTAGS
{' '.join(tags)}

## POSTING TIPS
{chr(10).join('- ' + t for t in tips)}

## THUMBNAIL IDEA
{thumb}

---
**Keyword CTA:** comment '{keyword}' · **Voiceover file:** voiceover_{today}.mp3 · **Captions:** captions_{today}.srt
"""
    (FEED / f"{today}.md").write_text(md, encoding="utf-8")
    (FEED / "latest.md").write_text(md, encoding="utf-8")

    # voiceover
    tmpdir = Path(tempfile.mkdtemp(prefix="nexvo_"))
    try:
        chunks = script_to_chunks(script)
        voice = rng.choice(VOICES)
        vo, srt = build_voiceover(chunks, voice, tmpdir)
        if vo:
            (FEED / f"voiceover_{today}.mp3").write_bytes(vo.read_bytes())
            (FEED / "voiceover_latest.mp3").write_bytes(vo.read_bytes())
            if srt:
                (FEED / f"captions_{today}.srt").write_text(srt, encoding="utf-8")
                (FEED / "captions_latest.srt").write_text(srt, encoding="utf-8")
            print(f"[Voiceover] {len(chunks)} chunks -> voiceover_{today}.mp3 + captions_{today}.srt")
        else:
            print("[Voiceover] failed (edge-tts unavailable)")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print(f"[Pack] {fmt['name']} · topic: {topic[:60]}")
    print(f"[Pack] Title: {title}")
    print(md[:600])


if __name__ == "__main__":
    main()
