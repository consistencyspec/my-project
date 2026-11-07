"""ニュース(記事)の部品のテスト。"""
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "sites" / "common"))

import news  # noqa: E402

SAMPLE = """---
title: テストの記事
date: 2026-11-07
summary: 説明
kind: auto
---
本文の**太字**です。

## 見出し

| 商品 | 値段 |
|---|---|
| [ある商品](item:shop:1) | 100円 |
| [なくなった商品](item:shop:2) | 200円 |

- [ランキング](/kome/)
"""


class NewsTests(unittest.TestCase):
    def test_load_and_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "2026-11-07-test.md").write_text(SAMPLE, encoding="utf-8")
            Path(tmp, "2026-12-01-future.md").write_text(SAMPLE.replace("2026-11-07", "2026-12-01"), encoding="utf-8")
            Path(tmp, "memo.md").write_text("ファイル名の形が違うものは読まない", encoding="utf-8")
            arts = news.load_articles(tmp, today=date(2026, 11, 7))
        self.assertEqual([a.slug for a in arts], ["2026-11-07-test"])   # 未来の日付の記事は出さない
        a = arts[0]
        self.assertEqual(a.kind, "auto")
        html = news.render_markdown(a.body_md, resolve=lambda code: "https://hb.afl.rakuten.co.jp/x" if code == "shop:1" else None)
        self.assertIn("<strong>太字</strong>", html)
        self.assertIn("<h2>見出し</h2>", html)
        self.assertIn('<a href="https://hb.afl.rakuten.co.jp/x" rel="nofollow sponsored noopener" target="_blank">ある商品</a>', html)
        self.assertIn("<td>なくなった商品</td>", html)                  # 販売が終わった商品はリンクなし
        self.assertIn('<a href="/kome/">ランキング</a>', html)
        page = news.article_html(a, "ch1", resolve=lambda c: None)
        self.assertIn("広告リンク(PR)", page)                          # 商品の印があれば PR の表示

    def test_escape(self):
        self.assertNotIn("<script>", news.render_markdown("<script>alert(1)</script>"))


if __name__ == "__main__":
    unittest.main()
