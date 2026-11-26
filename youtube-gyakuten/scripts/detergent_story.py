"""液体洗剤は進化の証？ 物語版：洗剤の売り場の「政権交代」を、物語・議席カード・議席でつなぐ(新常識クロニクル 洗剤編)。

  .venv/bin/python scripts/detergent_story.py           -> output/detergent_story/detergent_story_draft.mp4(ナレーションつき)
  .venv/bin/python scripts/detergent_story.py --script  -> content/detergent_war_story.md の表(台本)だけ作り直す
  .venv/bin/python scripts/detergent_story.py --voice   -> 声と台本だけ(映像は作らない)
  .venv/bin/python scripts/detergent_story.py --stills  -> 各場面の静止画だけ(output/detergent_story/stills/)

お布施の回(ofuse_story.py)と同じ型。違いは、2つの派が「液体派(オレンジ)」と「粉派(青)」であること、
議席が粉と液体の生産量の割合をもとにした目安であること(2003年=液体12、2018年=液体78 が実際の数字。途中は演出)。
イラストは scripts/detergent_art.py。
"""
import os
import re
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frames  # noqa: E402
from frames import BAD, GOOD, INK, SUB, TRIM, W, WHITE, arrow, font, panel, stage, text  # noqa: E402
from motion import Card, blank, out_back, parliament_frame, seg  # noqa: E402
import coffee_war as cw  # noqa: E402
from coffee_war import B, G  # noqa: E402
import coffee_story as cs  # noqa: E402
from coffee_story import WithAudio, chapter_start_frame, chip, story_frames, words, year_tag  # noqa: E402
import detergent_art as da  # noqa: E402
from detergent_art import (gel_box, neo_bottle, powder_box, soap_bar, washer, white_shirt, pct_bars, ton_bars,  # noqa: E402
                           fleece, nanox_bottle, spoon)
from thumbnail import EPISODES, series_card  # noqa: E402
import narrate  # noqa: E402

frames.LBL[:] = ["液体派", "粉派"]   # 左=オレンジ=液体派、右=青=粉派。議席の数は液体派の議席
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "output", "detergent_story")
SCRIPT_MD = os.path.join(HERE, "..", "content", "detergent_war_story.md")
EPISODE = "detergent_war"
EPISODES.setdefault(EPISODE, ("液体洗剤は進化の証？", "「粉派」vs「液体派」シェア争いの行方", "液体派", "粉派"))

# この回で読み間違えやすい語(この回だけで足す。他の回の声のキャッシュは変わらない)
narrate.MM_DICT += ["粉派/こなは", "液体派/えきたいは", "粉/こな", "固形/こけい", "石けん/せっけん", "皮脂/ひし",
                    "漂白剤/ひょうはくざい", "合成繊維/ごうせいせんい", "肌着/はだぎ", "銀座/ぎんざ", "高濃縮/こうのうしゅく",
                    "濃縮/のうしゅく", "高濃度/こうのうど", "黒ずみ/くろずみ", "型くずれ/かたくずれ", "色あせ/いろあせ",
                    "辿ります/たどります", "ドラム式/ドラムしき", "共働き/ともばたらき", "生産量/せいさんりょう",
                    "販売量/はんばいりょう", "政権交代/せいけんこうたい", "主役/しゅやく", "得意分野/とくいぶんや",
                    "泥だらけ/どろだらけ", "泥汚れ/どろよごれ", "泥/どろ", "汚れ/よごれ", "大ヒット/だいヒット",
                    "公認会計士/こうにんかいけいし", "司法試験/しほうしけん", "最難関/さいなんかん", "手ごわい/てごわい",
                    "見立てます/みたてます", "目安/めやす", "演出/えんしゅつ", "売り場/うりば", "ひと粒/ひとつぶ",
                    "酵素/こうそ", "注ぐ/そそぐ", "賢い/かしこい", "一方/いっぽう"]
narrate.NUM_STYLE = "dict"
narrate.ICHINICHI_PAUSE = 0.03
narrate.PAUSE_SHORT = 0
narrate.PAUSE_QUOTE_HA = 0
narrate.TEXT_READ += [("下が", "さが"),
                      ("司法試験vs公認会計士", "司法試験バーサス公認会計士"),
                      ("1994年度", "せんきゅうひゃくきゅうじゅうよねんど"),   # 4で終わる年は かなで(全回共通の決まり)
                      ("GAP", "ギャップ"),
                      ("アタックネオ", "アタック、ネオ"),
                      ("88議席", "はちじゅう<#0.05#>はち議席"), ("78議席", "ななじゅう<#0.05#>はち議席")]
# 「8」は「ジュウ」「ヒャク」のすぐあとだと濁るので、ごく短い間をはさむ(赤ワインの回と同じ)
cs.VOICE_FIX[:0] = [("2018年", "ニセンジュウ<#0.05#>ハチネン"), ("1998年", "センキュウヒャクキュウジュウ<#0.05#>ハチネン")]

_voice_for = cs.voice_for


def _calm_voice_for(i, narr, cache, emotion=None, fresh=False):
    return _voice_for(i, narr, cache, emotion=emotion or ("calm" if "逆転です" in narr else None), fresh=fresh)


cs.voice_for = _calm_voice_for
cs.STEP_COLORS.update({"1度目の逆転": INK, "粉の得意分野": BAD, "粉の黄金時代": BAD, "服が変わる": INK, "データ": INK,
                       "アタックNeo": GOOD, "液体の強み": GOOD, "トップNANOX": GOOD, "第3の洗剤": INK,
                       "ドラム式説": INK, "反論": BAD, "服の変化説": GOOD, "粉の今": BAD})


def E(f):
    return f


# ---------- 議席カード ----------
# (年, 国, 種類, 見出し, データ3つ, ピクトグラム, 前の液体派の議席, 後の議席, 速報の見出し, 出典)
def p01(d):
    fleece(d, 260, 690, 190)
    arrow(d, 420, 500, 690)
    pct_bars(d, 600, 790, [("1994年度", 25.6, (190, 196, 210)), ("最近", 49.6, GOOD)], h=180, bw=150, gap=80)


def p02(d):
    neo_bottle(d, 300, 690, 95)
    text(d, (600, 690), "約2.5倍に濃縮", 64, GOOD, anchor="mm")
    text(d, (960, 690), "すすぎ1回", 52, INK, anchor="mm")


def p03(d):
    # 前の年を1とした伸び(数字は出さず、棒の高さだけ)
    for i, (lab, v, c) in enumerate((("2009年", 1.0, (190, 196, 210)), ("2010年", 1.39, GOOD))):
        x = 260 + i * 240
        d.rounded_rectangle([x, 790 - 120 * v, x + 150, 790], radius=12, fill=c, outline=INK, width=5)
        text(d, (x + 75, 800), lab, 30, da.SUB_INK, heavy=False, anchor="ma")
    d.line([(230, 790), (680, 790)], fill=INK, width=4)
    text(d, (880, 690), "+39%", 110, GOOD, anchor="mm")


def p04(d):
    neo_bottle(d, 330, 690, 90)
    text(d, (560, 690), ">", 110, INK, anchor="mm")
    powder_box(d, 790, 700, 160)


def p05(d):
    ton_bars(d, 200, 795, [("粉 2003", 65.6, BAD), ("液体 2003", 9.2, GOOD), ("粉 2018", 15.7, BAD), ("液体 2018", 56.3, GOOD)],
             66, h=165, bw=150, gap=60)


EVENTS = [
    ("1998〜2008", "日本", "暮らしの変化", [[("合成繊維の服", G), ("が", INK)], [("およそ", INK), ("半分", G), ("に", INK)]],
     [("1994年度", "25.6%"), ("最近", "49.6%"), ("服", "フリース・発熱する肌着")], p01, 12, 18,
     "服が変わる", "出典：家庭系衣類廃棄物の繊維組成(J-STAGE 廃棄物資源循環学会誌 34巻3号)"),
    ("2009", "日本", "大きな新商品", [[("超コンパクトの", INK)], [("液体", G), ("が登場", INK)]],
     [("商品", "花王 アタックNeo"), ("濃縮", "約2.5倍"), ("すすぎ", "1回")], p02, 18, 33,
     "高濃縮の液体が登場", "出典：家電Watch 2009年7月10日(花王の発表)"),
    ("2010", "日本", "大きな伸び", [[("液体の売れ行き", G)], [("前の年より", INK), ("+39%", G)]],
     [("ライバル", "ライオン トップNANOX"), ("発売", "2010年1月"), ("伸び", "+39%")], p03, 33, 43,
     "液体が大きく伸びる", "出典：ダイヤモンド・オンライン/家電Watch 2009年11月18日"),
    ("2011", "日本", "逆転", [[("液体", G), ("が", INK), ("粉", B), ("を", INK)], [("初めて", INK), ("上回る", G)]],
     [("販売量", "液体 > 粉"), ("金額", "液体 > 粉"), ("背景", "高濃縮の液体")], p04, 43, 53,
     "液体が粉を上回る", "出典：ダイヤモンド・オンライン/BusinessPlus"),
    ("2018", "日本", "生産量の割合", [[("液体", G), ("は", INK), ("粉", B), ("の", INK)], [("3倍以上", G)]],
     [("液体", "9.2万t→56.3万t"), ("粉", "65.6万t→15.7万t"), ("液体", "15年で6倍以上")], p05, 53, 78,
     "液体が78議席", "出典：日本石鹸洗剤工業会の統計(2003年・2018年の生産量)"),
]


def delta_label(before, after):
    diff = after - before
    return f"{frames.LBL[0] if diff > 0 else frames.LBL[1]} +{abs(diff)}議席"


# ---------- 場面 ----------
SCENES = [
    ("hook", "洗濯洗剤、いま使っているのは、粉ですか？ 液体ですか？ 2003年、液体の洗剤は、粉の7分の1ほどしか作られていませんでした。それが2018年には、粉の3倍以上。わずか15年で、立場がひっくり返ったんです。"),
    ("title", "液体は、洗う力で粉に勝ったのか。それとも、別の理由があるのか。洗剤の売り場で起きた政権交代を、データで読み解きます。新常識クロニクル、今日のテーマは「液体洗剤は進化の証？」です。"),
    ("rules_intro", "今回は、洗剤の売り場を選挙に見立てます。議席は100。粉派の色は青、液体派の色はオレンジです。議席は、粉と液体の生産量の割合をもとにした目安で、途中の動きは演出です。"),
    ("start_seats", "スタートの2003年は、粉派が88議席、液体派が12議席。ここから、何が議席を動かしたのかを追いかけます。"),
    ("chapter_start", "それでは、行ってみましょう！第1話。実は洗剤の世界では、前にも一度、政権交代が起きています。", "第1話", "1度目の政権交代"),

    # 第1話 粉の時代
    ("story", 1, "1度目の逆転", "1963年 粉の洗剤の生産量が、固形石けんを上回った",
     [E(lambda d: year_tag(d, 960, 280, "1963年")), E(lambda d: soap_bar(d, 480, 520, 330)),
      E(lambda d: words(d, 480, 720, "固形石けん", 52, da.SUB_INK)), E(lambda d: arrow(d, 760, 860, 520)),
      E(lambda d: washer(d, 1120, 500, 230, drum=False)), E(lambda d: powder_box(d, 1460, 520, 230)),
      E(lambda d: words(d, 1290, 740, "粉の洗剤が主役に", 56, BAD))],
     "1963年。粉の洗剤の生産量が、固形の石けんを初めて上回りました。電気洗濯機が家庭に広がり、水に溶けやすい粉が、洗濯の主役になったんです。"),
    ("story", 1, "粉の得意分野", "粉:アルカリ剤・酸素系漂白剤を入れやすい → 泥・皮脂汚れに強い",
     [E(lambda d: powder_box(d, 520, 510, 300)), E(lambda d: chip(d, 1250, 330, "アルカリ剤", BAD, 56)),
      E(lambda d: chip(d, 1250, 470, "酸素系漂白剤", BAD, 56)), E(lambda d: arrow(d, 860, 950, 600)),
      E(lambda d: words(d, 1250, 640, "泥・皮脂汚れに強い", 64, INK))],
     "それから40年、粉は洗剤の王様でした。粉には、汚れを浮かせるアルカリ剤や、酸素の力で落とす漂白剤を入れやすい。泥だらけの靴下も、えりの皮脂汚れも、粉の得意分野です。"),
    ("story", 1, "粉の黄金時代", "1987年4月 花王「アタック」発売。「スプーン1杯で驚きの白さ」。酵素入りの小型濃縮の粉",
     da.attack_scene_elements(),
     "1987年には、花王の「アタック」が登場します。スプーン1杯で驚きの白さ。箱がぐっと小さくなった酵素入りの粉は、大ヒットしました。この時点では、粉の時代がまだまだ続くと思われていたんです。"),

    # 第2話 服が変わる
    ("chapter_start", "第2話。次の変化は、洗剤より先に、クローゼットの中で起きていました。", "第2話", "クローゼットの変化"),
    ("story", 2, "服が変わる", "1995年 GAP上陸/1998年ごろ ユニクロのフリースが大ブーム/2003年 発熱する肌着/2008年 H&M 銀座に上陸",
     da.fashion_scene_elements(),
     "1995年、アメリカのGAPが日本に上陸。1998年ごろには、ユニクロの手ごろなフリースが大ブームに。2003年には、汗を熱に変える肌着が登場します。そして2008年、海外のファストファッションが銀座に上陸。安くて色あざやかな服を、気軽に買いかえる時代が始まりました。"),
    ("story", 2, "データ", "家庭から捨てられた服の合成繊維の割合 1994年度 25.6% → 最近 49.6%",
     [E(lambda d: fleece(d, 480, 500, 300)), E(lambda d: words(d, 480, 720, "ポリエステルなど", 48, da.SUB_INK)),
      E(lambda d: pct_bars(d, 1000, 740, [("1994年度", 25.6, (190, 196, 210)), ("最近", 49.6, GOOD)], h=380, bw=200, gap=140)),
      E(lambda d: words(d, 1340, 280, "服のおよそ半分が合成繊維", 52, GOOD))],
     "実際、家庭から捨てられた服を調べると、ポリエステルなどの合成繊維の割合は、1994年度の25.6%から、最近の調査では49.6%に。服のおよそ半分が、合成繊維になったんです。"),
    ("card", 1, "服の変化で、液体派が6議席。"),

    # 第3話 液体の新人
    ("chapter_start", "第3話。2009年、液体派に強力な新人が現れます。", "第3話", "液体の新人"),
    ("story", 3, "アタックNeo", "2009年8月 花王「アタックNeo」発売。約2.5倍に濃縮・すすぎ1回でOK・400gで従来の液体1kg分",
     da.neo_scene_elements(),
     "その名は、花王の「アタックネオ」。2009年8月に発売された、超コンパクトの液体洗剤です。洗剤の中の水分を減らして、約2.5倍に濃縮。400グラムのボトルで、それまでの液体洗剤1キロ分も洗えて、すすぎは1回でいい。"),
    ("story", 3, "液体の強み", "少ない量・小さいボトル・溶け残りなし・すすぎ1回で節水と時短",
     [E(lambda d: neo_bottle(d, 480, 480, 180)), E(lambda d: chip(d, 1250, 300, "量って注ぐだけ", GOOD, 54)),
      E(lambda d: chip(d, 1250, 430, "こぼれない・溶け残らない", GOOD, 54)), E(lambda d: chip(d, 1250, 560, "すすぎ1回で節水・時短", GOOD, 54)),
      E(lambda d: words(d, 1250, 720, "共働きの時代にぴったり", 56, INK))],
     "キャップで量って注ぐだけ。粉のようにこぼれたり、溶け残ったりもしません。すすぎが1回で済めば、水も時間も節約できます。共働きの家が増えた時代に、ぴったりの洗剤でした。"),
    ("card", 2, "液体派が、一気に15議席。"),
    ("story", 3, "トップNANOX", "2010年1月 ライオン「トップNANOX」発売。においの元の皮脂汚れを落とす高濃度の液体",
     da.nanox_scene_elements(),
     "ライバルも黙っていません。2010年1月、ライオンが「トップナノックス」を発売。においの元になる皮脂汚れを落とす、高濃度の液体洗剤です。"),
    ("card", 3, "各社の高濃縮の液体がそろった2010年、液体の売れ行きは、前の年より39%も伸びました。液体派が43議席に。"),
    ("seats", 4, "そして2011年、販売量でも金額でも、液体が粉を上回ります。液体派が過半数。逆転です！"),
    ("story", 3, "第3の洗剤", "2014年 ジェルボールが登場。粉・液体に続く「第3の洗剤」(P&G「アリエール ジェルボール」など)",
     da.gel_scene_elements(),
     "その後、ひと粒ずつ洗濯機に入れるだけの、ジェルボールも登場します。粉、液体に続く、第3の洗剤です。"),
    ("card", 5, "それでも液体の勢いは止まらず、2018年には、液体派が78議席、粉派が22議席。液体の生産量は、15年で6倍以上になりました。"),

    # 第4話 なぜ液体は勝った？
    ("chapter_start", "第4話。では、液体はなぜ、ここまで勝ったのでしょうか。よく言われる理由は、ドラム式洗濯機です。", "第4話", "なぜ液体は勝った？"),
    ("story", 4, "ドラム式説", "ドラム式は水が少ない → 粉が溶け残りやすい → 液体向き(この理由を挙げる研究もある)",
     [E(lambda d: washer(d, 480, 500, 300, drum=True)), E(lambda d: chip(d, 1250, 320, "使う水が少ない", INK, 54)),
      E(lambda d: chip(d, 1250, 460, "粉が溶け残りやすい", BAD, 54)), E(lambda d: chip(d, 1250, 600, "だから液体？", GOOD, 54)),
      E(lambda d: words(d, 1250, 740, "この理由を挙げる研究もある", 44, da.SUB_INK))],
     "ドラム式は、使う水が少ない。水が少ないと、粉は溶け残りやすい。だから液体が向いている、という説です。液体が増えた理由に、ドラム式の広がりを挙げる研究もあります。"),
    ("story", 4, "反論", "ドラム式の普及率 全体18%/共働き子育て世帯28%",
     [E(lambda d: washer(d, 330, 470, 190, drum=True)),
      E(lambda d: pct_bars(d, 620, 740, [("ドラム式 全体", 18, BAD), ("共働き子育て", 28, BAD), ("液体 2018", 78, GOOD)],
                           h=400, bw=190, gap=110)),
      E(lambda d: words(d, 960, 280, "ドラム式だけでは説明しきれない", 56, INK))],
     "ところが、ドラム式を使っている家は、全体で18%。共働きで子育て中の家でも28%です。ドラム式の家が全部液体に変えたとしても、液体が粉の3倍以上という差は、説明しきれません。"),
    ("story", 4, "服の変化説", "合成繊維・色柄物 → 色あせ・型くずれを防ぐやさしさ/冷たい水にも溶ける",
     [E(lambda d: fleece(d, 380, 480, 240)), E(lambda d: white_shirt(d, 650, 500, 200)),
      E(lambda d: chip(d, 1300, 320, "汗や軽い汚れが中心", INK, 52)), E(lambda d: chip(d, 1300, 460, "色あせ・型くずれを防ぐ", GOOD, 52)),
      E(lambda d: chip(d, 1300, 600, "冷たい水にも溶ける", GOOD, 52)), E(lambda d: neo_bottle(d, 900, 520, 110))],
     "そこで浮かぶのが、もう一つの説。服が変わったから、洗剤が変わった。毎日着がえる合成繊維の服は、泥よりも汗や軽い汚れが中心。強い洗浄力より、色あせや型くずれを防ぐやさしさが求められます。冷たい水にも溶けやすい液体は、こうした服と相性がいいんです。"),
    ("final", "最終結果、液体派が78議席。ただ、これは生産量の話です。服の変化と洗濯機の変化、どちらがどれだけ効いたのかは、まだ決着がついていません。"),
    ("story", 4, "粉の今", "泥汚れ・えりそでの黒ずみ → 今も粉が強い",
     [E(lambda d: powder_box(d, 500, 510, 280)), E(lambda d: chip(d, 1250, 330, "泥汚れ", BAD, 56)),
      E(lambda d: chip(d, 1250, 470, "えり・そでの黒ずみ", BAD, 56)),
      E(lambda d: words(d, 1250, 650, "粉派の22議席は手ごわい汚れ担当", 50, INK))],
     "それに、粉が負けたわけではありません。泥汚れや、えりやそでの黒ずみには、アルカリ剤や漂白剤を入れやすい粉が、今でも強い。粉派の22議席は、手ごわい汚れの担当として、しっかり残っています。"),
    ("summary", "今日のまとめです。液体洗剤は、洗う力が進化したというより、私たちの服と暮らしに合わせて進化した洗剤。ふだんの服や色柄物には液体、泥汚れや白いタオルには粉。使い分けるのが、いちばん賢いのかもしれません。洗い方は、服のタグの表示も確かめてくださいね。",
     ["液体洗剤は", "ふだんの服", "泥汚れ", "洗い方は"]),
    ("next", "次回のテーマは「司法試験vs公認会計士」。最難関同士の資格試験の逆転の歴史を辿ります。"),
    ("outro", "新常識クロニクルでは、これからも、健康や暮らしの常識の移り変わりを、データで分析していきます。次に取り上げてほしいテーマがあれば、ぜひコメントで教えてください。チャンネル登録と高評価も、よろしくお願いします！"),
]

# 台本の表に出すテロップ(story 以外の場面)
TELOP = {"hook": ("つかみ", "2003年 液体は粉の約7分の1 → 2018年 粉の3倍以上"),
         "title": ("タイトル", "新常識クロニクル:液体洗剤は進化の証？"),
         "rules_intro": ("ルール説明", "100議席・粉派(青) vs 液体派(オレンジ)・議席は生産量の割合をもとにした目安"),
         "start_seats": ("ルール説明", "2003年 粉派88・液体派12")}


# ---------- この回だけの画面 ----------
def at_maker(narr, alen, lead):
    return lambda k: lead + narr.index(k) / len(narr) * alen  # noqa: E731


def hook_maker(narr):
    """粉の箱と液体のボトルが出て「2003年 液体は粉の約7分の1」→「2018年 粉の3倍以上」→「15年で逆転」の帯。"""
    def make(alen, lead):
        at = at_maker(narr, alen, lead)
        t0, t1, t2, t3 = at("洗濯洗剤") - 0.2, at("2003年"), at("それが"), at("わずか")

        def frame(t):
            im = stage()[0].convert("RGBA")
            lay = blank()
            dd = ImageDraw.Draw(lay)
            k0 = seg(t, t0, t0 + 0.4)
            if k0 > 0:
                sc = 0.6 + 0.4 * out_back(k0)
                powder_box(dd, 600, 560, 300 * sc)
                neo_bottle(dd, 1320, 560, 150 * sc)
            im.alpha_composite(lay)
            d = ImageDraw.Draw(im)
            if k0 > 0:
                text(d, (600, 810), "粉", 64, WHITE, anchor="mm")
                text(d, (1320, 810), "液体", 64, WHITE, anchor="mm")
            k1 = seg(t, t1, t1 + 0.4)
            if k1 > 0 and t < t2:
                chip(d, W / 2, 190, "2003年  液体は粉の約7分の1", BAD, int(60 * (0.6 + 0.4 * out_back(k1))))
            k2 = seg(t, t2, t2 + 0.4)
            if k2 > 0:
                chip(d, W / 2, 190, "2018年  液体は粉の3倍以上", GOOD, int(60 * (0.6 + 0.4 * out_back(k2))))
            k3 = seg(t, t3, t3 + 0.45)
            if k3 > 0:
                sc = 1.5 - 0.5 * out_back(k3)
                cx, cy = W / 2, 930
                bw, bh = 480 * sc, 70 * sc
                d.rounded_rectangle([cx - bw, cy - bh, cx + bw, cy + bh], radius=24 * sc, fill=GOOD, outline=WHITE,
                                    width=max(3, int(8 * sc)))
                text(d, (cx, cy), "わずか15年で逆転", int(66 * sc), WHITE, anchor="mm")
            return im.convert("RGB")
        return frame, t3 + 0.8
    return WithAudio(make)


def rules_intro_frame(t):
    im = parliament_frame("", "洗剤の売り場を選挙に見立てる", 50, 50, t, tag="見方")
    d = ImageDraw.Draw(im)
    for x, lab, c in ((W / 2 - 400, "液体の洗剤", GOOD), (W / 2 + 400, "粉の洗剤", BAD)):
        k = seg(t, 0.8, 1.2)
        if k > 0:
            chip(d, x, 300, lab, c, int(46 * (0.6 + 0.4 * out_back(k))))
    a = seg(t, 1.4, 1.8)
    if a > 0:
        text(d, (W / 2, 1030), "※ 議席は粉と液体の生産量の割合をもとにした目安。途中の動きは演出です", 34,
             tuple(int(200 * a + 30 * (1 - a)) for _ in range(3)), heavy=False, anchor="mm")
    return im


def start_seats_frame(t):
    return parliament_frame("2003年", "スタート(生産量の割合)", 50, 12, t, tag="スタート")


def summary_maker(narr, keys):
    items = [("液体洗剤は", "服と暮らしに合わせた進化", GOOD), ("ふだんの服・色柄物には", "液体", GOOD),
             ("泥汚れ・白いタオルには", "粉", BAD), ("洗い方は", "服のタグの表示も確かめる", INK)]

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


NEXT_TITLE = "司法試験vs公認会計士"


def next_frame(t):
    im, d = stage()
    text(d, (W / 2, 260), "次回のテーマ", 70, TRIM, anchor="mm")
    k = out_back(seg(t, 0.3, 0.8))
    if k > 0:
        sc = 0.6 + 0.4 * k
        chip(d, W / 2 - 400, 560, "司法試験", GOOD, int(90 * sc))
        chip(d, W / 2 + 400, 560, "公認会計士", BAD, int(90 * sc))
        text(d, (W / 2, 560), "vs", int(90 * sc), TRIM, anchor="mm")
    a = seg(t, 0.9, 1.3)
    if a > 0:
        text(d, (W / 2, 850), "最難関同士の資格試験、逆転の歴史", 72, tuple(int(255 * a + 30 * (1 - a)) for _ in range(3)), anchor="mm")
    return im


TOPICS = ["司法試験vs公認会計士", "サウナは長生きのもと？", "朝ごはんは食べるべき？", "塩は減らすほどいい？", "牛乳は体にいい？", "人工甘味料は安全？"]


def outro_frame(t):
    im, d = stage()
    k = out_back(seg(t, 0.2, 0.7))
    if k > 0:
        text(d, (W / 2, 230), "新常識クロニクル", int(120 * (0.5 + 0.5 * k)), WHITE, anchor="mm")
    a = seg(t, 0.6, 1.0)
    if a > 0:
        text(d, (W / 2, 350), "これからも、常識の移り変わりを分析します", 56, tuple(int(TRIM[j] * a + 30 * (1 - a)) for j in range(3)), anchor="mm")
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


FINAL_NOTE = "議席は2018年の生産量の割合。服と洗濯機、どちらがどれだけ効いたかは未決着"


# ---------- 組み立て ----------
def dur(narr):
    return max(3.0, len(narr) / 8.0 + 0.8)


def card_of(idx):
    year, country, kindx, title, facts, picto, before, after, headline, source = EVENTS[idx - 1]
    rows = [[(s, cw.color_of(c)) for s, c in row] for row in title]
    return Card(year, country, kindx, rows, facts, picto, before, after, delta_label(before, after), source)


def build_plan():
    """(描く関数, 動く秒数, 合計秒数, 台本の行) のリスト。"""
    plan, last_chapter = [], None
    for sc in SCENES:
        kind, narr = sc[0], sc[-1] if sc[0] not in ("summary", "chapter_start") else sc[1]
        if kind == "hook":
            plan.append((hook_maker(narr), 0, dur(narr), TELOP[kind] + (narr,)))
        elif kind == "title":
            img = os.path.join(OUT, "00_title.png")
            series_card(*EPISODES[EPISODE]).save(img)
            plan.append(((lambda im: lambda t: im)(Image.open(img)), 0, dur(narr), TELOP[kind] + (narr,)))
        elif kind == "rules_intro":
            plan.append((rules_intro_frame, 1.9, dur(narr), TELOP[kind] + (narr,)))
        elif kind == "start_seats":
            plan.append((start_seats_frame, 2.6, dur(narr), TELOP[kind] + (narr,)))
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
                         (f"議席カード {e[0]}", f"液体派 {e[6]}→{e[7]}", narr)))
        elif kind == "seats":
            last_chapter = None
            year, _, _, _, _, _, before, after, headline, _ = EVENTS[sc[1] - 1]
            plan.append(((lambda y, h, b, a: lambda t: parliament_frame(y, h, b, a, t))(year, headline, before, after),
                         2.6, max(dur(narr), 3.6), (f"開票速報 {year}", f"液体派 {before}→{after} 逆転！", narr)))
        elif kind == "final":
            last_chapter = None
            plan.append((lambda t: cw.final_frame(EVENTS[-1][7], t, note=FINAL_NOTE), 2.6, dur(narr),
                         ("最終結果", "液体派78・粉派22(2018年)", narr)))
        elif kind == "summary":
            plan.append((summary_maker(sc[1], sc[2]), 0, dur(sc[1]), ("まとめ", "ふだんの服・色柄物=液体/泥汚れ・白いタオル=粉", sc[1])))
        elif kind == "next":
            plan.append((next_frame, 1.3, dur(narr), ("次回予告", "司法試験 vs 公認会計士", narr)))
        elif kind == "outro":
            plan.append((outro_frame, 4.2, dur(narr), ("エンディング", "チャンネル登録・今後の論争", narr)))
    return plan


def write_script(plan, voiced=False):
    """台本(content/detergent_war_story.md)の表と合計だけを作り直す。表の下(議席の推移・確認リスト)は手書きのまま残す。"""
    total = 0.0
    rows = []
    for _, _, sec, (name, tl, narr) in plan:
        m, s = divmod(int(total), 60)
        rows.append(f"| {m}:{s:02d} | {name} | {tl} | {narr} |")
        total += sec
    m, s = divmod(int(total), 60)
    md = open(SCRIPT_MD, encoding="utf-8").read()
    h = "| 時間 | 場面 | 画面のテロップ・内容 | ナレーション |\n|---|---|---|---|\n"
    i, j = md.index(h) + len(h), md.index("\n## 議席の推移")
    note = "合成した声の長さ" if voiced else "目安"
    md = md[:i] + "\n".join(rows) + f"\n\n合計:約{m}分{s:02d}秒({note})\n" + md[j:]
    md = re.sub(r"ナレーション合計:約[\d,]+字", f"ナレーション合計:約{sum(len(p[3][2]) for p in plan):,}字", md)
    md = md.replace("状態:初稿(手書き)。動画にするときは `scripts/wine_story.py` をコピーして `scripts/detergent_story.py` を作り、この表を SCENES に移す。",
                    "状態:初稿。表は `scripts/detergent_story.py` の SCENES から自動で作っています(台本を直すときは SCENES を直す)。")
    with open(SCRIPT_MD, "w", encoding="utf-8") as f:
        f.write(md)
    base = SCRIPT_MD.replace("_story.md", "")
    t, marked, plain = 0.0, [], []
    for k, (_, _, sec, (name, _, narr)) in enumerate(plan, 1):
        mm, ss = divmod(int(t), 60)
        marked.append(f"【{k:02d}】{mm}:{ss:02d} {name}\n{narr}\n")
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
        if "議席カード" in meta[0]:
            sec = max(sec, Card.ANIM_END + 0.8)
        if isinstance(fn, WithAudio):
            fn, anim = fn.make(len(v) / RATE, LEAD)
            sec = max(sec, anim + 0.3)
        voices.append(v)
        new_plan.append((fn, anim, sec, meta))
        print(f"声 {i + 1:3d}/{len(plan)} {len(v) / RATE:5.1f}秒 {meta[0]}", flush=True)
    plan = new_plan
    total = write_script(plan, voiced=True)
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
        mp3 = os.path.join(OUT, "detergent_narration.mp3")
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
    out = os.path.join(OUT, "detergent_story_draft.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", wav, "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-ar", "48000", "-c:a", "aac", "-b:a", "160k", "-shortest", out], check=True)
    shutil.rmtree(seg_dir)
    print("done:", out)


if __name__ == "__main__":
    sys.exit(main())
