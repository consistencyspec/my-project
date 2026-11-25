"""お布施はいくら？ 物語版：「お気持ち派」vs「定額派」の論争を、出来事カードと議席でつなぐ(新常識クロニクル お布施編)。

  .venv/bin/python scripts/ofuse_story.py           -> output/ofuse_story/ofuse_story_draft.mp4(ナレーションつき)
  .venv/bin/python scripts/ofuse_story.py --script  -> content/ofuse_war_story.md(台本)だけ作り直す
  .venv/bin/python scripts/ofuse_story.py --voice   -> 声と台本だけ(映像は作らない)
  .venv/bin/python scripts/ofuse_story.py --stills  -> 各場面の静止画だけ(output/ofuse_story/stills/)

赤ワインの回(wine_story.py)と同じ型。違いは、2つの派が「お気持ち派(オレンジ)」と「定額派(青)」であること、
議席の目安が研究ではなく「声明・調査」であること、一般の人とお坊さんの意識調査を2つの議会で並べる場面(vs)があること。
"""
import os
import re
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frames  # noqa: E402
from frames import BAD, GOOD, INK, SEATS, SUB, TRIM, W, WHITE, arrow, font, panel, stage, text  # noqa: E402
from motion import Card, blank, out_back, out_cubic, parliament_frame, seg  # noqa: E402
import coffee_war as cw  # noqa: E402
import coffee_story as cs  # noqa: E402
from coffee_story import WithAudio, chapter_start_frame, chip, story_frames, words, year_tag  # noqa: E402
import ofuse_war as ow  # noqa: E402
from ofuse_war import GRAY, bars, cart, envelope, monk, price_tag, question, temple  # noqa: E402
from thumbnail import EPISODES, series_card  # noqa: E402
import narrate  # noqa: E402

frames.LBL[:] = ["お気持ち派", "定額派"]
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "output", "ofuse_story")
SCRIPT_MD = os.path.join(HERE, "..", "content", "ofuse_war_story.md")
EVENTS = ow.EVENTS
EPISODE = "ofuse_war"

# お布施の回で読み間違えやすい語(この回だけで足す。他の回の声のキャッシュは変わらない)
narrate.MM_DICT += ["お布施/おふせ", "布施/ふせ", "お気持ち派/おきもちは", "定額派/ていがくは", "定額/ていがく",
                    "Amazon/アマゾン", "お坊さん便/おぼうさんびん", "お坊さん/おぼうさん", "全日本仏教会/ぜんにほんぶっきょうかい",
                    "対価/たいか", "法事/ほうじ", "法要/ほうよう", "読経/どきょう", "宗派/しゅうは", "家族葬/かぞくそう",
                    "葬儀/そうぎ", "お葬式/おそうしき", "鎌倉新書/かまくらしんしょ", "山形/やまがた", "福井/ふくい",
                    "山梨/やまなし", "奈良/なら", "大分/おおいた", "安居/あんご", "鵜飼秀徳/うかいひでのり", "檀家/だんか",
                    "包め/つつめ", "お包み/おつつみ", "執着/しゅうちゃく", "明示/めいじ", "僧侶/そうりょ", "修行/しゅぎょう",
                    "目安/めやす", "葬儀社/そうぎしゃ", "一般の人/いっぱんのひと"]
narrate.NUM_STYLE = "dict"
narrate.ICHINICHI_PAUSE = 0.03
narrate.PAUSE_SHORT = 0
narrate.PAUSE_QUOTE_HA = 0
narrate.TEXT_READ += [("Zoom安居", "ズーム安居"), ("Surfvote", "サーフボート"),
                      ("12月", "じゅうにがつ"),   # 「じゅうにつき」と読まれた(2026-11-25 聞き取り)
                      ("下が", "さが")]           # 「もとがる」と読まれた(赤ワイン・1万歩の回と同じ)
# 「8」は「ジュウ」「ヒャク」のすぐあとだと濁るので、ごく短い間をはさむ(赤ワインの回と同じ)
cs.VOICE_FIX[:0] = [("208人", "ニヒャク<#0.05#>ハチにん"), ("28.4%", "ニジュウ<#0.05#>ハッテンヨンパーセント")]

_voice_for = cs.voice_for


def _calm_voice_for(i, narr, cache, emotion=None, fresh=False):
    return _voice_for(i, narr, cache, emotion=emotion or ("calm" if "逆転です" in narr else None), fresh=fresh)


cs.voice_for = _calm_voice_for
cs.STEP_COLORS.update({"なぜ反対？": GOOD, "反発": GOOD, "値段": BAD, "なぞ": BAD, "お布施は？": BAD, "対決": INK,
                       "はじまり": INK, "家族葬": INK, "2022年": INK})


def E(f):
    return f


# ---------- 場面 ----------
SCENES = [
    ("hook", "お葬式で、お坊さんに渡すお布施。いくら包めばいいのか、お寺に聞いても、返ってくるのは「お気持ちで」。でも、そのお気持ち、全国の平均は約22万円なんです。"),
    ("title", "お布施は、なぜ金額がはっきりしないのか。定額にすべきか、お気持ちのままでいいのか。10年近く続く論争を、データで判定します。新常識クロニクル、今日のテーマは「お布施はいくら？」です。"),
    ("rules_intro", "見方はかんたん。論争を選挙に見立てます。議席は100。オレンジは、金額は決めずに気持ちで、と考えるお気持ち派の色。青は、金額をはっきり示すべき、と考える定額派の色です。スタートは50対50です。"),
    ("rules", "出来事があるたびに、勝った側に議席が移ります。団体の声明や大手の新しいサービスは15議席、全国調査は10議席、数百人の意識調査は6議席、条件が限られた結果やネット投票は3議席です。",
     ["団体の声明", "全国調査", "数百人", "条件が限られた"]),
    ("chapter_start", "それでは、行ってみましょう！第1話。物語は、2015年の年末から始まります。", "第1話", "Amazonにお坊さん"),

    # 第1話 Amazonにお坊さん
    ("story", 1, "はじまり", "2015年12月 Amazonに、お坊さんを呼べる「お坊さん便」が登場",
     [E(lambda d: year_tag(d, 440, 360, "2015年12月")), E(lambda d: cart(d, 450, 610, 300)),
      E(lambda d: arrow(d, 640, 730, 610)), E(lambda d: monk(d, 900, 420, 360)),
      E(lambda d: words(d, 1430, 540, "お坊さん便", 110, BAD)), E(lambda d: words(d, 1430, 680, "法事・法要に呼べる", 56))],
     "2015年12月、通販サイトのAmazonに、ある商品が登場します。その名も「お坊さん便」。法事や法要に、お坊さんを呼べるサービスです。"),
    ("story", 1, "値段", "お布施込みで3万5千円の定額。追加の料金もはっきり書かれていた",
     [E(lambda d: envelope(d, 420, 580, 400)), E(lambda d: arrow(d, 620, 710, 580)),
      E(lambda d: price_tag(d, 1150, 450, 240, "3万5千円")), E(lambda d: words(d, 1150, 620, "お布施込みの定額", 68, BAD)),
      E(lambda d: words(d, 1150, 750, "お墓の前の読経は +1万円", 52))],
     "驚かれたのは、その値段です。お布施込みで、3万5千円の定額。お墓の前での読経はプラス1万円、など、追加の料金もはっきり書かれていました。お気持ちで、とは正反対です。"),
    ("card", 1, "相場が分からず困っていた人には、ありがたいサービス。定額派が、いきなり15議席の大勝です。"),
    ("story", 1, "反発", "2016年3月 全日本仏教会がAmazonに抗議。販売の取りやめを求めた",
     [E(lambda d: year_tag(d, 440, 360, "2016年3月")), E(lambda d: temple(d, 480, 620, 380)),
      E(lambda d: arrow(d, 720, 810, 610)),
      E(lambda d: words(d, 1330, 530, "全日本仏教会", 84, GOOD)), E(lambda d: words(d, 1330, 670, "販売をやめてほしい", 64))],
     "これに強く反発したのが、多くの宗派が加わる全日本仏教会です。2016年3月、Amazonに抗議の文書を送り、販売をやめるよう求めました。"),
    ("story", 1, "なぜ反対？", "お布施はサービスの対価ではない。値段をつけると商売になり、税金がかかるおそれも",
     [E(lambda d: envelope(d, 420, 580, 400)),
      E(lambda d: words(d, 1150, 420, "お布施は修行のひとつ", 66, GOOD)), E(lambda d: words(d, 1150, 570, "値段をつけると商売に", 66)),
      E(lambda d: words(d, 1150, 720, "税金がかかるおそれも", 66, BAD))],
     "理由は、お布施はサービスの対価ではない、という考えです。お布施は修行のひとつで、差し出す側にとっても、執着を手放す行いだとされます。値段をつけると、宗教ではなく商売になってしまう。それに、もし対価とみなされれば、税金がかかるおそれもある、という心配もありました。"),
    ("card", 2, "お気持ち派が15議席を取り返し、50対50。振り出しに戻ります。"),

    # 第2話 小さくなるお葬式
    ("story", 2, "家族葬", "家族や親しい人だけで送る「家族葬」が増えていった",
     [E(lambda d: cw.crowd(d, 300, 420, 3, 2, 160)),
      E(lambda d: words(d, 1300, 420, "家族葬の割合", 60, SUB)), E(lambda d: words(d, 1300, 560, "2015年  31.3%", 76)),
      E(lambda d: words(d, 1300, 700, "2017年  37.9%", 76))],
     "では、実際のお葬式は、どう変わってきたのでしょう。葬儀の情報サービスの鎌倉新書は、2013年から、くり返し全国調査をしています。目立つのが、家族や親しい人だけで送る家族葬。2015年には31.3%、2017年には37.9%と、増えていきました。"),
    ("card", 3, "一方で、2017年の調査では、しきたりを重視する地域として、山形、福井、山梨、奈良、大分の5県が挙がりました。地域が限られた結果なので、お気持ち派が3議席です。"),
    ("story", 2, "2022年", "家族葬が55.7%で最多に。葬儀の総額は約178万円から約111万円へ",
     [E(lambda d: year_tag(d, 440, 360, "2022年")),
      E(lambda d: bars(d, 330, 690, [("2017年", 178.2, GRAY), ("2022年", 110.7, GRAY)], 180, 200, bw=150, gap=90)),
      E(lambda d: words(d, 1320, 460, "家族葬が55.7%で最多", 64)), E(lambda d: words(d, 1320, 600, "葬儀の総額", 56, SUB)),
      E(lambda d: words(d, 1320, 720, "5年で約67万円ダウン", 76))],
     "そして2022年。家族葬は55.7%で、ついに最多になります。葬儀にかかる費用の総額も、2017年の約178万円から、約111万円へ。5年で、約67万円も下がりました。"),
    ("story", 2, "お布施は？", "お布施の平均は約23万7千円(2020年)→約22万4千円(2022年)。ほとんど下がらない",
     [E(lambda d: bars(d, 330, 690, [("2020年", 23.7, BAD), ("2022年", 22.4, BAD)], 30, 300, bw=150, gap=90)),
      E(lambda d: words(d, 1320, 500, "お布施の平均", 64)), E(lambda d: words(d, 1320, 660, "ほぼ横ばい", 120, BAD))],
     "ところが、お布施はどうでしょう。2020年の平均は約23万7千円。2022年は約22万4千円。ほとんど下がっていないんです。"),
    ("story", 2, "なぞ", "いちばん多いのは1万〜10万円未満で28.4%。10万円台も23.9%。人によってバラバラ",
     [E(lambda d: question(d, 420, 400, 380)),
      E(lambda d: words(d, 1200, 420, "1万〜10万円未満  28.4%", 60)), E(lambda d: words(d, 1200, 540, "10万〜20万円未満  23.9%", 60)),
      E(lambda d: words(d, 1200, 700, "人によってバラバラ", 92, BAD))],
     "お葬式は小さく、安くなったのに、お布施だけは下がらない。しかも、いちばん多かったのは、1万円以上10万円未満で28.4%。10万円台も23.9%。人によって、金額がまったく違うんです。これでは、いくら包めばいいのか、ますます分かりません。"),
    ("card", 4, "定額派が10議席を取ります。"),
    ("seats", 4, "定額派が57議席、お気持ち派が43議席。ついに、逆転です。"),
    ("card", 5, "実は、全日本仏教会の調査でも、葬儀や法要の不安として、お布施の金額が分からない、と答えた人が64.9%いた、と報じられています。定額派がさらに6議席。"),

    # 第3話 一般の人 vs お坊さん
    ("card", 6, "2024年2月には、ネット投票の結果が発表されます。お布施の金額を明示すべきか。賛成は30.5%。いちばん多かったのは、何万円から何万円、と幅を持たせて示す、で47.5%。反対は16.9%でした。ただし59票の小さな投票。定額派が3議席です。"),
    ("story", 3, "対決", "2024年11月 同じ質問を、一般の人とお坊さんの両方に聞いた",
     [E(lambda d: year_tag(d, 440, 360, "2024年11月")), E(lambda d: cw.crowd(d, 300, 430, 3, 2, 140)),
      E(lambda d: words(d, 960, 560, "vs", 110)),
      E(lambda d: monk(d, 1250, 420, 260)), E(lambda d: monk(d, 1450, 420, 260)),
      E(lambda d: words(d, 960, 790, "お布施の金額を明示することに、賛成ですか？", 54))],
     "そして2024年11月。住職で作家の鵜飼秀徳さんが、仏教のオンライン勉強会、Zoom安居で行った調査を紹介しました。同じ質問を、一般の人と、お坊さんの両方に聞いたんです。お布施の金額を明示することに、賛成ですか？"),
    ("vs", "一般の人、208人では、賛成が68.7%。反対は、わずか11.1%。一方、お坊さん203人では、賛成が26.6%、反対が33%。そして、どちらでもない、が40.4%で、いちばん多かったんです。"),
    ("card", 7, "一般の人の声で、定額派が6議席。"),
    ("card", 8, "お坊さんは、反対がやや多いものの、意見は割れています。お気持ち派は3議席にとどまりました。"),

    ("final", "最終結果は、お気持ち派が31議席、定額派が69議席。それでも、当選確実は出せません。お布施の額を決めるのは、法律でも調査でもなく、それぞれのお寺と家族だからです。宗派や地域、お寺とのつきあいによっても、金額は大きく変わります。"),
    ("summary", "今日のまとめです。お布施の金額は、聞いてもいいんです。「皆さん、どのくらいお包みされていますか」と聞けば、目安を教えてもらえることもあります。分からなければ、葬儀社や、同じお寺の檀家さんに聞くのも手。全国の平均は約22万円ですが、1万円台から数十万円まで、幅はとても大きい。そして、お布施は対価ではない、というお寺の考えも、知っておくと話しやすくなります。聞きづらいお布施。でも、聞いてはいけないものではありません。",
     ["聞いても", "葬儀社", "全国の平均", "お布施は対価"]),
    ("next", "次回のテーマは「サウナは長生きのもと？」。フィンランドの男性を、20年追いかけた研究から始まります。"),
    ("outro", "新常識クロニクルでは、これからも、健康や暮らしの論争を、データでどんどん分析していきます。次に取り上げてほしい論争があれば、ぜひコメントで教えてください。チャンネル登録と高評価も、よろしくお願いします！"),
]


# ---------- お布施の回だけの画面 ----------
def at_maker(narr, alen, lead):
    return lambda k: lead + narr.index(k) / len(narr) * alen  # noqa: E731


def hook_maker(narr):
    """封筒がポンと出て「いくら？」→「お気持ちで」のふきだし →「平均 約22万円」の帯。"""
    def make(alen, lead):
        at = at_maker(narr, alen, lead)
        t1, t2, t3 = at("お布施") - 0.3, at("お気持ちで"), at("全国の平均")

        def frame(t):
            im = stage()[0].convert("RGBA")
            lay = blank()
            dd = ImageDraw.Draw(lay)
            k1 = seg(t, t1, t1 + 0.4)
            if k1 > 0:
                envelope(dd, 640, 560, 480 * (0.6 + 0.4 * out_back(k1)))
            k2 = seg(t, t2, t2 + 0.4)
            if k2 > 0:
                monk(dd, 1250, 360, 400 * (0.6 + 0.4 * out_back(k2)))
            im.alpha_composite(lay)
            d = ImageDraw.Draw(im)
            if k1 > 0:
                chip(d, 640, 190, "いくら包めばいい？", BAD, int(60 * (0.6 + 0.4 * out_back(k1))))
            if k2 > 0:
                chip(d, 1300, 190, "お気持ちで", GOOD, int(60 * (0.6 + 0.4 * out_back(k2))))
            k3 = seg(t, t3, t3 + 0.45)
            if k3 > 0:
                sc = 1.5 - 0.5 * out_back(k3)
                cx, cy = W / 2, 900
                bw, bh = 560 * sc, 80 * sc
                d.rounded_rectangle([cx - bw, cy - bh, cx + bw, cy + bh], radius=24 * sc, fill=BAD, outline=WHITE,
                                    width=max(3, int(8 * sc)))
                text(d, (cx, cy), "全国の平均  約22万円", int(72 * sc), WHITE, anchor="mm")
            return im.convert("RGB")
        return frame, t3 + 0.8
    return WithAudio(make)


def rules_frame_maker(narr, keys):
    rows = [("団体の声明・大手の新サービス", "15議席"), ("全国調査", "10議席"),
            ("数百人の意識調査", "6議席"), ("条件が限られた結果・ネット投票", "3議席")]

    def make(alen, lead):
        times = [lead + narr.index(k) / len(narr) * alen - 0.2 for k in keys]

        def frame(t):
            im, d = stage()
            panel(d, (300, 150, 1620, 960))
            text(d, (W / 2, 230), "議席を動かすルール", 80, INK, anchor="mm")
            now = max([i for i, tt in enumerate(times) if t >= tt], default=-1)
            for i, (k, v) in enumerate(rows):
                kk = seg(t, times[i], times[i] + 0.4)
                if kk <= 0:
                    continue
                sc = 0.7 + 0.3 * out_back(kk)
                cx, cy = W / 2, 408 + i * 120
                hw, hh = 580 * sc, 48 * sc
                d.rounded_rectangle([cx - hw, cy - hh, cx + hw, cy + hh], radius=hh,
                                    fill=(255, 232, 205) if i == now else (240, 236, 228))
                text(d, (cx - hw + 50 * sc, cy), k, int(48 * sc), INK, anchor="lm")
                text(d, (cx + hw - 50 * sc, cy), v, int(60 * sc), GOOD, anchor="rm")
            text(d, (W / 2, 880), "※ 議席は演出のための目安です", 36, SUB, heavy=False, anchor="mm")
            return im
        return frame, times[-1] + 0.6
    return WithAudio(make)


def rules_intro_frame(t):
    im = parliament_frame("", "論争を選挙に見立てる", 50, 50, t, tag="見方")
    d = ImageDraw.Draw(im)
    for x, lab, c in ((W / 2 - 400, "金額は気持ちで", GOOD), (W / 2 + 400, "金額をはっきり示す", BAD)):
        k = seg(t, 0.8, 1.2)
        if k > 0:
            chip(d, x, 300, lab, c, int(46 * (0.6 + 0.4 * out_back(k))))
    return im


# 一般の人とお坊さんの意識調査(2つの議会)。席の数は割合を100席に丸めたもの(左=反対、灰=そのほか、右=賛成)
VS_SIDES = [("一般の人 208人", (11, 20, 69), [("賛成", "68.7%", BAD), ("反対", "11.1%", GOOD), ("そのほか", "20.2%", GRAY)], "一般の人"),
            ("お坊さん 203人", (33, 40, 27), [("賛成", "26.6%", BAD), ("反対", "33.0%", GOOD), ("どちらでもない", "40.4%", GRAY)], "お坊さん")]


def vs_maker(narr):
    def make(alen, lead):
        at = at_maker(narr, alen, lead)
        starts = [at(VS_SIDES[0][3]), at(VS_SIDES[1][3])]

        def frame(t):
            im, d = stage()
            text(d, (W / 2, 125), "お布施の金額を明示することに賛成？", 56, WHITE, anchor="mm")
            text(d, (W / 2, 560), "vs", 90, TRIM, anchor="mm")
            for k, (title, (no, gray, yes), rows, _) in enumerate(VS_SIDES):
                cx, cy, R = (500, 1420)[k], 610, 320
                a = seg(t, starts[k] - 0.4, starts[k])
                if a <= 0:
                    continue
                text(d, (cx, 215), title, 56, tuple(int(255 * a + 40 * (1 - a)) for _ in range(3)), anchor="mm")
                p = out_cubic(seg(t, starts[k], starts[k] + 1.4))
                shown = int(100 * p)
                s = R * 0.05
                for i, (ang, r) in enumerate(SEATS[:shown]):
                    import math
                    x, y = cx + R * r * math.cos(ang), cy - R * r * math.sin(ang)
                    c = GOOD if i < no else (GRAY if i < no + gray else BAD)
                    d.rounded_rectangle([x - s, y - s, x + s, y + s], radius=s * 0.45, fill=c)
                for j, (lab, v, c) in enumerate(rows):
                    b = seg(t, starts[k] + 1.0 + j * 0.25, starts[k] + 1.4 + j * 0.25)
                    if b <= 0:
                        continue
                    y = 700 + j * 100
                    sc = 0.6 + 0.4 * out_back(b)
                    d.rounded_rectangle([cx - 300 * sc, y - 42 * sc, cx + 300 * sc, y + 42 * sc], radius=42 * sc, fill=c)
                    text(d, (cx - 260 * sc, y), lab, int(44 * sc), WHITE, anchor="lm")
                    text(d, (cx + 260 * sc, y), v, int(56 * sc), WHITE, anchor="rm")
            text(d, (W / 2, 1010), "Zoom安居の調査(JBpress 2024年11月5日)。席は割合を100席に丸めたもの", 30, (170, 176, 192),
                 heavy=False, anchor="mm")
            return im
        return frame, starts[1] + 2.4
    return WithAudio(make)


def summary_maker(narr, keys):
    items = [("お布施の金額は", "聞いてもいい", BAD), ("分からなければ", "葬儀社・檀家さんに聞く", BAD),
             ("全国の平均は約22万円", "でも幅はとても大きい", INK), ("お寺の考え", "お布施は対価ではない", GOOD)]

    def make(alen, lead):
        times = [lead + narr.index(k) / len(narr) * alen - 0.3 for k in keys]

        def frame(t):
            im, d = stage()
            panel(d, (200, 150, 1720, 960))
            text(d, (960, 230), "まとめ", 76, INK, anchor="mm")
            for i, (a, b, c) in enumerate(items):
                k = seg(t, times[i], times[i] + 0.4)
                if k > 0:
                    y = 340 + i * 150
                    d.rounded_rectangle([280, y, 1640, y + 120], radius=60, fill=(240, 236, 228))
                    d.ellipse([300, y + 20, 380, y + 100], fill=c)
                    text(d, (340, y + 60), str(i + 1), 48, WHITE, anchor="mm")
                    text(d, (420, y + 60), a, 44, SUB, heavy=False, anchor="lm")
                    text(d, (1610, y + 60), b, 50, c, anchor="rm")
            return im
        return frame, times[-1] + 0.6
    return WithAudio(make)


NEXT_TITLE = "サウナは長生きのもと？"


def next_frame(t):
    im, d = stage()
    text(d, (W / 2, 260), "次回の論争", 70, TRIM, anchor="mm")
    k = out_back(seg(t, 0.3, 0.8))
    if k > 0:
        im = im.convert("RGBA")
        lay = blank()
        cw.thermo(ImageDraw.Draw(lay), W / 2, 380, 360 * (0.6 + 0.4 * k))
        im.alpha_composite(lay)
        im = im.convert("RGB")
        d = ImageDraw.Draw(im)
    text(d, (W / 2, 850), NEXT_TITLE, 100, WHITE, anchor="mm")
    return im


TOPICS = ["サウナは長生きのもと？", "朝ごはんは食べるべき？", "塩は減らすほどいい？", "牛乳は体にいい？", "日光浴は体にいい？", "人工甘味料は安全？"]


def outro_frame(t):
    im, d = stage()
    k = out_back(seg(t, 0.2, 0.7))
    if k > 0:
        text(d, (W / 2, 230), "新常識クロニクル", int(120 * (0.5 + 0.5 * k)), WHITE, anchor="mm")
    a = seg(t, 0.6, 1.0)
    if a > 0:
        text(d, (W / 2, 350), "これからも、論争をどんどん分析します", 56, tuple(int(TRIM[j] * a + 30 * (1 - a)) for j in range(3)), anchor="mm")
    for i, tp in enumerate(TOPICS):
        kk = seg(t, 1.2 + i * 0.35, 1.55 + i * 0.35)
        if kk <= 0:
            continue
        x, y = (560 if i % 2 == 0 else 1360), 480 + (i // 2) * 110
        sc = 0.6 + 0.4 * out_back(kk)
        tw = d.textlength(tp, font=font(int(46 * sc))) + 60 * sc
        d.rounded_rectangle([x - tw / 2, y - 42 * sc, x + tw / 2, y + 42 * sc], radius=42 * sc, fill=(46, 58, 92))
        text(d, (x, y), tp, int(46 * sc), WHITE, anchor="mm")
    b = seg(t, 3.6, 4.1)
    if b > 0:
        sc = 0.6 + 0.4 * out_back(b)
        cx, cy = W / 2, 850
        bw, bh = 330 * sc, 62 * sc
        d.rounded_rectangle([cx - bw, cy - bh, cx + bw, cy + bh], radius=bh, fill=(220, 40, 40))
        text(d, (cx, cy), "チャンネル登録", int(64 * sc), WHITE, anchor="mm")
        text(d, (cx, cy + bh + 40 * sc), "高評価・コメントもよろしくお願いします", int(36 * sc), WHITE, heavy=False, anchor="mm")
    return im


FINAL_NOTE = "お布施の額は、宗派・地域・お寺とのつきあいで大きく変わる"


# ---------- 組み立て ----------
def dur(narr):
    return max(3.0, len(narr) / 8.0 + 0.8)


def card_of(idx):
    year, country, kindx, title, facts, picto, before, after, headline, source = EVENTS[idx - 1]
    rows = [[(s, cw.color_of(c)) for s, c in row] for row in title]
    return Card(year, country, kindx, rows, facts, picto, before, after, ow.delta_label(before, after), source)


def build_plan():
    """(描く関数, 動く秒数, 合計秒数, 台本の行) のリスト。"""
    plan, last_chapter = [], None
    for sc in SCENES:
        kind, narr = sc[0], sc[-1] if sc[0] not in ("rules", "summary", "chapter_start") else sc[1]
        if kind == "hook":
            plan.append((hook_maker(narr), 0, dur(narr), ("つかみ", "いくら包めばいい？ →「お気持ちで」→ 平均 約22万円", narr)))
        elif kind == "title":
            img = os.path.join(OUT, "00_title.png")
            series_card(*EPISODES[EPISODE]).save(img)
            plan.append(((lambda im: lambda t: im)(Image.open(img)), 0, dur(narr), ("タイトル", "新常識クロニクル:お布施はいくら？", narr)))
        elif kind == "rules_intro":
            plan.append((rules_intro_frame, 1.3, dur(narr), ("ルール説明", "100議席・お気持ち派 vs 定額派・50対50", narr)))
        elif kind == "rules":
            plan.append((rules_frame_maker(narr, sc[2]), 0, dur(narr), ("ルール説明", "議席を動かすルール", narr)))
        elif kind == "chapter_start":
            plan.append((chapter_start_frame(sc[2], sc[3]), 1.2, dur(narr), (sc[2], sc[3], narr)))
        elif kind == "story":
            _, ch, step, tl, els, narr = sc
            fn, anim = story_frames(ch, step, tl, els, first=(ch != last_chapter))
            last_chapter = ch
            plan.append((fn, anim, dur(narr), (f"第{ch}話「{step}」", tl, narr)))
        elif kind == "card":
            last_chapter = None
            e = EVENTS[sc[1] - 1]
            plan.append((card_of(sc[1]).frame, Card.ANIM_END, max(dur(narr), Card.ANIM_END + 1.0),
                         (f"出来事カード {e[0]}", f"{e[6]}→{e[7]}", narr)))
        elif kind == "seats":
            year, _, _, _, _, _, before, after, headline, _ = EVENTS[sc[1] - 1]
            plan.append(((lambda y, h, b, a: lambda t: parliament_frame(y, h, b, a, t))(year, headline, before, after),
                         2.6, max(dur(narr), 3.6), (f"開票速報 {year}", f"{before}→{after}", narr)))
        elif kind == "vs":
            plan.append((vs_maker(narr), 0, dur(narr), ("一般の人 vs お坊さん", "明示に賛成？ 2つの議会", narr)))
        elif kind == "final":
            plan.append((lambda t: cw.final_frame(EVENTS[-1][7], t, note=FINAL_NOTE), 2.6, dur(narr), ("結果", "", narr)))
        elif kind == "summary":
            plan.append((summary_maker(sc[1], sc[2]), 0, dur(sc[1]), ("まとめ", "", sc[1])))
        elif kind == "next":
            plan.append((next_frame, 1.0, dur(narr), ("次回予告", NEXT_TITLE, narr)))
        elif kind == "outro":
            plan.append((outro_frame, 4.2, dur(narr), ("エンディング", "チャンネル登録・今後の論争", narr)))
    return plan


def write_script(plan):
    total = 0.0
    lines = ["# 台本(物語版):お布施はいくら？ 〜「お気持ち派」vs「定額派」論争の行方〜", "",
             "作成：2026-11-25 / 状態：初稿。`scripts/ofuse_story.py` の SCENES から自動で作っています(台本を直すときは SCENES を直す)。", "",
             f"ナレーション合計：約{sum(len(p[3][2]) for p in plan):,}字。場面の長さは合成したナレーションの長さで決まる。", "",
             "この回の2つの派:お気持ち派(オレンジ)=金額は決めず気持ちで/定額派(青)=金額をはっきり示すべき。議席は研究ではなく声明・調査で動かす(目安)。", "",
             "| 時間 | 場面 | 画面のテロップ・内容 | ナレーション |", "|---|---|---|---|"]
    for _, _, sec, (name, tl, narr) in plan:
        m, s = divmod(int(total), 60)
        lines.append(f"| {m}:{s:02d} | {name} | {tl} | {narr} |")
        total += sec
    m, s = divmod(int(total), 60)
    lines += ["", f"合計：約{m}分{s:02d}秒", "",
              "## 議席の推移(お気持ち派の議席)", "", "| # | 年 | 種類 | 前 → 後 | 出典 |", "|---|---|---|---|---|"]
    for i, e in enumerate(EVENTS, 1):
        lines.append(f"| {i} | {e[0]} | {e[2]} | {e[6]} → {e[7]} | {e[9].replace('出典：', '')} |")
    lines += ["", "議席の目安:団体の声明・大手の新サービス15/全国調査10/数百人の意識調査6/条件が限られた結果・ネット投票3。",
              "2017年のしきたり重視の地域は「地域が限られた結果」として3議席。お坊さん203人の調査は、反対がやや多いが「どちらでもない」が最多で意見が割れているため3議席にした。", "",
              "## 公開前に原文で確認すること",
              "- 2015年12月 お坊さん便(みんれび):Amazonマーケットプレイスへの出品は2015年12月8日、税込3万5,000円、墓前の法要は+1万円(ネットショップ担当者フォーラム https://netshop.impress.co.jp/node/2377 で確認)。法事・法要向けであることも確認する",
              "- 2016年3月 全日本仏教会:2016年3月4日にAmazonへ抗議・取り扱い中止を求めた(J-CAST https://www.j-cast.com/2016/03/08260753.html で確認)。「課税の可能性」を理由に挙げたかは原文・婦人公論の記事で確かめる",
              "- 「お布施は修行のひとつ/執着を手放す」は仏教の一般的な説明。全日本仏教会の表現(「お布施はサービスの対価ではありません」)と合わせて確認",
              "- 家族葬:2015年 31.3%(第2回)・2017年 37.9%(第3回の発表は「38%」)・2022年 55.7%(第5回で確認)。2015年の数字は原文で確認",
              "- 2017年 しきたりを重視する地域ベスト5:山形・福井・山梨・奈良・大分(第3回 https://www.kamakura-net.co.jp/newstopics/4013/ で確認)",
              "- 葬儀費用の総額:2017年 178.2万円(お布施を除く)・2022年 110.7万円(過去最安)(確認済み)。「5年で約67万円」は差の計算",
              "- お布施の平均:2020年 23万6,900円(第4回 https://www.e-sogi.com/guide/29463/ で確認する)・2022年 22.4万円(確認済み)。最多は1万円以上〜10万円未満 28.4%、次いで10万円以上〜20万円未満 23.9%(確認済み)",
              "- 「鎌倉新書は2013年から全国調査」:第1回が2013年かを確認(e-sogi の推移ページ)",
              "- **全日本仏教会の調査 64.9%・53.5%**:報道(ben54 など)による二次情報。原典(全日本仏教会の発表)で設問・人数・年を確認する。確認できなければ場面ごと外す",
              "- Surfvote:賛成30.5%・幅を持たせて47.5%・反対16.9%・わからない5.1%、59票、投票期間 2023年11月28日〜2024年1月31日、発表 2024年2月16日(確認済み)",
              "- **Zoom安居の調査**:JBpress(鵜飼秀徳、2024年11月5日)。僧侶203人・一般人208人は確認済み。**割合(一般人 賛成68.7%・反対11.1%/僧侶 はい26.6%・いいえ33.0%・どちらでもない40.4%)は記事の有料部分にあり未確認**。調査を行った時期も確認する", ""]
    with open(SCRIPT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    base = SCRIPT_MD.replace("_story.md", "")
    t, marked, plain = 0.0, [], []
    for i, (_, _, sec, (name, _, narr)) in enumerate(plan, 1):
        m, s_ = divmod(int(t), 60)
        marked.append(f"【{i:02d}】{m}:{s_:02d} {name}\n{narr}\n")
        plain.append(narr + "\n")
        t += sec
    with open(base + "_narration.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(marked))
    with open(base + "_narration_plain.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(plain))
    return total


def spoken_len(narr):
    t = re.sub(r"<#[\d.]+#>", "", narrate.mm_text(narr))
    for entry in narrate.mm_tone(narr)[len(narrate.MM_DICT):]:
        k, v = entry.split("/", 1)
        t = t.replace(k, v)
    return len(t)


def voiced_sec(narr, v):
    from narrate import RATE
    pauses = sum(float(x) for x in re.findall(r"<#([\d.]+)#>", narrate.mm_text(narr)))
    return max(0.5, len(v) / RATE - 2.5 * pauses)


def check_voices(plan, tries=3):
    """文字数に比べて長すぎる声(変な声・笑い声などが混ざった声)を見つける。作り直しは --fix-voices のときだけ。"""
    import numpy as np
    cache = os.path.join(OUT, "voice")
    rates = []
    for i, (_, _, _, meta) in enumerate(plan):
        v = cs.voice_for(i, meta[2], cache)
        rates.append(spoken_len(meta[2]) / voiced_sec(meta[2], v))
    med = float(np.median(rates))
    for i, (_, _, _, meta) in enumerate(plan):
        n = 0
        while rates[i] < med * 0.82 and n < tries and "--fix-voices" in sys.argv:
            n += 1
            print(f"  ! 声が長すぎる({meta[0]}、{rates[i]:.1f}字/秒、ふつうは{med:.1f})ので作り直し {n}/{tries}", flush=True)
            v = cs.voice_for(i, meta[2], cache, fresh=True)
            rates[i] = spoken_len(meta[2]) / voiced_sec(meta[2], v)
        if rates[i] < med * 0.82:
            print(f"  !! 声が長め:{meta[0]}(耳で確認。作り直すなら --fix-voices)", flush=True)


def stills(plan):
    """各場面の最後の絵を書き出す(見た目の確認用。声は使わない)。"""
    d = os.path.join(OUT, "stills")
    os.makedirs(d, exist_ok=True)
    for i, (fn, anim, sec, meta) in enumerate(plan):
        if isinstance(fn, WithAudio):
            fn, anim = fn.make(sec - 1.0, 0.35)
        fn(max(anim, sec) + 5).save(os.path.join(d, f"{i:03d}.png"))
    print("stills:", d)


def main():
    os.makedirs(OUT, exist_ok=True)
    plan = build_plan()
    if "--script" in sys.argv:
        total = write_script(plan)
        print(f"台本：{SCRIPT_MD}(約{int(total // 60)}分{int(total % 60):02d}秒、{len(plan)}場面、目安)")
        return
    if "--stills" in sys.argv:
        stills(plan)
        return
    check_voices(plan)
    import numpy as np
    import soundfile as sf
    from narrate import RATE
    LEAD, TAIL = 0.35, 0.55
    voices, new_plan = [], []
    for i, (fn, anim, sec, meta) in enumerate(plan):
        v = cs.voice_for(i, meta[2], os.path.join(OUT, "voice"))
        sec = max(anim + 0.3 if anim else 2.0, LEAD + len(v) / RATE + TAIL)
        if "出来事カード" in meta[0]:
            sec = max(sec, Card.ANIM_END + 0.8)
        if isinstance(fn, WithAudio):
            fn, anim = fn.make(len(v) / RATE, LEAD)
            sec = max(sec, anim + 0.3)
        voices.append(v)
        new_plan.append((fn, anim, sec, meta))
        print(f"声 {i + 1:3d}/{len(plan)} {len(v) / RATE:5.1f}秒 {meta[0]}", flush=True)
    plan = new_plan
    total = write_script(plan)
    print(f"台本：{SCRIPT_MD}(約{int(total // 60)}分{int(total % 60):02d}秒、{len(plan)}場面)")
    if "--voice" in sys.argv:
        parts = []
        for v, (_, _, sec, _) in zip(voices, plan):
            a = np.zeros(int(round(sec * RATE)), dtype="float32")
            vv = v[: max(0, len(a) - int(LEAD * RATE))]
            a[int(LEAD * RATE): int(LEAD * RATE) + len(vv)] = vv
            parts.append(a)
        wav = os.path.join(OUT, "narration.wav")
        sf.write(wav, np.concatenate(parts), RATE)
        mp3 = os.path.join(OUT, "ofuse_narration.mp3")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                        "-ar", "48000", "-b:a", "192k", mp3], check=True)
        print("音声:", mp3)
        return

    seg_dir = os.path.join(OUT, "_seg")
    os.makedirs(seg_dir, exist_ok=True)
    parts, audio = [], []
    for i, (fn, anim, sec, (name, _, _)) in enumerate(plan):
        mp4 = os.path.join(seg_dir, f"{i:03d}.mp4")
        cw.clip(fn, min(anim, sec), sec, mp4, os.path.join(seg_dir, "_frames"))
        parts.append(mp4)
        real = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4],
                                    capture_output=True, text=True).stdout)
        n = int(round(real * RATE))
        a = np.zeros(n, dtype="float32")
        v = voices[i][: max(0, n - int(LEAD * RATE))]
        a[int(LEAD * RATE): int(LEAD * RATE) + len(v)] = v
        audio.append(a)
        print(f"{i + 1:3d}/{len(plan)} {name}", flush=True)
    lst = os.path.join(seg_dir, "list.txt")
    with open(lst, "w") as f:
        for p in parts:
            f.write(f"file '{os.path.abspath(p)}'\n")
    silent = os.path.join(seg_dir, "video.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent], check=True)
    wav = os.path.join(OUT, "narration.wav")
    sf.write(wav, np.concatenate(audio), RATE)
    out = os.path.join(OUT, "ofuse_story_draft.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", wav, "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-ar", "48000", "-c:a", "aac", "-b:a", "160k", "-shortest", out], check=True)
    shutil.rmtree(seg_dir)
    print("done:", out)


if __name__ == "__main__":
    sys.exit(main())
