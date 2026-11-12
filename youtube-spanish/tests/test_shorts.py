"""ショート動画の動作確認（実行: python3 -m unittest discover -s tests -v）。音声合成と動画の書き出しはしません。"""
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_short as bs  # noqa: E402

SHORTS = sorted((ROOT / "content" / "shorts").glob("*.json"))


class ShortTests(unittest.TestCase):
    def test_all_shorts_are_valid(self):
        self.assertGreaterEqual(len(SHORTS), 6)
        ids = set()
        for path in SHORTS:
            with self.subTest(path=path.name):
                s = bs.load_short(path)
                self.assertNotIn(s["id"], ids)
                ids.add(s["id"])

    def test_bad_voice_is_rejected(self):
        s = bs.load_short(SHORTS[0])
        s["example"][0]["voice"] = "X"
        with self.assertRaises(ValueError):
            bs.validate_short(s)

    def test_slides_render_in_portrait(self):
        for path in SHORTS:
            s = bs.load_short(path)
            with self.subTest(path=path.name), tempfile.TemporaryDirectory() as d:
                d = Path(d)
                bs.slide_hook(s, d / "h.png")
                if s.get("literal"):
                    bs.slide_literal(s, d / "l.png")
                bs.slide_answer(s, d / "a.png", "ふつうの速さ")
                for i in range(len(s["example"])):
                    bs.slide_example(s, d / f"e{i}.png", i)
                bs.slide_end(s, d / "z.png")
                for p in d.glob("*.png"):
                    self.assertEqual(Image.open(p).size, (bs.SW, bs.SH))

    def test_content_stays_above_youtube_buttons(self):
        """どの画面も、下のボタンで隠れる範囲に文字がはみ出さないこと。"""
        for path in SHORTS:
            s = bs.load_short(path)
            with self.subTest(path=path.name), tempfile.TemporaryDirectory() as d:
                p = Path(d) / "a.png"
                bs.slide_answer(s, p, "ゆっくり")
                img = Image.open(p).convert("RGB")
                below = img.crop((0, bs.SAFE_BOTTOM, bs.SW, bs.SH))
                self.assertEqual(below.getcolors(1 << 16), [(below.width * below.height, bs.BG)])

    def test_description(self):
        s = bs.load_short(SHORTS[0])
        text = bs.description(s)
        self.assertIn("#shorts", text)
        self.assertIn(s["answer"]["es"], text)
        self.assertIn("CC BY 3.0", text)


if __name__ == "__main__":
    unittest.main()
