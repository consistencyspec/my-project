"""投稿の型ごとの文章テンプレート。

・《 》で囲まれた部分は「あなた自身の言葉に置き換える場所」です。
  置き換えずに投稿しないよう、下書きファイルで警告が出ます。
・広告(アフィリエイトリンク)を含む投稿は、必ず先頭に【PR】を入れます。
・Threads は1投稿500文字以内。本文とリプライ(リンク用)に分けて作ります。
"""
import re

LIMIT = 500
PLACEHOLDER = re.compile(r"《[^》]*》")
PLACEHOLDER_ESTIMATE = 40  # 置き換え後の文字数の見積もり(1か所あたり)

TYPES = {
    1: "悩み解決型", 2: "比較型", 3: "レビュー型", 4: "ランキング型", 5: "セール・イベント型",
    6: "コスパ型", 7: "失敗回避型", 8: "使用シーン型", 9: "ギフト・季節型",
    10: "質問・アンケート型", 11: "豆知識型", 12: "体験談・ストーリー型", 13: "旅行プラン型",
}
# 何件の商品を使う型か(0 は商品を使わない型)
ITEM_COUNT = {1: 1, 2: 3, 3: 1, 4: 3, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 0, 11: 0, 12: 0, 13: 0}
# 商品の並び順(楽天APIの sort 指定)
SORT = {2: "-reviewCount", 4: "-reviewCount"}
REPLY_NOTICE = "※広告を含みます。価格・在庫・ポイントは変動します。購入前に商品ページでご確認ください。"


def shorten(name, n=26):
    """商品名の【】や記号を取り除いて短くする。"""
    name = re.sub(r"【[^】]*】|\[[^\]]*\]|※[^ 　]*", "", name)
    name = re.sub(r"[\s　]+", " ", name).strip()
    return name if len(name) <= n else name[: n - 1] + "…"


def estimated_length(text):
    return len(PLACEHOLDER.sub("x" * PLACEHOLDER_ESTIMATE, text))


def placeholders(text):
    return PLACEHOLDER.findall(text)


def _line(item, d):
    return f"{shorten(item.name)} / 約{item.price:,}円 / ★{item.review_average:.1f}({item.review_count}件)"


def _reply(items, d, urls_first=True):
    lines = ["【PR】リンクはこちら"]
    for i, it in enumerate(items, 1):
        label = f"{i}. " if len(items) > 1 else ""
        lines.append(f"{label}{shorten(it.name, 20)}\n{it.affiliate_url or it.url}")
    lines.append(f"({d.month}/{d.day}時点の情報)")
    lines.append(REPLY_NOTICE)
    return "\n".join(lines)


def build(type_id, items, d, keyword=""):
    """(本文, リプライ) を返す。リプライが不要な型は空文字。"""
    it = items[0] if items else None
    asof = f"{d.month}/{d.day}時点"

    if type_id == 1:
        return (
            f"【PR】《悩み。例: 在宅で肩がこる》、ありませんか?\n\n"
            f"《その悩みが起きる場面を1行で》\n\n"
            f"私ならまずこれを試します👇\n{_line(it, d)}\n\n"
            f"選ぶ理由: 《あなたの言葉で。例: 軽さと価格のバランスがいい》\n\n"
            f"リンクはリプ欄に置いておきます。", _reply(items, d))
    if type_id == 2:
        body = "\n".join(f"{n}. {_line(x, d)}" for n, x in enumerate(items, 1))
        return (
            f"【PR】《{keyword or '商品ジャンル'}》3つを比べてみました\n\n{body}\n\n"
            f"選び方の目安\n・《こだわる人: どれ》\n・《コスパ重視: どれ》\n\n"
            f"※レビュー数・評価は楽天市場の表示({asof})。使用感ではありません。\nリンクはリプ欄です。",
            _reply(items, d))
    if type_id == 3:
        return (
            f"【PR】《使ったことがある場合のみ: 使用感を書く / 使っていない場合: 『楽天のレビューから見た印象』と明記》\n\n"
            f"{_line(it, d)}\n\n"
            f"良い口コミで多いのは: 《レビューを自分で読んで要約》\n"
            f"気になる口コミ: 《低評価の内容も1つ紹介》\n\n"
            f"向いている人: 《》\nリンクはリプ欄です。", _reply(items, d))
    if type_id == 4:
        body = "\n".join(f"{n}位 {_line(x, d)}" for n, x in enumerate(items, 1))
        return (
            f"【PR】《ジャンル》レビュー件数が多い順 TOP3({asof})\n\n{body}\n\n"
            f"※楽天公式ランキングではなく、検索結果をレビュー件数の多い順に並べたものです。\n"
            f"一言: 《あなたの感想》\nリンクはリプ欄です。", _reply(items, d))
    if type_id == 5:
        return (
            f"【PR】《開催中のセール名。例: 楽天お買い物マラソン》の前にチェックしたい1品\n\n"
            f"{_line(it, d)}\n\n"
            f"買う前のメモ: 《エントリー必須か・期間・買い回りの条件を公式ページで確認して書く》\n"
            f"セール価格は《終了日》までとは限りません。\nリンクはリプ欄です。", _reply(items, d))
    if type_id == 6:
        return (
            f"【PR】《予算》円以内で探すなら、これは候補になりそう\n\n"
            f"{_line(it, d)}\n\n"
            f"コスパが良いと思う点: 《》\nもう少し安い選択肢が良い人は: 《別の探し方》\nリンクはリプ欄です。",
            _reply(items, d))
    if type_id == 7:
        return (
            f"【PR】《ジャンル》を買う前に確認したい3つのこと\n\n"
            f"1. 《サイズ・対応機種など》\n2. 《保証・返品条件》\n3. 《よくある失敗》\n\n"
            f"この条件で探すなら、こんな商品があります👇\n{_line(it, d)}\nリンクはリプ欄です。",
            _reply(items, d))
    if type_id == 8:
        return (
            f"【PR】《場面。例: 朝の支度が5分短くなった/なりそう》\n\n"
            f"《使うシーンを具体的に2〜3行》\n\n{_line(it, d)}\n\n"
            f"《実際に使っていない場合は『こんな使い方ができそう』と書く》\nリンクはリプ欄です。",
            _reply(items, d))
    if type_id == 9:
        return (
            f"【PR】《贈る相手。例: 家電好きの友人》へのギフト、迷っているなら\n\n"
            f"{_line(it, d)}\n\n"
            f"おすすめの理由: 《》\n贈る前の注意: 《サイズ・のし・配送日など》\nリンクはリプ欄です。",
            _reply(items, d))
    if type_id == 10:
        return (
            "《質問。例: 在宅ワークで「買ってよかった!」と思ったものは?》\n\n"
            "私は《あなたの答え》です。\n"
            "みなさんのおすすめ、ぜひ教えてください🙌", "")
    if type_id == 11:
        return (
            "《豆知識のタイトル。例: モバイルバッテリー、飛行機に持ち込めるのは?》\n\n"
            "・《ポイント1》\n・《ポイント2》\n・《ポイント3》\n\n"
            "《出典(公式サイトなど)》", "")
    if type_id == 12:
        return (
            "《最近の失敗談・発見・買い物のきっかけなど、自分の経験を3〜5行で》\n\n"
            "《そこから学んだこと》", "")
    if type_id == 13:
        return (
            "【PR】《行き先》へ《日数》のプラン案\n\n"
            "・《移動》\n・《泊まる場所の条件。例: 駅近・朝食付き》\n・《予算の目安》\n\n"
            "楽天トラベルのリンクはリプ欄です(《プラン名》)。\n※料金・空室は変動します。",
            "【PR】《楽天アフィリエイト管理画面で作った 楽天トラベル のリンクを貼る》\n"
            "※広告を含みます。料金・空室状況は予約ページでご確認ください。")
    raise ValueError(f"未知の型です: {type_id}")
