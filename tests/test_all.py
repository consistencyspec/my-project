"""動作確認用のテスト(実行: python3 -m unittest discover -s tests -v)。楽天APIには接続しません。"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tracking"))

import generate_drafts as gd  # noqa: E402
import post_templates as pt  # noqa: E402
import rakuten_client as rc  # noqa: E402
import tracklib as tl  # noqa: E402

DEMO = json.loads((ROOT / "scripts" / "sample_items.json").read_text(encoding="utf-8"))


class TemplateTests(unittest.TestCase):
    def setUp(self):
        self.items = rc.parse_items(DEMO)

    def test_all_types_fit_limit_and_pr(self):
        for type_id in pt.TYPES:
            n = pt.ITEM_COUNT[type_id]
            main, reply = pt.build(type_id, self.items[:n], date(2026, 10, 5), "テスト")
            self.assertLessEqual(pt.estimated_length(main), 500, type_id)
            self.assertLessEqual(pt.estimated_length(reply), 500, type_id)
            if type_id not in (10, 11, 12):
                self.assertTrue(main.startswith("【PR】"), type_id)
                self.assertIn("【PR】", reply.split("\n")[0])

    def test_long_item_name_is_shortened(self):
        long_item = rc.Item("c", "あ" * 200, 1000, "u", "a", "s", 4.5, 10)
        main, _ = pt.build(2, [long_item] * 3, date(2026, 10, 7))
        self.assertLessEqual(pt.estimated_length(main), 500)


class ClientTests(unittest.TestCase):
    def test_parse_both_formats(self):
        v1 = {"Items": [{"Item": {"itemName": "A", "itemPrice": "100", "itemCode": "x"}}]}
        v2 = {"Items": [{"itemName": "A", "itemPrice": 100, "itemCode": "x"}]}
        self.assertEqual(rc.parse_items(v1)[0].price, 100)
        self.assertEqual(rc.parse_items(v2)[0].name, "A")

    def test_missing_env_reported_without_values(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(len(rc.get_settings()["missing"]), 3)

    def test_placeholder_env_treated_as_missing(self):
        env = {"RAKUTEN_APPLICATION_ID": "ここにアプリケーションID", "RAKUTEN_ACCESS_KEY": "pk_real", "RAKUTEN_AFFILIATE_ID": "abc"}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(rc.get_settings()["missing"], ["RAKUTEN_APPLICATION_ID"])

    def test_select_filters(self):
        items = rc.parse_items(DEMO) + [rc.Item("u", "中古 品", 1, "", "", "", 5, 100), rc.Item("l", "良品", 1, "", "", "", 3.0, 100)]
        got = rc.select_items(items, 20, exclude_codes={"demo-shop:0001"})
        names = [i.item_code for i in got]
        self.assertNotIn("demo-shop:0001", names)
        self.assertNotIn("u", names)
        self.assertNotIn("l", names)

    def test_source_has_no_secrets(self):
        for p in list((ROOT / "scripts").glob("*.py")) + [ROOT / ".env.example"]:
            text = p.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"pk_[A-Za-z0-9]{10,}")
            self.assertNotRegex(text, r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


class KpiTests(unittest.TestCase):
    def test_followers_and_impressions_against_milestones(self):
        import summarize as sm
        cfg = {"kpi_milestones": {"2026-11": {"followers": 400, "avg_impressions": 800}}}
        followers = [{"date": "2026-10-31", "followers": "180"}, {"date": "2026-11-07", "followers": "200"},
                     {"date": "2026-11-21", "followers": "999"}]  # 基準日より後の記録は使わない
        posts = [{"status": "posted", "ad": "1", "posted_date": "2026-11-02", "impressions": "600"},
                 {"status": "posted", "ad": "1", "posted_date": "2026-11-04", "impressions": "1,000"},
                 {"status": "posted", "ad": "0", "posted_date": "2026-11-05", "impressions": "5000"},  # 広告なしは除外
                 {"status": "posted", "ad": "1", "posted_date": "2026-11-06", "impressions": ""}]  # 未記入は除外
        text = "\n".join(sm.kpi_section(posts, followers, cfg, date(2026, 11, 14)))
        self.assertIn("**200人**", text)
        self.assertIn("50%", text)
        self.assertIn("+20人", text)
        self.assertIn("**800回**", text)
        self.assertIn("100%", text)

    def test_missing_kpi_data_is_explained(self):
        import summarize as sm
        text = "\n".join(sm.kpi_section([], [], {}, date(2026, 11, 14)))
        self.assertIn("followers.csv", text)
        self.assertIn("impressions", text)


class PipelineTests(unittest.TestCase):
    def run_py(self, *args, env=None):
        e = {**os.environ, "RAKUTEN_APPLICATION_ID": "", "RAKUTEN_ACCESS_KEY": "", "RAKUTEN_AFFILIATE_ID": ""}
        e.update(env or {})
        return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, env=e, cwd=ROOT)

    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            posts, sales = tmp / "posts.csv", tmp / "sales.csv"
            tl.write_csv(posts, tl.POST_COLUMNS, [])
            tl.write_csv(sales, tl.SALES_COLUMNS, [])
            # 下書き(APIはモックして呼ぶ)
            demo = rc.parse_items(DEMO)
            with mock.patch.object(rc, "search_items", return_value=demo), \
                 mock.patch.object(rc, "get_settings", return_value={"missing": []}), \
                 mock.patch.object(sys, "argv", ["x", "--start", "2026-10-05", "--days", "7", "--posts", str(posts),
                                                 "--out-dir", str(tmp)]):
                gd.main()
            rows = tl.read_csv(posts)
            self.assertEqual([r["planned_date"] for r in rows], [f"2026-10-{d:02d}" for d in range(5, 12)])  # 毎日投稿
            self.assertEqual(len({r["item_code"] for r in rows if r["item_code"]}), 3)  # 重複商品なし
            self.assertTrue((tmp / "drafts_2026-10-05.md").exists())
            # 再実行しても二重登録されない
            with mock.patch.object(rc, "search_items", return_value=demo), \
                 mock.patch.object(rc, "get_settings", return_value={"missing": []}), \
                 mock.patch.object(sys, "argv", ["x", "--start", "2026-10-05", "--days", "7", "--posts", str(posts),
                                                 "--out-dir", str(tmp)]):
                gd.main()
            self.assertEqual(len(tl.read_csv(posts)), 7)
            # 投稿済みにして楽天CSVを取り込む
            rows = tl.read_csv(posts)
            for r in rows:
                if r["ad"] == "1":
                    r["status"], r["posted_date"] = "posted", r["planned_date"]
            tl.write_csv(posts, tl.POST_COLUMNS, rows)
            first_item_name = rows[0]["item_name"].split(" | ")[0]
            report = tmp / "r.csv"
            report.write_text(f"日付,商品名,クリック数,注文件数,売上金額\n2026/10/06,{first_item_name} 追加文字,12,2,\"21,500\"\n"
                              "2026/10/08,存在しない商品,3,1,\"3,000\"\n合計,,15,3,\"24,500\"\n", encoding="cp932")
            res = self.run_py(ROOT / "tracking" / "import_report.py", report, "--posts", posts, "--sales", sales)
            self.assertEqual(res.returncode, 0, res.stderr)
            res = self.run_py(ROOT / "tracking" / "import_report.py", report, "--posts", posts, "--sales", sales)  # 二重取り込み
            sales_rows = tl.read_csv(sales)
            self.assertEqual(sum(tl.to_int(r["sales_yen"]) for r in sales_rows), 24500)
            attributed = [r for r in tl.read_csv(posts) if tl.to_int(r["sales_yen"])]
            self.assertEqual(sum(tl.to_int(r["sales_yen"]) for r in attributed), 21500)
            # 集計
            res = self.run_py(ROOT / "tracking" / "summarize.py", "--today", "2026-10-10", "--posts", posts,
                              "--sales", sales, "--no-save")
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn("24,500円", res.stdout)
            self.assertIn("目標の", res.stdout)

    def test_demo_mode_runs_without_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            res = self.run_py(ROOT / "scripts" / "generate_drafts.py", "--demo", "--start", "2026-10-02", "--days", "7",
                              "--out-dir", tmp)
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertTrue(list(Path(tmp).glob("drafts_*_demo.md")))

    def test_real_mode_without_ids_stops(self):
        res = self.run_py(ROOT / "scripts" / "generate_drafts.py", "--start", "2026-10-02", env={"HOME": "/nonexistent"})
        # .env が無い環境では、ID未設定で止まる(.env があるマシンでは成功することもあるため returncode のみ緩く確認)
        if not (ROOT / ".env").exists():
            self.assertNotEqual(res.returncode, 0)


if __name__ == "__main__":
    unittest.main()
