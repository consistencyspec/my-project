"""予算ごとの「使い切る組み合わせ」を作る部品(APIには接続しません)。

ジャンルごとに単位(kg・ロールなど)が違い、量どうしは足せないので、
「決めた順番のジャンルから、残りの予算で買える中でいちばん量が多いもの」を選んでいく、分かりやすい方法にしています。
"""


def best_within(gifts, limit, used):
    """寄付額が limit 以下で、1万円あたりの量がいちばん多い返礼品(なければ None)。"""
    pool = [g for g in gifts if g.price_min <= limit and g.code not in used]
    return max(pool, key=lambda g: (g.per10k, -g.price_min)) if pool else None


def make_plan(ranked_by_genre, genres, budget, min_use=0.8):
    """genres の順に1つずつ選び、余った予算で同じジャンルたちからさらに追加する。

    戻り値: [(slug, gift), ...] と合計寄付額。2品未満か、予算の min_use 割未満しか使えないときは ([], 0)。
    """
    genres = [s for s in genres if ranked_by_genre.get(s)]
    picks, used, left = [], set(), budget
    for slug in genres:
        g = best_within(ranked_by_genre[slug], left, used)
        if g:
            picks.append((slug, g))
            used.add(g.code)
            left -= g.price_min
    while True:  # 余りで、まだ選べるものを追加(量が多い順)
        options = [(slug, best_within(ranked_by_genre[slug], left, used)) for slug in genres]
        options = [(s, g) for s, g in options if g]
        if not options:
            break
        slug, g = max(options, key=lambda sg: sg[1].per10k / max(1, _typical(ranked_by_genre[sg[0]])))
        picks.append((slug, g))
        used.add(g.code)
        left -= g.price_min
    total = budget - left
    if len(picks) < 2 or total < budget * min_use:
        return [], 0
    return picks, total


def _typical(gifts):
    """ジャンルの「ふつうの量」(中央値)。ジャンルどうしで、どれだけお得かを比べるために使う。"""
    v = sorted(g.per10k for g in gifts)
    return v[len(v) // 2] if v else 1
