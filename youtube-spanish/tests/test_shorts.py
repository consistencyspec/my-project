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

    def test_narration_lines(self):
        hook, end = bs.narration_lines({"word": "草（www）"})
        self.assertEqual(hook, "「草」って、スペイン語でなんて言うと思いますか？")  # かっこ書きは読まない
        self.assertEqual(end, "")
        for path in SHORTS:
            s = bs.load_short(path)
            hook, end = bs.narration_lines(s)
            self.assertTrue(hook and end, path.name)
            self.assertNotRegex(hook + end, "[¡¿áéíóúñ]", "日本語の声にスペイン語を読ませない")

    def test_bad_narration_key(self):
        s = bs.load_short(SHORTS[0])
        s["narration"] = {"middle": "x"}
        with self.assertRaises(ValueError):
            bs.validate_short(s)

    def test_character_sits_above_buttons_and_text_above_character(self):
        self.assertLessEqual(bs.CHAR_Y + bs.CHAR_H, bs.SAFE_BOTTOM)
        self.assertLess(bs.content_bottom(), bs.CHAR_Y)
        s = bs.load_short(SHORTS[0])
        with tempfile.TemporaryDirectory() as d:
            base = Path(d) / "a.png"
            bs.slide_answer(s, base, "ふつうの速さ")
            img = Image.open(base).convert("RGB")
            # 文字はキャラクターの場所に入っていない（背景色のまま）
            area = img.crop((0, bs.CHAR_Y, bs.SW, bs.SH))
            self.assertEqual(area.getcolors(1 << 16), [(area.width * area.height, bs.BG)])
            out = bs.with_character(base, "kimegao", {})
            self.assertNotEqual(Image.open(out).convert("RGB").getpixel((bs.SW // 2, bs.CHAR_Y + bs.CHAR_H // 2)), bs.BG)

    def test_mouth_track_ends_closed(self):
        import character as ch
        import math, struct, wave
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "v.wav"
            with wave.open(str(p), "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(22050)
                w.writeframes(b"".join(struct.pack("<h", int(8000 * math.sin(i / 7) * (1 + math.sin(i / 3000)) / 2))
                                       for i in range(22050)))
            track, sec = ch.mouth_track(p)
            self.assertEqual(track[-1], "n")
            self.assertGreater(len(set(track)), 2)
            self.assertEqual(sum(c for _, c in ch.runs(track)), len(track))

    def test_description(self):
        s = bs.load_short(SHORTS[0])
        text = bs.description(s)
        self.assertIn("#shorts", text)
        self.assertIn(s["answer"]["es"], text)
        self.assertIn("CC BY 3.0", text)


if __name__ == "__main__":
    unittest.main()
