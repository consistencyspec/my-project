#!/usr/bin/env python3
"""
eBay 輸出の利益計算

使い方
  1) 1件だけ計算する(対話式)
       python3 profit.py
  2) CSV でまとめて計算する
       python3 profit.py items.csv
     → output/profit_日時.csv に結果が出ます。

CSV の列(1行目は見出し。items_sample.csv を参考に)
  name            商品名(メモ)
  buy_jpy         仕入れ値(円)
  sell_usd        eBayの販売価格(ドル)
  ship_usd        バイヤーからもらう送料(ドル。送料無料なら0)
  ship_cost_jpy   実際の発送費(円。空欄なら config の DEFAULT_SHIPPING_COST_JPY)
  to_us           アメリカ向けなら1(関税を計算)、それ以外は0。空欄なら1
"""
import csv
import math
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import config

HERE = Path(__file__).resolve().parent


def fee_rate():
    """売上(商品代+送料)にかかる割合の合計"""
    return (config.FINAL_VALUE_FEE_RATE + config.INTERNATIONAL_FEE_RATE
            + config.PROMOTED_AD_RATE + config.PAYOUT_FX_COST_RATE)


@dataclass
class Result:
    revenue_jpy: int      # 売上(商品代+送料)を円にしたもの
    fees_jpy: int         # eBay手数料+為替コスト
    tariff_jpy: int       # 関税(DDP)
    ship_cost_jpy: int    # 発送費+梱包+国内送料
    buy_jpy: int
    profit_jpy: int
    margin: float         # 利益 ÷ 売上

    @property
    def ok(self):
        return self.profit_jpy >= config.MIN_PROFIT_JPY and self.margin >= config.MIN_MARGIN


def calc(buy_jpy, sell_usd, ship_usd=0.0, ship_cost_jpy=None, to_us=True):
    r = config.USD_JPY
    if ship_cost_jpy is None:
        ship_cost_jpy = config.DEFAULT_SHIPPING_COST_JPY
    gross_usd = sell_usd + ship_usd
    revenue = gross_usd * r
    fees = revenue * fee_rate() + config.PER_ORDER_FEE_USD * r
    tariff = 0.0
    if to_us and config.US_DDP:
        tariff = sell_usd * r * config.US_TARIFF_RATE + config.US_DDP_FEE_JPY
    costs = ship_cost_jpy + config.PACKING_COST_JPY + config.DOMESTIC_SHIPPING_JPY
    profit = revenue - fees - tariff - costs - buy_jpy
    return Result(round(revenue), round(fees), round(tariff), round(costs), round(buy_jpy),
                  math.floor(profit), round(profit / revenue, 3) if revenue else 0.0)


def max_buy_price(sell_usd, ship_usd=0.0, ship_cost_jpy=None, to_us=True):
    """この価格以下で仕入れれば、目標の利益(MIN_PROFIT_JPY と MIN_MARGIN の両方)を満たす"""
    base = calc(0, sell_usd, ship_usd, ship_cost_jpy, to_us)
    target = max(config.MIN_PROFIT_JPY, config.MIN_MARGIN * base.revenue_jpy)
    return max(0, math.floor((base.profit_jpy - target) / 10) * 10)


def min_sell_price(buy_jpy, ship_usd=0.0, ship_cost_jpy=None, to_us=True):
    """この価格(ドル)以上で売れば、目標の利益を満たす"""
    lo, hi = 0.0, 100000.0
    for _ in range(60):  # 二分探索
        mid = (lo + hi) / 2
        if calc(buy_jpy, mid, ship_usd, ship_cost_jpy, to_us).ok:
            hi = mid
        else:
            lo = mid
    return math.ceil(hi * 100) / 100


def _num(v, default=None, cast=float):
    v = (v or "").strip().replace(",", "").replace("¥", "").replace("$", "")
    return cast(float(v)) if v else default


def run_csv(path):
    rows = list(csv.DictReader(Path(path).open(encoding="utf-8-sig")))
    out_dir = HERE / "output"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"profit_{datetime.now():%Y%m%d_%H%M}.csv"
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["判定", "商品名", "仕入れ値", "販売価格USD", "送料USD", "売上(円)", "手数料", "関税",
                    "発送・梱包", "利益", "利益率", "仕入れ上限(円)", "最低販売価格USD"])
        for row in rows:
            buy = _num(row.get("buy_jpy"), 0, int)
            sell = _num(row.get("sell_usd"), 0.0)
            ship = _num(row.get("ship_usd"), 0.0)
            cost = _num(row.get("ship_cost_jpy"), None, int)
            to_us = _num(row.get("to_us"), 1, int) == 1
            res = calc(buy, sell, ship, cost, to_us)
            w.writerow(["OK" if res.ok else "", row.get("name", ""), buy, sell, ship, res.revenue_jpy,
                        res.fees_jpy, res.tariff_jpy, res.ship_cost_jpy, res.profit_jpy,
                        f"{res.margin:.0%}", max_buy_price(sell, ship, cost, to_us),
                        min_sell_price(buy, ship, cost, to_us)])
            print(f"{'OK ' if res.ok else '   '}利益 ¥{res.profit_jpy:>7,} ({res.margin:.0%})  {row.get('name', '')}")
    print(f"\n結果: {out}")


def interactive():
    print(f"eBay 利益計算(1ドル={config.USD_JPY}円で計算。設定は config.py)\n")
    buy = _num(input("仕入れ値(円): "), 0, int)
    sell = _num(input("eBayの販売価格(ドル): "), 0.0)
    ship = _num(input("バイヤーからもらう送料(ドル、無料なら0): "), 0.0)
    cost = _num(input(f"実際の発送費(円、空欄で{config.DEFAULT_SHIPPING_COST_JPY}): "), None, int)
    to_us = (input("アメリカ向けですか? (y/n、空欄でy): ").strip().lower() or "y") == "y"
    r = calc(buy, sell, ship, cost, to_us)
    print(f"""
  売上(商品代+送料)  ¥{r.revenue_jpy:,}
  eBay手数料・為替   −¥{r.fees_jpy:,}
  関税(DDP)          −¥{r.tariff_jpy:,}
  発送・梱包         −¥{r.ship_cost_jpy:,}
  仕入れ値           −¥{r.buy_jpy:,}
  ─────────────────
  利益               ¥{r.profit_jpy:,}(利益率 {r.margin:.0%}){'  ✓目標達成' if r.ok else ''}

  この販売価格なら、仕入れは ¥{max_buy_price(sell, ship, cost, to_us):,} 以下に
  この仕入れ値なら、販売価格は ${min_sell_price(buy, ship, cost, to_us):,.2f} 以上に""")


if __name__ == "__main__":
    run_csv(sys.argv[1]) if len(sys.argv) > 1 else interactive()
