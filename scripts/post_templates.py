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
    10: "質問・アンケート型", 11: "豆知識型", 12: "体験談・ストーリー型", 13: "旅行プラン型", 14: "注意喚起型", 15: "反響まとめ型",
}
# 何件の商品を使う型か(0 は商品を使わない型)
ITEM_COUNT = {1: 1, 2: 3, 3: 1, 4: 3, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 0, 11: 0, 12: 0, 13: 0, 14: 1, 15: 0}
# 商品の並び順(楽天APIの sort 指定)
SORT = {2: "-reviewCount", 4: "-reviewCount"}
REPLY_NOTICE = "※広告を含みます。価格・在庫・ポイントは変動します。購入前に商品ページでご確認ください。"


_COMPACT = False  # True のとき、商品の行から「★評価(件数)」を省いて短くする
_NAME_LEN = 26  # 商品名の最大文字数(本文が500文字に収まらないときは build() が自動で短くする)


def shorten(name, n=None):
    n = n or _NAME_LEN
    """商品名の【】や記号を取り除いて短くする。"""
    name = re.sub(r"【[^】]*】|\[[^\]]*\]|※[^ 　]*|[((][^))]*(P\d+倍|ポイント|OFF|オフ|クーポン|送料無料|セール)[^))]*[))]", "", name)
    name = re.sub(r"(ランキング|楽天|週間|月間|デイリー)\d*位(入賞|獲得)?|送料無料|ポイント\d+倍|最安値挑戦|激安", "", name)
    name = re.sub(r"[\s　]+", " ", name).strip()
    return name if len(name) <= n else name[: n - 1] + "…"


def estimated_length(text):
    return len(PLACEHOLDER.sub("x" * PLACEHOLDER_ESTIMATE, text))


def placeholders(text):
    return PLACEHOLDER.findall(text)


def _line(item, d):
    if _COMPACT:
        return f"{shorten(item.name)} / 約{item.price:,}円"
    return f"{shorten(item.name)} / 約{item.price:,}円 / ★{item.review_average:.1f}({item.review_count}件)"


def _reply(items, d, start=1):
    """リプライ(リンク用)。start=2 なら「2.」から番号を振る(本文に1つ目のリンクを入れた場合)。"""
    lines = ["【PR】リンクはこちら" if start == 1 else "【PR】他の商品のリンクはこちら"]
    for i, it in enumerate(items, start):
        label = f"{i}. " if (len(items) > 1 or start > 1) else ""
        lines.append(f"{label}{shorten(it.name, 20)}\n{it.affiliate_url or it.url}")
    lines.append(f"({d.month}/{d.day}時点の情報)")
    lines.append(REPLY_NOTICE)
    return "\n".join(lines)


def _build_reply_mode(type_id, items, d, keyword=""):
    """リンクをリプライに置く形の (本文, リプライ)。"""
    it = items[0] if items else None
    asof = f"{d.month}/{d.day}時点"

    if type_id == 1:
        return (
            f"【PR】《悩み。例: 勉強机で長時間座ると腰がつらい》、ありませんか?\n\n"
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
            f"【PR】《贈る相手。例: 受験生の子ども》へのギフト、迷っているなら\n\n"
            f"{_line(it, d)}\n\n"
            f"おすすめの理由: 《》\n贈る前の注意: 《サイズ・のし・配送日など》\nリンクはリプ欄です。",
            _reply(items, d))
    if type_id == 10:
        return (
            "《意見が割れる質問。例: 受験期の夜食、いつまで用意する? A毎日 B週末だけ C用意しない》\n\n"
            "私は《あなたの答え》です。\n"
            "みなさんのおすすめ、ぜひ教えてください🙌", "")
    if type_id == 11:
        return (
            "《豆知識のタイトル。例: 共通テストの持ち物、時計は何が使える?(公式の案内で確認してから書く)》\n\n"
            "・《ポイント1》\n・《ポイント2》\n・《ポイント3》\n\n"
            "《出典(公式サイトなど)》", "")
    if type_id == 12:
        return (
            "《最近の失敗談・発見・買い物のきっかけなど、自分の経験を3〜5行で》\n\n"
            "《そこから学んだこと》", "")
    if type_id == 13:
        return (
            "【PR】《行き先。例: 〇〇大学の受験で泊まる宿の選び方》《日数》のプラン案\n\n"
            "・《移動》\n・《泊まる場所の条件。例: 駅近・朝食付き》\n・《予算の目安》\n\n"
            "楽天トラベルのリンクはリプ欄です(《プラン名》)。\n※料金・空室は変動します。",
            "【PR】《楽天アフィリエイト管理画面で作った 楽天トラベル のリンクを貼る》\n"
            "※広告を含みます。料金・空室状況は予約ページでご確認ください。")
    if type_id == 14:
        return (
            f"【PR】《受験生の親向け。例: 〇〇は、買う前に一度立ち止まった方がいいかも》\n\n"
            f"理由は《事実だけで。価格・条件・口コミなど根拠を書く》\n"
            f"・《ポイント1》\n・《ポイント2》\n\n"
            f"代わりにこの条件で探すなら👇\n{_line(it, d)}\n\n"
            f"※個人の感想・判断です。《特定の店や会社を断定的に批判しない》\nリンクはリプ欄です。",
            _reply(items, d))
    if type_id == 15:
        return (
            "《ヒット投稿のテーマ。例: 指定校・総合型・一般、実際どうだった?》に、たくさんの返信ありがとうございます。\n\n"
            "返信をまとめると👇\n"
            "・《意見A: どれくらいの人が》…《理由》\n・《意見B》…《理由》\n・《意見C》…《理由》\n\n"
            "私の感想: 《》\n(個別のコメントは引用せず、要約しています)", "")
    raise ValueError(f"未知の型です: {type_id}")


_LINK_LINE = re.compile(r"[^\n]*リンクはリプ欄[^\n]*")


def _to_link_in_main(type_id, items, d, main, reply):
    """リンクを本文に入れる形に変える(実測で、リプライ欄は閲覧数が1〜3%しかなかったため)。"""
    if not reply:
        return main, reply
    if items:
        url = items[0].affiliate_url or items[0].url
    else:
        url = "《楽天アフィリエイト管理画面で作った 楽天トラベル のリンク》"
    label = "▼リンク(広告)" if len(items) <= 1 else "▼1つ目の商品のリンク(広告)"
    block = f"{label}\n{url}\n({d.month}/{d.day}時点。価格・在庫は変動します)"
    if len(items) > 1:
        block += "\n他の商品のリンクはリプ欄に置きます"
    main = _LINK_LINE.sub(block, main, count=1)
    return main, (_reply(items[1:], d, start=2) if len(items) > 1 else "")


PR_MARK = "【PR】"


def has_pr_mark(main):
    """広告であることが1行目で分かるか(先頭の【PR】、または1行目の終わりの(PR))。"""
    first = main.split("\n")[0].rstrip()
    return first.startswith(PR_MARK) or first.endswith("(PR)")


def apply_pr_style(main, pr_style):
    """pr_style='head': 先頭に【PR】(従来)/ 'inline': 1行目の終わりに(PR)(初期設定)。"""
    if pr_style != "inline" or not main.startswith(PR_MARK):
        return main
    rest = main[len(PR_MARK):]
    first, sep, tail = rest.partition("\n")
    return first.rstrip() + "(PR)" + sep + tail


def build(type_id, items, d, keyword="", link_in_main=True, pr_style="inline"):
    """(本文, リプライ) を返す。

    link_in_main=True(初期値): アフィリエイトリンクを本文に入れる。1商品の型はリプライ不要。
    比較型・ランキング型は、本文に1つ目の商品のリンク、リプライに2つ目以降の商品のリンクを置く。
    link_in_main=False: 従来どおり、リンクはリプライに置く。
    本文が500文字を超えるときは、商品名・評価の表示を短くして収める(それでも超える場合は make_draft が警告する)。
    """
    global _NAME_LEN, _COMPACT
    original = _NAME_LEN
    try:
        for n, compact in ((original, False), (20, False), (14, False), (14, True), (10, True)):
            _NAME_LEN, _COMPACT = n, compact
            main, reply = _build_reply_mode(type_id, items, d, keyword)
            if link_in_main:
                main, reply = _to_link_in_main(type_id, items, d, main, reply)
            main = apply_pr_style(main, pr_style)
            if estimated_length(main) <= LIMIT and estimated_length(reply) <= LIMIT:
                return main, reply
        return main, reply  # 収まらなくても、いちばん短い形を返す(make_draft が文字数の警告を出す)
    finally:
        _NAME_LEN, _COMPACT = original, False
