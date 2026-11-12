"""解説（自分の声の録音）を差し込む仕組みの確認。実行: python3 -m unittest discover -s tests -v"""
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_video as bv  # noqa: E402
import commentary as cm  # noqa: E402

EP = sorted((ROOT / "content").glob("*.json"))[0]


def tone(path, seconds, lead=0.0, tail=0.0):
    """テスト用の「録音」：前後に無音のついた音（スマホのボイスメモと同じ m4a で作る）。"""
    cmd = ["ffmpeg", "-loglevel", "error", "-y",
           "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={max(lead, 0.01)}",
           "-f", "lavfi", "-i", f"sine=frequency=300:sample_rate=44100:duration={seconds}",
           "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={max(tail, 0.01)}",
           "-filter_complex", "[1]aformat=channel_layouts=stereo[s];[0][s][2]concat=n=3:v=0:a=1",
           "-c:a", "aac", str(path)]
    subprocess.run(cmd, check=True)


class ValidateTests(unittest.TestCase):
    def test_needs_audio(self):
        with self.assertRaises(ValueError):
            cm.validate({"slides": []})

    def test_bad_position(self):
        with self.assertRaises(ValueError):
            cm.validate({"audio": "a.m4a", "after": "nowhere"})

    def test_times_must_increase(self):
        with self.assertRaises(ValueError):
            cm.validate({"audio": "a.m4a", "slides": [{"at": 10, "title": "a"}, {"at": 5, "title": "b"}]})

    def test_all_or_none_times(self):
        with self.assertRaises(ValueError):
            cm.validate({"audio": "a.m4a", "slides": [{"at": 0, "title": "a"}, {"title": "b"}]})


class TimingTests(unittest.TestCase):
    def test_even_split_without_times(self):
        self.assertEqual(cm.slide_times([{"title": "a"}, {"title": "b"}], 60), [0.0, 30.0])

    def test_first_slide_starts_at_zero(self):
        self.assertEqual(cm.slide_times([{"at": 3, "title": "a"}, {"at": 20, "title": "b"}], 60), [0.0, 20.0])

    def test_times_after_end_are_dropped(self):
        self.assertEqual(cm.slide_times([{"at": 0, "title": "a"}, {"at": 90, "title": "b"}], 60), [0.0])


class AudioTests(unittest.TestCase):
    def test_prepare_and_split(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            src = d / "memo.m4a"
            tone(src, 6, lead=1.0, tail=3.0)
            out = cm.prepare_audio(src, d / "talk.wav", 22050)
            with wave.open(str(out), "rb") as w:
                self.assertEqual((w.getnchannels(), w.getsampwidth(), w.getframerate()), (1, 2, 22050))
            total = cm.wav_seconds(out)
            self.assertAlmostEqual(total, 7.0, delta=0.4)  # 頭の1秒は残し、最後の3秒の無音は切る
            parts = cm.split_wav(out, [0.0, 4.0], d)
            self.assertEqual(len(parts), 2)
            self.assertAlmostEqual(sum(cm.wav_seconds(p) for p in parts), total, places=3)
            self.assertAlmostEqual(cm.wav_seconds(parts[0]), 4.0, places=2)


class IntegrationTests(unittest.TestCase):
    def test_sections_insert_after_given_key(self):
        ep = bv.load_episode(EP)
        ep["commentary"] = {"audio": "x.m4a", "after": "phrases"}
        keys = [k for k, _, _ in bv.sections_for(ep, True)]
        self.assertEqual(keys[keys.index("phrases") + 1], "commentary")
        self.assertNotIn("commentary", [k for k, _, _ in bv.sections_for(ep, False)])

    def test_missing_file_is_skipped_with_warning(self):
        self.assertIsNone(cm.find_audio({"audio": "commentary/does_not_exist.m4a"}, ROOT))

    def test_slide_and_script(self):
        ep = bv.load_episode(EP)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.png"
            bv.slide_commentary(ep, {"title": "例文で確認", "points": ["説明", {"es": "Hola.", "ja": "こんにちは"}]}, 1, 2, p)
            self.assertGreater(p.stat().st_size, 1000)
            bv.slide_title(ep, Path(d) / "t.png", bv.sections_for(ep | {"commentary": {"audio": "x"}}, True))
        text = cm.script_template(ep)
        self.assertIn(ep["grammar"], text)
        self.assertIn('"commentary"', text)


if __name__ == "__main__":
    unittest.main()
