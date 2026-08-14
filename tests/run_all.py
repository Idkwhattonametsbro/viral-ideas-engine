#!/usr/bin/env python3
"""Smoke tests for the Viral Ideas Engine."""
import json
import sys
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "content-engine"))


class TestResearch(unittest.TestCase):
    def test_01_research_runs_and_ranks(self):
        import research
        items = research.hn_top(5) + research.reddit_top(2) + research.bing_news_top(3) + research.github_trending(2)
        self.assertTrue(len(items) > 0)
        ranked = research.rank(items)
        scores = [r["score"] for r in ranked]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_02_titles_nonempty(self):
        import research
        items = research.hn_top(5)
        for it in items:
            self.assertTrue(it.get("title"))


class TestGenerate(unittest.TestCase):
    def setUp(self):
        import generate
        self.gen = generate
        self._orig = self.gen.FEED
        self.tmp = Path(tempfile.mkdtemp(prefix="nexviral_"))
        self.gen.FEED = self.tmp

    def tearDown(self):
        self.gen.FEED = self._orig
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_03_formats_render(self):
        import random
        rng = random.Random(7)
        for fmt in self.gen.FORMATS:
            s = self.gen.render_pattern(fmt, rng, "AI agents", "the platform", "ALPHA")
            self.assertGreater(len(s), 60, fmt["id"])
            self.assertNotIn("{", s.replace("{[", ""), f"unfilled template: {fmt['id']}")

    def test_04_script_chunks_short(self):
        s = "This is a sentence that is intentionally quite long and should be split into shorter chunks for voiceover purposes."
        chunks = self.gen.script_to_chunks(s)
        for c in chunks:
            self.assertLessEqual(len(c), 95)

    def test_05_pack_has_all_fields(self):
        import random, generate
        rng = random.Random(3)
        fmt = generate.pick_format(rng, "AI")
        script = generate.render_pattern(fmt, rng, "AI agents", "the platform", "ALPHA")
        self.assertTrue(script.strip())
        title = generate.title_for(fmt["id"], "AI agents", "the platform", rng)
        self.assertLessEqual(len(title), 80)
        tags = generate.hashtags_for("AI agents", rng)
        self.assertLessEqual(len(tags), 4)
        self.assertTrue(all(t.startswith("#") for t in tags))

    def test_06_no_banned_slop(self):
        import random, generate
        rng = random.Random(11)
        for fmt in generate.FORMATS:
            if fmt["id"] == "reframe":
                continue  # intentionally quotes the bad words ("don't say game-changer")
            s = generate.render_pattern(fmt, rng, "AI agents", "the platform", "ALPHA").lower()
            for bad in ("in today's fast-paced world", "game-changer", "delve", "supercharge"):
                self.assertNotIn(bad, s)


class TestVoiceover(unittest.TestCase):
    def test_07_srt_format(self):
        import generate
        lines = ["00:00:00,000 --> 00:00:02,500", "hello world", ""]
        self.assertEqual(generate.fmt_srt(0.0), "00:00:00,000")
        self.assertEqual(generate.fmt_srt(2.5), "00:00:02,500")


class TestWorkflow(unittest.TestCase):
    def test_08_workflow_references_engine(self):
        wf = (ROOT / ".github" / "workflows" / "daily.yml").read_text(encoding="utf-8")
        self.assertIn("research.py", wf)
        self.assertIn("generate.py", wf)
        self.assertIn("0 3,15 * * *", wf)

    def test_09_dashboard_references_feed(self):
        dash = (ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")
        self.assertIn("latest.json", dash)
        self.assertIn("voiceover_latest.mp3", dash)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    res = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f"\n=== {res.testsRun} tests, {len(res.failures)} failures, {len(res.errors)} errors ===")
    sys.exit(0 if res.wasSuccessful() else 1)
