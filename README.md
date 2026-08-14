# Viral Ideas Engine

A system that **browses the web 24/7** (twice daily on GitHub's free servers)
and produces **iconic tech content packs**: script, title, caption, hashtags,
tips, thumbnail idea — plus a **premium voiceover MP3 and caption SRT file**
so you can drop them into your editor and cut the video yourself.

**Niche: technology.** Formats are modeled on high-converting viral tech
creators (workforce/autonomous, vocabulary reframing, ad remix, myth-takedown,
before/after).

## How it works

```
1. RESEARCH  - browses Hacker News (Algolia), Reddit (r/technology,
               r/artificial, r/Entrepreneur, r/SideProject), Bing News RSS,
               and GitHub trending. Ranks by heat + tech relevance.
2. GENERATE  - matches the hottest topic to a proven viral format, writes
               the full pack with a quality bar (specific, concrete,
               valuable - never vague slop).
3. VOICEOVER - edge-tts (free) renders the script into one MP3 with a
               matching SRT captions file, perfectly synced.
4. DELIVER   - everything lands in feed/ + research/ -> the dashboard.
```

## Your daily flow (10 min)

1. Open the dashboard (or check Gmail if configured)
2. Download **voiceover_latest.mp3** + **captions_latest.srt**
3. Drop both + the script into your editor (CapCut / Premiere)
4. Cut it, post it, reply to comments

## Dashboard

https://idkwhattonametsbro.github.io/viral-ideas-engine/dashboard/

- **PACK tab** — today's script/title/caption/tags/tips + audio player + downloads
- **RESEARCH tab** — what the web is talking about right now (live)
- **GENERATE NOW** — instant fresh pack (needs a GitHub token once, stored in your browser)

## Scheduling

Runs **twice daily** (03:00 + 15:00 UTC ≈ 07:00 + 19:00 Morocco) via
`.github/workflows/daily.yml`, plus manual dispatch anytime.

## Voiceover

- Free neural voices (rotates for variety): Guy, Aria, Jenny, Christopher, Eric, Michelle
- One continuous MP3, small gaps between beats, SRT synced to real audio durations
- Optional: add `GROQ_API_KEY` / `GEMINI_API_KEY` secrets to generate fresh
  copy with an LLM instead of the template formats

## Tests

```
python tests/run_all.py     # 9 tests: research, formats, chunking, slop-check, SRT, workflow
```

## Honest notes

- The system produces the **raw material** (idea + script + voice + captions).
  Editing taste is yours - that's where the premium lives.
- Ideas come from real web signals, so they track what's actually trending.
- No bots, no fake engagement, no income promises - just consistent,
  high-quality content fuel.
