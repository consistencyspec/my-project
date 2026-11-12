"""動作確認用のテスト（実行: python3 -m unittest discover -s tests -v）。音声合成と動画の書き出しはしません。"""
import json
import sys
import tempfile
import unittest
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_video as bv  # noqa: E402

EPISODES = sorted((ROOT / "content").glob("*.json"))


class ContentTests(unittest.TestCase):
    def test_all_episodes_are_valid(self):
        self.assertGreaterEqual(len(EPISODES), 3)
        for path in EPISODES:
            with self.subTest(path=path.name):
                ep = bv.load_episode(path)
                self.assertGreaterEqual(len(ep["lines"]), 12)
                self.assertGreaterEqual(len(ep["phrases"]), 5)
                voices = {info["voice"] for info in ep["speakers"].values()}
                self.assertEqual(voices, {"F", "M"}, "男女1人ずつにする")

    def test_validation_catches_unknown_speaker(self):
        ep = json.loads(EPISODES[0].read_text(encoding="utf-8"))
        ep["lines"][0]["speaker"] = "Nadie"
        with self.assertRaises(ValueError):
            bv.validate_episode(ep)


class LayoutTests(unittest.TestCase):
    def test_wrap_fits_width(self):
        f = bv.font(bv.FONT_ES, 70)
        text = "Por ahora no, pero si decide alquilarlo, necesitaremos su contrato de trabajo."
        lines = bv.wrap(text, f, 1000)
        self.assertGreater(len(lines), 1)
        self.assertEqual(" ".join(lines), text)
        for ln in lines:
            self.assertLessEqual(f.getlength(ln), 1000)

    def test_wrap_japanese_by_char(self):
        f = bv.font(bv.FONT_JA, 50)
        text = "今のところは不要です。ただ、借りると決めた場合は、雇用契約書が必要になります。"
        lines = bv.wrap(text, f, 600, by_char=True)
        self.assertEqual("".join(lines), text)

    def test_slides_render(self):
        ep = bv.load_episode(EPISODES[0])
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            bv.slide_title(ep, p / "t.png")
            bv.slide_line(ep, "test", ep["lines"][0], 1, 18, p / "l.png", tag="ふつう")
            bv.slide_phrase(ep, ep["phrases"][0], 1, 7, p / "p.png")
            bv.make_thumbnail(ep, p / "th.png")
            for name in ("t.png", "l.png", "p.png", "th.png"):
                self.assertTrue((p / name).stat().st_size > 1000)


class TimelineTests(unittest.TestCase):
    def _wav(self, path, seconds, rate=22050):
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(b"\x00\x00" * int(seconds * rate))

    def test_video_matches_audio_length(self):
        with tempfile.TemporaryDirectory() as d:
            wav = Path(d) / "a.wav"
            self._wav(wav, 1.234)
            tl = bv.Timeline(22050)
            for _ in range(200):  # 細かい端数が積み重なってもずれないこと
                tl.add("x.png", [wav, 0.37])
            video_total = sum(dur for _, dur in tl.video_durations())
            self.assertAlmostEqual(video_total, tl.now, delta=1 / bv.FPS)
            out = Path(d) / "all.wav"
            tl.write_audio(out)
            self.assertAlmostEqual(bv.wav_seconds(out), tl.now, places=3)

    def test_description_has_chapters_from_zero(self):
        ep = bv.load_episode(EPISODES[0])
        tl = bv.Timeline(22050)
        tl.chapter("はじめに")
        tl.add("x.png", [5.0])
        tl.chapter("1回目")
        text = bv.description(ep, tl)
        self.assertIn("0:00 はじめに", text)  # YouTube のチャプターは 0:00 から始める必要がある
        self.assertIn("CC BY 3.0", text)


if __name__ == "__main__":
    unittest.main()
