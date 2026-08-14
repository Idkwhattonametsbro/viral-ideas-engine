#!/usr/bin/env python3
"""
Nexus Viral Research Engine
---------------------------
Browses the web for real (no API keys): Hacker News (Algolia), Reddit,
Bing News RSS, and GitHub trending. Ranks topics by freshness + heat and
returns the top candidate topics for today's viral tech content pack.
"""
import json
import re
import html
import datetime
import urllib.request
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "research"


def fetch(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (NexusViralEngine)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def fetch_json(url: str, timeout: int = 20):
    return json.loads(fetch(url, timeout))


def safe(fn):
    """Wrap any source call so the engine never dies on one bad site."""
    def wrapper(*a, **k):
        try:
            return fn(*a, **k)
        except Exception as e:
            return [{"source": "error", "title": f"{fn.__name__} failed: {e}", "points": 0, "url": ""}]
    return wrapper


@safe
def hn_top(limit: int = 12) -> list:
    """Top stories right now from Hacker News."""
    out = []
    try:
        d = fetch_json("https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=24")
        for hit in d.get("hits", [])[:limit]:
            title = hit.get("title") or ""
            if title and len(title) > 8:
                out.append({"source": "HackerNews", "title": title.strip(),
                            "points": hit.get("points") or 0,
                            "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"})
    except Exception as e:
        out.append({"source": "error", "title": f"hn failed: {e}", "points": 0, "url": ""})
    return out


@safe
def reddit_top(subreddits=("technology", "artificial", "Entrepreneur", "SideProject"), limit: int = 8) -> list:
    out = []
    for sub in subreddits:
        try:
            d = fetch_json(f"https://www.reddit.com/r/{sub}/hot.json?limit=8", timeout=15)
            for post in d.get("data", {}).get("children", []):
                p = post.get("data", {})
                title = p.get("title") or ""
                if title and not p.get("stickied"):
                    out.append({"source": f"r/{sub}", "title": title.strip(),
                                "points": p.get("score") or 0,
                                "url": "https://www.reddit.com" + (p.get("permalink") or "")})
        except Exception as e:
            out.append({"source": "error", "title": f"reddit {sub} failed: {e}", "points": 0, "url": ""})
    return out[:limit]


@safe
def bing_news_top(query: str = "AI technology", limit: int = 8) -> list:
    """Bing News RSS - keyless current news."""
    out = []
    try:
        xml = fetch(f"https://www.bing.com/news/search?q={urllib.parse.quote(query)}&format=rss")
        items = re.findall(r"<item>(.*?)</item>", xml, re.S)
        for it in items[:limit]:
            m = re.search(r"<title>(.*?)</title>", it, re.S)
            if m:
                title = html.unescape(m.group(1)).strip()
                if title:
                    out.append({"source": "BingNews", "title": title, "points": 0, "url": ""})
    except Exception as e:
        out.append({"source": "error", "title": f"bing failed: {e}", "points": 0, "url": ""})
    return out


@safe
def github_trending(limit: int = 8) -> list:
    out = []
    try:
        d = fetch_json("https://api.github.com/search/repositories?q=created:>%s&sort=stars&order=desc&per_page=15"
                       % (datetime.date.today() - datetime.timedelta(days=14)).isoformat())
        for repo in d.get("items", [])[:limit]:
            name = repo.get("full_name") or ""
            desc = (repo.get("description") or "")[:100]
            out.append({"source": "GitHub", "title": f"{name} - {desc}".strip(),
                        "points": repo.get("stargazers_count") or 0,
                        "url": repo.get("html_url") or ""})
    except Exception as e:
        out.append({"source": "error", "title": f"github failed: {e}", "points": 0, "url": ""})
    return out


def is_techy(title: str) -> bool:
    kw = ("ai", "agent", "llm", "gpt", "robot", "code", "app", "startup", "cloud",
          "tech", "software", "data", "model", "openai", "google", "microsoft",
          "apple", "nvidia", "chip", "computer", "phone", "web", "saas", "api",
          "crypto", "bitcoin", "automation", "workforce", "ads", "marketing", "sales")
    t = title.lower()
    return any(k in t for k in kw)


def rank(items: list) -> list:
    """Score: points (log-scaled) + recency-ish + techy boost. Sort desc."""
    scored = []
    for it in items:
        if not it.get("title"):
            continue
        pts = float(it.get("points") or 0)
        score = (1.0 if pts <= 0 else 1.0 + min(2.5, (pts ** 0.4) / 6.0))
        if is_techy(it["title"]):
            score *= 1.6
        if it["source"] == "BingNews":
            score *= 1.3
        scored.append({**it, "score": round(score, 2)})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def main():
    OUT.mkdir(exist_ok=True)
    all_items = hn_top() + reddit_top() + bing_news_top() + github_trending()
    ranked = rank(all_items)
    today = datetime.date.today().isoformat()

    data = {
        "date": today,
        "top": ranked[:15],
        "count": len(ranked),
    }
    (OUT / "latest.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT / f"{today}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[Research] {len(ranked)} items ranked; top 5:")
    for it in ranked[:5]:
        print(f"  [{it['source']} {it['score']}] {it['title'][:80]}")


if __name__ == "__main__":
    main()
