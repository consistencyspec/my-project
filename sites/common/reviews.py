"""楽天のレビュー件数・評価から、目印(バッジ)を作る部品(2つのサイトで共通)。

楽天APIの「件数」と「平均」だけを使います。レビューの文章を作ったり、集めたりはしません。
"""


def review_badges(count, average):
    """件数と平均から、表示する目印の文字のリストを返す(多いもの順)。"""
    badges = []
    if count >= 1000:
        badges.append("レビュー1,000件以上")
    elif count >= 100:
        badges.append("レビュー100件以上")
    if average >= 4.5 and count >= 10:
        badges.append("★4.5以上")
    return badges


def review_html(count, average, chip_class="chip"):
    """「★4.8 レビュー112件」と目印のHTML。レビューがなければ「レビューなし」。"""
    if not count:
        return '<p class="rv">レビューなし</p>'
    chips = "".join(f'<span class="{chip_class}">{b}</span>' for b in review_badges(count, average))
    chips = f'<span class="chips">{chips}</span>' if chips else ""
    return f'<p class="rv"><span class="rv-s">★{average:.1f}</span> レビュー<b>{count:,}</b>件{chips}</p>'
