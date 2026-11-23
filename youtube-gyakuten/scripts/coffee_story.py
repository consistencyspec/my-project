"""コーヒー10年戦争 物語版：主な研究を「なぜ調べた→どうやって→クイズ→結果」の物語にして、長くつなげる。

  .venv/bin/python scripts/coffee_story.py   -> output/coffee_story/coffee_story_draft.mp4(ナレーションつき)
  python3 scripts/coffee_story.py --script -> content/coffee_war_story.md(台本)だけ作り直す

場面の長さは、合成したナレーション(Kokoro)の長さから決める。
"""
import os
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frames import BAD, GOOD, INK, LW, PANEL, SUB, TRIM, W, H, WHITE, arrow, bean, font, heart, line, meter, mug, panel, stage, text  # noqa: E402
from motion import Card, blank, out_back, out_cubic, parliament_frame, seg, with_alpha  # noqa: E402
import coffee_war as cw  # noqa: E402
import narrate  # noqa: E402

narrate.ICHINICHI_PAUSE = 0   # この回は「1日」のあとに間を置かない(2026-11-23 指示)
INTRO_EMOTION = "happy"       # 冒頭(番組紹介〜タイトル)は爽やかに
INTRO_SCENES = ("番組紹介", "オープニング", "タイトル")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "output", "coffee_story")
SCRIPT_MD = os.path.join(HERE, "..", "content", "coffee_war_story.md")
FPS = 30
SPEED = 8.0       # ナレーションの速さの目安(字/秒)。実際の長さは合成した声で決まる
CREAM = cw.CREAM
FADED = (205, 208, 216)


# ---------- 追加のピクトグラム ----------
def hospital(d, cx, cy, s):
    d.rounded_rectangle([cx - s * 0.5, cy - s * 0.4, cx + s * 0.5, cy + s * 0.5], radius=14, fill=WHITE, outline=INK, width=LW)
    d.rounded_rectangle([cx - s * 0.08, cy - s * 0.28, cx + s * 0.08, cy + s * 0.08], radius=4, fill=(220, 70, 70))
    d.rounded_rectangle([cx - s * 0.2, cy - s * 0.16, cx + s * 0.2, cy - s * 0.04], radius=4, fill=(220, 70, 70))
    d.rounded_rectangle([cx - s * 0.12, cy + s * 0.22, cx + s * 0.12, cy + s * 0.5], radius=6, fill=CREAM, outline=INK, width=6)


def cigarette(d, cx, cy, s):
    d.rounded_rectangle([cx - s * 0.5, cy - s * 0.07, cx + s * 0.3, cy + s * 0.07], radius=8, fill=WHITE, outline=INK, width=6)
    d.rounded_rectangle([cx + s * 0.3, cy - s * 0.07, cx + s * 0.5, cy + s * 0.07], radius=8, fill=(240, 150, 60), outline=INK, width=6)
    for i in range(2):
        x = cx + s * 0.42 + i * 22
        line(d, [(x, cy - s * 0.12), (x + 10, cy - s * 0.22), (x, cy - s * 0.32), (x + 10, cy - s * 0.42)], SUB, 6)


def magnifier(d, cx, cy, r):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(230, 240, 255), outline=INK, width=LW + 2)
    line(d, [(cx + r * 0.7, cy + r * 0.7), (cx + r * 1.5, cy + r * 1.5)], INK, LW + 8)


def dna(d, cx, cy, h):
    import math
    pts1, pts2 = [], []
    for i in range(41):
        t = i / 40
        y = cy - h / 2 + t * h
        x = math.sin(t * math.pi * 3) * h * 0.18
        pts1.append((cx + x, y))
        pts2.append((cx - x, y))
    for i in range(0, 41, 4):
        d.line([pts1[i], pts2[i]], fill=SUB, width=5)
    d.line(pts1, fill=GOOD, width=LW, joint="curve")
    d.line(pts2, fill=BAD, width=LW, joint="curve")


def phone(d, cx, cy, h, msg, color=GOOD):
    w = h * 0.52
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=w * 0.18, fill=WHITE, outline=INK, width=LW)
    bw = w * 0.82
    d.rounded_rectangle([cx - bw / 2, cy - h * 0.18, cx + bw / 2, cy + h * 0.1], radius=18, fill=color)
    fs = int(min(h * 0.085, h * 0.085 * (bw - 20) / max(1, d.textlength(msg, font=font(int(h * 0.085))))))
    text(d, (cx, cy - h * 0.04), msg, fs, WHITE, anchor="mm")


def watch(d, cx, cy, s):
    d.rounded_rectangle([cx - s * 0.18, cy - s * 0.6, cx + s * 0.18, cy + s * 0.6], radius=12, fill=SUB)
    d.rounded_rectangle([cx - s * 0.32, cy - s * 0.32, cx + s * 0.32, cy + s * 0.32], radius=20, fill=WHITE, outline=INK, width=LW)
    text(d, (cx, cy), "歩数", int(s * 0.16), INK, anchor="mm")


def patch(d, cx, cy, s):
    d.rounded_rectangle([cx - s * 0.5, cy - s * 0.22, cx + s * 0.5, cy + s * 0.22], radius=s * 0.2, fill=CREAM, outline=INK, width=LW)
    cw.ecg(d, cx - s * 0.4, cy, s * 0.8)


def sensor(d, cx, cy, r):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE, outline=INK, width=LW)
    d.ellipse([cx - r * 0.45, cy - r * 0.45, cx + r * 0.45, cy + r * 0.45], fill=(220, 70, 70))
    text(d, (cx, cy + r + 14), "血糖値", 28, INK, heavy=False, anchor="ma")


def chip(d, cx, cy, s, color, size=46):
    tw = d.textlength(s, font=font(size)) + size * 1.2
    d.rounded_rectangle([cx - tw / 2, cy - size * 0.85, cx + tw / 2, cy + size * 0.85], radius=size * 0.85, fill=color)
    text(d, (cx, cy), s, size, WHITE, anchor="mm")


def words(d, cx, cy, s, size=56, color=INK):
    text(d, (cx, cy), s, size, color, anchor="mm")


def flag_jp(d, cx, cy, s):
    d.rounded_rectangle([cx - s * 0.6, cy - s * 0.4, cx + s * 0.6, cy + s * 0.4], radius=10, fill=WHITE, outline=INK, width=6)
    d.ellipse([cx - s * 0.22, cy - s * 0.22, cx + s * 0.22, cy + s * 0.22], fill=(220, 50, 50))


def year_tag(d, cx, cy, y, color=INK):
    chip(d, cx, cy, y, color, 44)


# 要素は (描く関数) のリスト。順番にポンと出る。
E = lambda f: f  # noqa: E731


# ---------- 場面 ----------
# 種類：
#   ("story", 話数, 見出し, テロップ, [要素], ナレーション)
#   ("quiz", 話数, 問題, A, B, 正解(0/1), ナレーション)  → 問題の場面と、答えの場面の2つになる
#   ("card", 研究番号(1〜16), ナレーション)  → 研究カード
#   ("seats", 研究番号, ナレーション)        → 全画面の開票速報
#   ("headlines", ナレーション) / ("title", ナレーション) / ("rules", ナレーション) / ("final", ナレーション)
SCENES = [
    # 番組紹介(新常識クロニクルとは)。本題は30秒あまりから
    ("intro_myths", "「卵は1日1個まで」「1日1万歩」「朝ごはんはしっかり」。よく聞くこの話、いまの研究では、どうなっているんでしょう？",
     ["卵は1日1個まで", "1日1万歩", "朝ごはんはしっかり"]),
    ("intro_flip", "実は、研究の答えは、時代とともに少しずつ変わってきたんです。"),
    ("intro_logo", "新常識クロニクルでは、そんな論争の歴史を年表でたどりながら、いまどちらが優勢なのかを、データで楽しく見ていきます。"),
    ("headlines", "今回のテーマは、コーヒー。「長生きできる」という話もあれば、「体によくない」という話も。いったい、どっちなんでしょう？"),
    ("title", "題して、コーヒー10年戦争です。"),
    # ルール説明
    ("rules_intro", "この番組では、研究の歴史を選挙に見立てて見ていきます。議会の議席は全部で100。オレンジが「いい派」、青が「悪い派」です。スタートは50対50の互角。真ん中の天秤は、いまどちらが優勢かを表しています。"),
    ("rules", "新しい研究や発表が出るたびに、勝った側に議席が移ります。動く議席の数は、その研究の重みで決まります。WHOや国、裁判所などの公的な判断は15議席。たくさんの研究をまとめた分析は10議席。数十万人を何年も追いかけた調査は6議席。対象や条件が限られた結果は3議席です。",
     ["公的な判断", "まとめた分析", "数十万人", "条件が限られた"]),
    ("demo", "たとえば、数十万人の調査で「コーヒーは体にいい」という結果が出たら、6議席がいい派に移って、56対44。天秤も、いい派の側にぐっと傾きます。", 50, 56, "数十万人の調査で「体にいい」"),
    ("demo", "そして、負けていた側が逆転して過半数を取ると「逆転！」です。なお、議席はあくまで分かりやすくするための目安。最後に、本当に決着がついたのかどうかもお話しします。", 47, 53, "負けていた側が過半数を取ると"),
    ("chapter_start", "それでは、行ってみましょう！第1話。すべての始まりは、1981年のアメリカです。", "第1話", "すべての始まり"),

    # 第1話 1991
    ("story", 1, "はじまり", "1981年「膵臓がんと関係あり？」→ 1986年 同じチームが調べ直すと、はっきりせず",
     [E(lambda d: year_tag(d, 400, 360, "1981年")), E(lambda d: hospital(d, 400, 600, 240)),
      E(lambda d: arrow(d, 590, 690, 600)), E(lambda d: mug(d, 740, 500, 180, fill=CREAM)),
      E(lambda d: words(d, 1300, 470, "膵臓がんと関係あり？", 64, BAD)),
      E(lambda d: year_tag(d, 1300, 600, "1986年")), E(lambda d: words(d, 1300, 710, "調べ直すと、はっきりせず", 56, GOOD))],
     "物語の始まりは1981年。舞台は、アメリカのハーバード大学です。膵臓がんの患者さんはコーヒーをよく飲んでいた、という研究が大ニュースになります。ところが1986年、同じチームが調べ直すと、関係ははっきりしませんでした。"),
    ("story", 1, "それでも", "1991年 WHOの機関は「発がん性があるかもしれない」に分類",
     [E(lambda d: year_tag(d, 480, 360, "1991年")), E(lambda d: mug(d, 380, 470, 200, fill=CREAM)),
      E(lambda d: cw.warn(d, 1000, 580, 260)), E(lambda d: words(d, 1420, 520, "グループ2B", 70, BAD)),
      E(lambda d: words(d, 1420, 630, "可能性がある", 54))],
     "それでも1991年、WHOの機関は、コーヒーを「発がん性があるかもしれないもの」に分類します。この疑いは、25年も残ることになります。"),
    ("card", 1, "悪い派、いきなり15議席の大勝です。"),
    ("seats", 1, "悪い派65、いい派35。いい派は苦しいスタートです。"),

    # 2015 日本(短く)
    ("card", 2, "そこに日本から援軍が。2015年、日本人約9万人を追いかけた研究で、コーヒーをよく飲む人ほど死亡リスクが低いと報告されます。いい派、41議席まで回復。"),

    # 第2話 2016
    ("story", 2, "25年目の見直し", "2016年 WHOの機関が1,000以上の研究を見直した",
     [E(lambda d: year_tag(d, 480, 360, "2016年")), E(lambda d: cw.papers(d, 360, 480, 230, 5)),
      E(lambda d: magnifier(d, 760, 600, 100)), E(lambda d: words(d, 1330, 560, "1,000以上の研究", 72))],
     "そして2016年。WHOの機関は、25年ぶりにコーヒーを見直します。集めた研究は1,000以上。あの「疑い」は本物だったのでしょうか。"),
    ("story", 2, "疑いの正体", "疑いの正体はタバコ。コーヒーをよく飲む人ほど、タバコも吸っていた",
     [E(lambda d: mug(d, 330, 470, 220, fill=CREAM)), E(lambda d: words(d, 680, 600, "＋", 100)),
      E(lambda d: cigarette(d, 940, 600, 300)), E(lambda d: words(d, 1450, 540, "正体は", 64)),
      E(lambda d: words(d, 1450, 650, "タバコ", 110, GOOD))],
     "見直しで分かったのは、疑いの正体がタバコだったことです。昔は、コーヒーをよく飲む人ほど、タバコもよく吸っていました。その影響をきちんと差し引いていない研究が多かったんです。"),
    ("story", 2, "新しい火種", "ただし「65℃を超える熱すぎる飲み物」は「おそらく発がん性がある」に",
     [E(lambda d: cw.thermo(d, 480, 380, 380)), E(lambda d: words(d, 640, 560, "65℃超", 90, (220, 50, 50))),
      E(lambda d: words(d, 1320, 500, "南米のマテ茶", 54)), E(lambda d: words(d, 1320, 600, "イラン・中国などの研究", 54)),
      E(lambda d: words(d, 1320, 720, "→ 食道がん", 64, BAD))],
     "ただし、このとき新しい火種も生まれました。南米のマテ茶や、イランや中国などの研究から、65℃を超える熱すぎる飲み物は、食道がんの「おそらく原因」と判断されたんです。問題はコーヒーではなく、温度でした。"),
    ("card", 3, "差し引きで、いい派は12議席を取り戻します。"),
    ("seats", 3, "いい派53、悪い派47。いい派、ついに過半数。逆転です！"),

    # 2017 EPIC(カードだけ)
    ("card", 4, "2017年。ヨーロッパの研究チームは、飲み方の違う国でも同じ結果になるのかを確かめました。イタリアのエスプレッソ、北欧のドリップ。デンマークからイタリアまで10か国、約52万人を16年あまり追いかけると、どの国でも、よく飲む人ほど死亡リスクが低かったんです。いい派、59議席。"),
    ("card", 5, "同じ年、イギリスの研究チームが200以上の研究をまとめ、1日3〜4杯がいちばん好結果、と発表。ただし妊娠中だけは悪い結果でした。いい派、66議席。"),

    # 第3話 カリフォルニアの裁判
    ("story", 3, "訴えた", "2010年 小さな市民団体が、コーヒー会社など約90社を訴えた",
     [E(lambda d: year_tag(d, 480, 360, "2010年")), E(lambda d: bean(d, 420, 460, 230, fill=BAD)),
      E(lambda d: words(d, 760, 580, "→", 90)), E(lambda d: cw.crowd(d, 980, 440, 5, 2, 120, fill=FADED)),
      E(lambda d: words(d, 1250, 760, "約90社", 60, BAD))],
     "ここで悪い派が、思わぬところから反撃します。舞台はアメリカ、カリフォルニア州。2010年、小さな市民団体が、有名なコーヒーチェーンなど約90社を訴えたんです。"),
    ("story", 3, "理由は？", "焙煎でできる「アクリルアミド」。ポテトチップスやトーストにも含まれる",
     [E(lambda d: mug(d, 400, 470, 190, fill=(120, 80, 50))), E(lambda d: words(d, 960, 520, "アクリルアミド", 80, BAD)),
      E(lambda d: words(d, 960, 640, "焙煎・揚げる・焼くとできる", 48)),
      E(lambda d: cw.label(d, 1350, 470, 300, 120, "警告表示"))],
     "理由は、アクリルアミド。コーヒー豆を焙煎するときにできる物質で、ポテトチップスやトーストにも含まれています。カリフォルニア州の法律では、がんの原因になりうる物質を含む商品には、警告表示が必要なんです。"),
    ("story", 3, "8年後", "2018年 裁判所「会社側は、危険が小さいことを証明できなかった」",
     [E(lambda d: year_tag(d, 480, 360, "2018年")), E(lambda d: cw.gavel(d, 480, 600, 280)),
      E(lambda d: words(d, 1250, 540, "危険が小さいと", 64)), E(lambda d: words(d, 1250, 650, "証明できず", 90, BAD))],
     "裁判は8年続き、2018年、裁判所はこう判断します。「会社側は、危険が小さいことを証明できなかった」。コーヒーに、がんの警告表示が必要だというのです。"),
    ("card", 6, "悪い派、一気に15議席。"),
    ("seats", 6, "いい派51、悪い派49。一気に大接戦です。"),

    # 2018.7 英国(短く)
    ("card", 7, "同じ2018年、イギリスで50万人を調べた研究が出ます。1日8杯以上飲む人でも、死亡リスクは低かった。カフェインを分解するのが遅い体質の人でも、同じでした。いい派、57議席。"),

    # 2019 南オーストラリア大(カードだけ)
    ("card", 8, "でも、本当に8杯でも大丈夫なのでしょうか。2019年、オーストラリアの南オーストラリア大学のチームは、カフェインを分解するのが速い遺伝子の人なら平気なのでは、と調べました。結果は、遺伝子に関係なく、1日6杯以上の人は、1〜2杯の人より心臓病のリスクが最大22%高い。悪い派、6議席を取り返します。"),
    ("seats8", 8, "いい派51、悪い派49。またも大接戦です。"),

    # 第3話の続き
    ("story", 3, "裁判の続き", "2019年 州の当局「コーヒーのアクリルアミドで、がんの危険は大きくない」",
     [E(lambda d: year_tag(d, 480, 360, "2019年")), E(lambda d: cw.label(d, 300, 470, 340, 140, "がん警告")),
      E(lambda d: line(d, [(290, 640), (650, 450)], BAD, LW + 8)), E(lambda d: words(d, 1250, 540, "警告は", 80)),
      E(lambda d: words(d, 1250, 660, "不要", 110, GOOD))],
     "あの裁判には、続きがあります。2019年、カリフォルニア州の当局が、たくさんの研究を見直して「コーヒーに含まれるアクリルアミドで、がんの危険は大きくない」と結論。コーヒーに警告は不要、という決まりを作ったんです。"),
    ("card", 9, "いい派、15議席の大逆転。"),
    ("seats", 9, "いい派66、悪い派34。一気に差が開きました。"),

    # 第4話 ノルウェー
    ("story", 4, "37年前", "1983年 ノルウェーの町で「たくさん飲む人ほどコレステロールが高い」",
     [E(lambda d: year_tag(d, 480, 360, "1983年")), E(lambda d: cw.crowd(d, 300, 430, 4, 2, 120)),
      E(lambda d: words(d, 1250, 520, "コレステロールが", 64)), E(lambda d: words(d, 1250, 640, "高い", 110, BAD))],
     "次の舞台は北欧、ノルウェー。話は1983年にさかのぼります。北の町トロムソで約1万4千人を調べたテレ博士たちが、「コーヒーをたくさん飲む人ほど、コレステロールが高い」と発表しました。"),
    ("story", 4, "なぜ？", "この町では、鍋で煮出して濾さずに飲むのが普通だった",
     [E(lambda d: cw.pot(d, 480, 470, 280)), E(lambda d: words(d, 480, 800, "煮出し", 54, BAD)),
      E(lambda d: words(d, 960, 600, "vs", 90, TRIM)),
      E(lambda d: cw.dripper(d, 1440, 450, 260)), E(lambda d: words(d, 1440, 800, "ペーパーで濾す", 54, GOOD))],
     "実はこの町では、フィルターを使わず、鍋で煮出して飲むのが普通でした。その後の実験で、煮出したコーヒーに戻すとコレステロールが上がり、ペーパーで濾したコーヒーでは上がらないことが分かってきます。"),
    ("story", 4, "37年後", "2020年 50万人の調査:濾したコーヒーは死亡リスクが低い。煮出しは△",
     [E(lambda d: year_tag(d, 480, 360, "2020年")), E(lambda d: cw.dripper(d, 400, 470, 200)), E(lambda d: cw.check(d, 580, 520, 44)),
      E(lambda d: cw.pot(d, 1000, 480, 200)), E(lambda d: words(d, 1180, 520, "△", 90, BAD)),
      E(lambda d: words(d, 1500, 520, "濾したコーヒーは", 50)), E(lambda d: words(d, 1500, 610, "死亡リスク低い", 64, GOOD))],
     "そして37年後の2020年。ノルウェーの50万人を調べた研究で、ペーパーで濾したコーヒーを飲む人は、飲まない人より死亡リスクが低いと分かりました。一方、煮出したコーヒーは、60歳以上の男性で心臓病による死亡がやや高め。この研究チームには、37年前のあのテレ博士の名前もありました。"),
    ("card", 10, "差し引きで、いい派が3議席。69議席です。"),

    # 2021・2022.5(短く)
    ("card", 11, "2021年には、オーストラリアのチームが再び登場。1日6杯以上の人は、認知症の可能性が53%高いと発表します。悪い派、37議席まで回復。"),
    ("card", 12, "すると2022年、中国の研究チームがイギリスのデータで調べると、砂糖入りのコーヒーでも、1日1.5〜3.5杯なら死亡リスクが約3割低い。甘党にはうれしいニュースです。"),

    # 第5話 日本 JACC
    ("story", 5, "なぜ調べた？", "ここまでは「全体の平均」。血圧が高い人はどうなの？",
     [E(lambda d: flag_jp(d, 480, 420, 160)), E(lambda d: meter(d, 480, 700, 150, needle=0.88)),
      E(lambda d: words(d, 1250, 540, "血圧が高い人も", 64)), E(lambda d: words(d, 1250, 660, "大丈夫？", 100, BAD))],
     "ここまでの研究は、いわば「全体の平均」。では、持病がある人はどうなのか。2022年の年末、日本の研究チームが、血圧に注目した結果を発表します。"),
    ("story", 5, "どうやって？", "日本の約1万9千人を、血圧の高さでグループに分けて追いかけた",
     [E(lambda d: cw.crowd(d, 300, 420, 4, 2, 120)), E(lambda d: words(d, 1250, 500, "約1万9千人", 90)),
      E(lambda d: words(d, 1250, 630, "40〜79歳", 60))],
     "調べたのは、40歳から79歳の日本人、約1万9千人。血圧の高さでグループに分けて、その後を追いかけました。"),
    ("story", 5, "結果", "血圧がかなり高い人が1日2杯以上飲むと、死亡リスク約2倍。緑茶では上がらず",
     [E(lambda d: meter(d, 330, 640, 130, needle=0.88)), E(lambda d: words(d, 540, 590, "＋", 90)),
      E(lambda d: mug(d, 610, 480, 120, steam=False)), E(lambda d: mug(d, 750, 480, 120, steam=False)),
      E(lambda d: arrow(d, 920, 1010, 590)), E(lambda d: words(d, 1200, 590, "約2倍", 110, BAD)),
      E(lambda d: words(d, 1560, 590, "緑茶は差なし", 54, GOOD))],
     "すると、血圧がかなり高い人がコーヒーを1日2杯以上飲むと、心臓病などで亡くなるリスクが約2倍。ところが、同じ人たちでも、緑茶では高くなりませんでした。血圧が高めの方は、気にしておきたい結果です。"),
    ("card", 13, "悪い派、3議席を取り返します。"),

    # 第6話 2023 くじ引き実験
    ("story", 6, "弱点", "それまでの研究は「飲む人」と「飲まない人」を比べただけ",
     [E(lambda d: bean(d, 520, 420, 280, fill=GOOD)), E(lambda d: mug(d, 680, 500, 120, fill=CREAM)),
      E(lambda d: words(d, 960, 560, "vs", 90, TRIM)), E(lambda d: bean(d, 1400, 420, 280, fill=FADED)),
      E(lambda d: words(d, 960, 780, "もともと健康な人が飲んでいるだけかも？", 50, BAD))],
     "ここで、それまでの研究の弱点を考えてみましょう。どれも、飲む人と飲まない人を比べただけ。もしかすると、もともと健康な人が、コーヒーを飲んでいるだけかもしれません。"),
    ("story", 6, "どうやって？", "100人が14日間、スマホの指示で「飲む日」「飲まない日」を決めた",
     [E(lambda d: phone(d, 360, 590, 380, "今日は飲む", GOOD)), E(lambda d: phone(d, 640, 590, 380, "今日は飲まない", BAD)),
      E(lambda d: patch(d, 1050, 480, 220)), E(lambda d: watch(d, 1380, 560, 220)), E(lambda d: sensor(d, 1640, 520, 70)),
      E(lambda d: words(d, 1300, 760, "心電図・歩数・血糖値を記録", 46))],
     "そこで2023年、アメリカのチームが実験をします。健康な100人に、心電図のパッチ、歩数を測る腕時計、血糖値のセンサーをつけてもらい、14日間、毎日スマホに「今日は飲む」「今日は飲まない」と、くじで決めた指示を送ったんです。"),
    ("story", 6, "結果", "飲む日は歩数が約1,000歩多い。でも脈の乱れ約1.5倍、睡眠は約36分短い",
     [E(lambda d: cw.foot(d, 420, 560, 170)), E(lambda d: words(d, 420, 720, "+1,000歩", 60, GOOD)),
      E(lambda d: cw.ecg(d, 820, 570, 260)), E(lambda d: words(d, 950, 720, "脈の乱れ ×1.5", 60, BAD)),
      E(lambda d: cw.moon(d, 1480, 560, 70)), E(lambda d: words(d, 1480, 720, "睡眠 -36分", 60, BAD))],
     "結果、飲む日は1日約1,000歩多く歩いていました。でも、心臓の脈が乱れる回数は約1.5倍。睡眠は約36分短くなっていました。血糖値には差がありませんでした。"),
    ("card", 14, "2対1で、悪い派が3議席。"),

    # 2025(短く)
    ("card", 15, "2025年。アメリカの研究で、朝だけ飲む人は死亡リスクが16%低い一方、一日中飲む人は飲まない人と差がない、という結果が出ます。"),
    ("card", 16, "さらに2025年までの研究のまとめで、1日3〜5杯で、死亡や主な病気のリスクが低いと報告されました。"),

    ("final", "最終結果、いい派76議席。それでも当選確実が出せないのは、ほとんどが飲む人と飲まない人を比べただけの研究だからです。くじ引きの実験で歩数が増えていたように、コーヒーを飲む人がもともと活動的なだけ、という可能性も残っています。"),
    ("summary", "今日のまとめです。1日3から4杯くらいまでなら、体にいいという研究が多い。飲むなら朝に、濾したコーヒーを、熱すぎない温度で。そして、妊娠中の方と、血圧がかなり高い方は控えめに。心配な方は、お医者さんに相談してくださいね。30年戦っても、まだ決着がつかないコーヒー論争。次の研究で、また議席がひっくり返るかもしれません。"),
    ("next", "次回のテーマは「卵は1日1個まで」。こちらも、優勢が大きく揺れ動きます。"),
    ("outro", "新常識クロニクルでは、これからも、健康や暮らしの「いい派」と「悪い派」の論争を、どんどん分析していきます。次に取り上げてほしい論争があれば、ぜひコメントで教えてください。チャンネル登録と高評価も、よろしくお願いします！"),
]

STEP_COLORS = {"どうやって？": BAD, "なぜ調べた？": INK}


# ---------- 描画 ----------
def dur(narr):
    return max(3.0, len(narr) / SPEED + 0.8)


def element_layers(elements):
    out = []
    for f in elements:
        lay = blank()
        f(ImageDraw.Draw(lay))
        box = lay.getbbox()
        if box:
            out.append((lay.crop(box), box))
    return out


def pop_in(im, layers, t, start=0.5, step=0.28, length=0.45, dy=70):
    for i, (img, box) in enumerate(layers):
        k = seg(t, start + i * step, start + i * step + length)
        if k <= 0:
            continue
        sc = 0.55 + 0.45 * out_back(k)
        w, h = img.size
        r = img.resize((max(1, int(w * sc)), max(1, int(h * sc))), Image.BICUBIC)
        cx, cy = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2
        im.alpha_composite(with_alpha(r, min(1.0, k * 2)), (cx - r.size[0] // 2, cy + dy - r.size[1] // 2))


def story_base(chapter, step, slide):
    base = stage()[0].convert("RGBA")
    lay = blank()
    d = ImageDraw.Draw(lay)
    panel(d, (90, 130, 1830, 1000))
    chip(d, 230, 205, f"第{chapter}話", INK, 40)
    tw = d.textlength(step, font=font(40)) + 48
    d.rounded_rectangle([330, 205 - 34, 330 + tw, 205 + 34], radius=34, fill=STEP_COLORS.get(step, GOOD))
    text(d, (330 + tw / 2, 205), step, 40, WHITE, anchor="mm")
    return base, lay


def telop(d, s):
    size = int(min(52, 52 * 1600 / max(1, d.textlength(s, font=font(52)))))
    d.line([(140, 870), (1780, 870)], fill=(222, 218, 210), width=3)
    text(d, (960, 930), s, size, INK, anchor="mm")


def story_frames(chapter, step, tl, elements, first):
    base, lay = story_base(chapter, step, first)
    layers = element_layers(elements)
    tlay = blank()
    telop(ImageDraw.Draw(tlay), tl)

    def frame(t):
        im = base.copy()
        k = out_cubic(seg(t, 0.0, 0.45)) if first else 1.0
        im.alpha_composite(lay, (int((1 - k) * -1900), 0))
        if k >= 1:
            pop_in(im, layers, t, start=0.2 if not first else 0.5)
            a = seg(t, 0.3, 0.7)
            if a > 0:
                im.alpha_composite(with_alpha(tlay, a), (0, int((1 - a) * 20)))
        return im.convert("RGB")
    return frame, 0.5 + len(layers) * 0.28 + 0.6


def quiz_frames(chapter, q, a_txt, b_txt, ans, reveal):
    base, lay = story_base(chapter, "結果はどっち？" if not reveal else "答え", False)
    d = ImageDraw.Draw(lay)
    size = int(min(80, 80 * 1600 / d.textlength(q, font=font(80))))
    text(d, (960, 360), q, size, INK, anchor="mm")
    boxes = [(200, 510, 900, 790), (1020, 510, 1720, 790)]

    def button(dd, i, sc=1.0, faded=False, correct=False):
        x0, y0, x1, y1 = boxes[i]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        w, h = (x1 - x0) * sc / 2, (y1 - y0) * sc / 2
        col = (GOOD if i == 0 else BAD) if not faded else FADED
        dd.rounded_rectangle([cx - w, cy - h, cx + w, cy + h], radius=40 * sc, fill=WHITE, outline=col, width=max(3, int(10 * sc)))
        dd.ellipse([cx - w + 30 * sc, cy - 50 * sc, cx - w + 130 * sc, cy + 50 * sc], fill=col)
        text(dd, (cx - w + 80 * sc, cy), "AB"[i], int(60 * sc), WHITE, anchor="mm")
        label = (a_txt, b_txt)[i]
        ls = int(min(64, 64 * (w * 2 - 200 * sc) / max(1, dd.textlength(label, font=font(64)))) * 1)
        text(dd, (cx + 50 * sc, cy), label, max(10, int(ls * sc)), INK if not faded else SUB, anchor="mm")
        if correct:
            cw.check(dd, cx + w - 20, cy - h + 20, 50 * sc)

    def frame(t):
        im = base.copy()
        im.alpha_composite(lay)
        dd = ImageDraw.Draw(im)
        if not reveal:
            for i in range(2):
                k = seg(t, 0.3 + i * 0.25, 0.75 + i * 0.25)
                if k > 0:
                    button(dd, i, 0.6 + 0.4 * out_back(k))
            # 考える時間のバー
            k = seg(t, 1.0, 4.0)
            if k > 0:
                if k < 1:
                    dd.rounded_rectangle([560, 870, 560 + 800 * (1 - k) + 1, 896], radius=13, fill=TRIM)
        else:
            k = seg(t, 0.3, 0.8)
            for i in range(2):
                if i == ans:
                    button(dd, i, 1.0 + 0.12 * out_back(k) - 0.12 * k + 0.08 * k, correct=k > 0.2)
                else:
                    button(dd, i, 1.0 - 0.1 * k, faded=k > 0.1)
        return im.convert("RGB")
    return frame, (4.2 if not reveal else 1.2)


class WithAudio:
    """声の長さが分かってから描き方を決める場面。"""
    def __init__(self, make):
        self.make = make


def rules_frame_maker(narr, keys):
    def make(alen, lead):
        times = [lead + narr.index(k) / len(narr) * alen - 0.2 for k in keys]
        img_rows = [("公的機関・裁判所の判断", "15議席"), ("たくさんの研究のまとめ", "10議席"),
                    ("数十万人の追跡調査", "6議席"), ("条件つきの結果", "3議席")]

        def frame(t):
            im, d = stage()
            panel(d, (300, 150, 1620, 960))
            text(d, (W / 2, 230), "議席を動かすルール", 80, INK, anchor="mm")
            now = max([i for i, tt in enumerate(times) if t >= tt], default=-1)
            for i, (k, v) in enumerate(img_rows):
                kk = seg(t, times[i], times[i] + 0.4)
                if kk <= 0:
                    continue
                sc = 0.7 + 0.3 * out_back(kk)
                y = 360 + i * 120
                cx, cy = W / 2, y + 48
                hw, hh = 580 * sc, 48 * sc
                fill = (255, 232, 205) if i == now else (240, 236, 228)
                d.rounded_rectangle([cx - hw, cy - hh, cx + hw, cy + hh], radius=hh, fill=fill)
                text(d, (cx - hw + 50 * sc, cy), k, int(52 * sc), INK, anchor="lm")
                text(d, (cx + hw - 50 * sc, cy), v, int(60 * sc), GOOD, anchor="rm")
            text(d, (W / 2, 880), "※ 議席は演出のための目安です", 36, SUB, heavy=False, anchor="mm")
            return im
        return frame, times[-1] + 0.6
    return WithAudio(make)


def quiz_preview_frame(t):
    im, d = stage()
    panel(d, (300, 160, 1620, 960))
    k = out_back(seg(t, 0.2, 0.6))
    text(d, (W / 2, 290), "途中でクイズ！", int(90 * (0.6 + 0.4 * k)), INK, anchor="mm")
    for i, (lab, c) in enumerate((("いい結果", GOOD), ("悪い結果", BAD))):
        kk = seg(t, 0.6 + i * 0.3, 1.0 + i * 0.3)
        if kk <= 0:
            continue
        sc = 0.6 + 0.4 * out_back(kk)
        cx, cy = 690 + i * 540, 560
        w, h = 230 * sc, 110 * sc
        d.rounded_rectangle([cx - w, cy - h, cx + w, cy + h], radius=36 * sc, fill=WHITE, outline=c, width=max(3, int(10 * sc)))
        d.ellipse([cx - w + 24 * sc, cy - 40 * sc, cx - w + 104 * sc, cy + 40 * sc], fill=c)
        text(d, (cx - w + 64 * sc, cy), "AB"[i], int(48 * sc), WHITE, anchor="mm")
        text(d, (cx + 40 * sc, cy), lab, int(54 * sc), INK, anchor="mm")
    a = seg(t, 1.6, 2.0)
    if a > 0:
        text(d, (W / 2, 800), "予想しながら見てね", 56, tuple(int(INK[j] * a + PANEL[j] * (1 - a)) for j in range(3)), anchor="mm")
    return im


def chapter_start_frame(no, sub):
    def frame(t):
        im, d = stage()
        k = out_back(seg(t, 0.2, 0.7))
        if k > 0:
            text(d, (W / 2, 470), no, int(220 * (0.5 + 0.5 * k)), WHITE, anchor="mm")
        a = seg(t, 0.7, 1.1)
        if a > 0:
            text(d, (W / 2, 690), sub, 90, tuple(int(TRIM[j] * a + 30 * (1 - a)) for j in range(3)), anchor="mm")
        return im
    return frame


def headlines_frame(t):
    im = stage()[0].convert("RGBA")
    lay = blank()
    d = ImageDraw.Draw(lay)
    mug(d, 830, 400, 260, fill=CREAM)
    im.alpha_composite(lay)
    d = ImageDraw.Draw(im)
    items = [("コーヒーで長生き！", GOOD, 420, 300), ("発がん性の疑い？", BAD, 1500, 300),
             ("1日3杯が最強！", GOOD, 400, 760), ("6杯で心臓に負担", BAD, 1500, 760)]
    for i, (s, c, x, y) in enumerate(items):
        k = seg(t, 0.8 + i * 0.95, 1.2 + i * 0.95)
        if k > 0:
            chip(d, x, y, s, c, int(54 * (0.5 + 0.5 * out_back(k))))
    k = seg(t, 4.6, 5.1)
    if k > 0:
        text(d, (W / 2, 950), "いったい、どっちなんでしょう？", int(76 * (0.5 + 0.5 * out_back(k))), WHITE, anchor="mm")
    return im.convert("RGB")


def summary_frame(t):
    im, d = stage()
    panel(d, (200, 150, 1720, 960))
    text(d, (960, 230), "まとめ", 76, INK, anchor="mm")
    items = [("1日3〜4杯くらいまでなら", "体にいいという研究が多い", GOOD), ("飲むなら", "朝に・濾して・熱すぎない温度で", GOOD),
             ("妊娠中・血圧がかなり高い人は", "控えめに", BAD), ("心配な人は", "お医者さんに相談", INK)]
    for i, (a, b, c) in enumerate(items):
        k = seg(t, 0.6 + i * 3.2, 1.0 + i * 3.2)
        if k > 0:
            y = 340 + i * 150
            d.rounded_rectangle([280, y, 1640, y + 120], radius=60, fill=(240, 236, 228))
            d.ellipse([300, y + 20, 380, y + 100], fill=c)
            text(d, (340, y + 60), str(i + 1), 48, WHITE, anchor="mm")
            text(d, (420, y + 60), a, 44, SUB, heavy=False, anchor="lm")
            text(d, (1610, y + 60), b, 50, c, anchor="rm")
    return im


def intro_myths_maker(narr, keys):
    """「常識」のチップが言葉に合わせて出て、最後に全部に「？」がつく。"""
    def make(alen, lead):
        times = [lead + narr.index(k) / len(narr) * alen - 0.1 for k in keys]
        q_t = lead + narr.index("いまの研究") / len(narr) * alen
        spots = [(560, 330), (1360, 470), (700, 650)]

        def frame(t):
            im, d = stage()
            text(d, (W / 2, 160), "よく聞くこの話", 64, TRIM, anchor="mm")
            for i, (k, (x, y)) in enumerate(zip(keys, spots)):
                kk = seg(t, times[i], times[i] + 0.35)
                if kk <= 0:
                    continue
                size = int(64 * (0.5 + 0.5 * out_back(kk)))
                tw = d.textlength(k, font=font(size)) + size * 1.4
                d.rounded_rectangle([x - tw / 2, y - size, x + tw / 2, y + size], radius=size * 0.4, fill=WHITE,
                                    outline=INK, width=6)
                text(d, (x, y), k, size, INK, anchor="mm")
                qk = seg(t, q_t + i * 0.25, q_t + i * 0.25 + 0.35)
                if qk > 0:
                    r = 52 * out_back(qk)
                    d.ellipse([x + tw / 2 - r, y - size - r * 0.6, x + tw / 2 + r, y - size + r * 1.4], fill=TRIM)
                    text(d, (x + tw / 2, y - size + r * 0.4), "？", int(70 * min(1, qk * 1.5)), WHITE, anchor="mm")
            k2 = seg(t, q_t + 0.9, q_t + 1.3)
            if k2 > 0:
                text(d, (W / 2, 900), "いまの研究では、どうなってる？", int(76 * (0.6 + 0.4 * out_back(k2))), WHITE, anchor="mm")
            return im
        return frame, q_t + 1.6
    return WithAudio(make)


def intro_flip_frame(t):
    """「常識」のカードがくるっと裏返って「新常識」になる。"""
    import math as m
    im, d = stage()
    k = seg(t, 1.0, 2.2)
    ang = m.pi * (1 - (1 - k) ** 2)
    w = abs(m.cos(ang))
    front = ang < m.pi / 2
    cx, cy, cw_, ch = W / 2, 520, 560, 300
    col, label, tc = (WHITE, "常識", INK) if front else (GOOD, "新常識", WHITE)
    if w > 0.02:
        d.rounded_rectangle([cx - cw_ * w, cy - ch, cx + cw_ * w, cy + ch], radius=40, fill=col, outline=INK, width=8)
        if w > 0.3:
            text(d, (cx, cy), label, int(170 * w), tc, anchor="mm")
    a = seg(t, 2.3, 2.7)
    if a > 0:
        text(d, (W / 2, 920), "研究の答えは、時代とともに変わる", int(60 * (0.7 + 0.3 * out_back(a))), WHITE, anchor="mm")
    return im


def intro_logo_frame(t):
    im, d = stage()
    k = out_back(seg(t, 0.2, 0.8))
    if k > 0:
        text(d, (W / 2, 420), "新常識クロニクル", int(190 * (0.5 + 0.5 * k)), WHITE, anchor="mm")
    a = seg(t, 0.9, 1.3)
    if a > 0:
        text(d, (W / 2, 600), "論争の歴史を、データで楽しく", 70, tuple(int(TRIM[j] * a + 30 * (1 - a)) for j in range(3)), anchor="mm")
    for i, (lab, c, x) in enumerate((("いい派", GOOD, W / 2 - 230), ("悪い派", BAD, W / 2 + 230))):
        kk = seg(t, 1.5 + i * 0.25, 1.9 + i * 0.25)
        if kk > 0:
            sc = 0.6 + 0.4 * out_back(kk)
            d.rounded_rectangle([x - 150 * sc, 780 - 50 * sc, x + 150 * sc, 780 + 50 * sc], radius=50 * sc, fill=c)
            text(d, (x, 780), lab, int(60 * sc), WHITE, anchor="mm")
    if t > 1.9:
        text(d, (W / 2, 780), "vs", 56, TRIM, anchor="mm")
    return im


def outro_frame(t):
    im, d = stage()
    k = out_back(seg(t, 0.2, 0.7))
    if k > 0:
        text(d, (W / 2, 230), "新常識クロニクル", int(120 * (0.5 + 0.5 * k)), WHITE, anchor="mm")
    a = seg(t, 0.6, 1.0)
    if a > 0:
        text(d, (W / 2, 350), "これからも、論争をどんどん分析します", 56, tuple(int(TRIM[j] * a + 30 * (1 - a)) for j in range(3)), anchor="mm")
    topics = ["卵は1日1個まで？", "お酒は少しなら体にいい？", "1日1万歩は必要？", "サウナは長生きのもと？", "朝ごはんは食べるべき？", "塩は減らすほどいい？"]
    for i, tp in enumerate(topics):
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
        # ベル
        bx = cx + bw + 70 * sc
        d.pieslice([bx - 36 * sc, cy - 44 * sc, bx + 36 * sc, cy + 28 * sc], 180, 360, fill=TRIM)
        d.rectangle([bx - 36 * sc, cy - 8 * sc, bx + 36 * sc, cy + 20 * sc], fill=TRIM)
        d.ellipse([bx - 10 * sc, cy + 18 * sc, bx + 10 * sc, cy + 38 * sc], fill=TRIM)
        text(d, (cx, cy + bh + 40 * sc), "高評価・コメントもよろしくお願いします", int(36 * sc), WHITE, heavy=False, anchor="mm")
    return im


def next_frame(t):
    im, d = stage()
    text(d, (W / 2, 300), "次回の逆転論争", 70, TRIM, anchor="mm")
    lay = blank()
    dd = ImageDraw.Draw(lay)
    dd.ellipse([W / 2 - 110, 400, W / 2 + 110, 690], fill=WHITE, outline=INK, width=LW)
    k = out_back(seg(t, 0.3, 0.8))
    if k > 0:
        im = im.convert("RGBA")
        w, h = lay.size
        r = lay.resize((int(w * (0.6 + 0.4 * k)), int(h * (0.6 + 0.4 * k))))
        im.alpha_composite(r, ((w - r.size[0]) // 2, (h - r.size[1]) // 2))
        im = im.convert("RGB")
        d = ImageDraw.Draw(im)
    text(d, (W / 2, 820), "卵は1日1個まで？", 100, WHITE, anchor="mm")
    return im


# ---------- 組み立て ----------
def build_plan():
    """(描く関数, 動く秒数, 合計秒数, 台本の行) のリスト。"""
    plan = []
    last_chapter = None
    for sc in SCENES:
        kind = sc[0]
        if kind == "headlines":
            plan.append((headlines_frame, 5.2, dur(sc[1]), ("オープニング", "", sc[1])))
        elif kind == "title":
            img = os.path.join(OUT, "00_title.png")
            cw.title_card(img)
            plan.append(((lambda im: lambda t: im)(Image.open(img)), 0, dur(sc[1]), ("タイトル", "", sc[1])))
        elif kind == "rules":
            plan.append((rules_frame_maker(sc[1], sc[2]), 0, dur(sc[1]), ("ルール説明", "議席を動かすルール", sc[1])))
        elif kind == "rules_intro":
            plan.append((lambda t: parliament_frame("", "研究の歴史を選挙に見立てる", 50, 50, t, tag="ルール"), 0.6, dur(sc[1]),
                         ("ルール説明", "100議席・スタートは50対50", sc[1])))
        elif kind == "demo":
            _, narr, b, a, h = sc
            plan.append(((lambda b, a, h: lambda t: parliament_frame("", h, b, a, t, flip=(1.2, 2.3), settle=3.2, tag="たとえば"))(b, a, h),
                         3.4, dur(narr), ("ルール説明", f"たとえば {b}→{a}", narr)))
        elif kind == "quiz_preview":
            plan.append((quiz_preview_frame, 2.1, dur(sc[1]), ("ルール説明", "途中でクイズ", sc[1])))
        elif kind == "chapter_start":
            plan.append((chapter_start_frame(sc[2], sc[3]), 1.2, dur(sc[1]), (sc[2], sc[3], sc[1])))
        elif kind == "final":
            plan.append((lambda t: cw.final_frame(cw.EVENTS[-1][7], t), 2.6, dur(sc[1]), ("結果", "", sc[1])))
        elif kind == "summary":
            plan.append((summary_frame, 11.0, dur(sc[1]), ("まとめ", "", sc[1])))
        elif kind == "intro_myths":
            plan.append((intro_myths_maker(sc[1], sc[2]), 0, dur(sc[1]), ("番組紹介", "よく聞くこの話、いまの研究では？", sc[1])))
        elif kind == "intro_flip":
            plan.append((intro_flip_frame, 2.8, dur(sc[1]), ("番組紹介", "常識 → 新常識", sc[1])))
        elif kind == "intro_logo":
            plan.append((intro_logo_frame, 2.2, dur(sc[1]), ("番組紹介", "新常識クロニクル:論争の歴史を、データで楽しく", sc[1])))
        elif kind == "outro":
            plan.append((outro_frame, 4.2, dur(sc[1]), ("エンディング", "チャンネル登録・今後の論争", sc[1])))
        elif kind == "next":
            plan.append((next_frame, 1.0, dur(sc[1]), ("次回予告", "", sc[1])))
        elif kind == "story":
            _, ch, step, tl, els, narr = sc
            fn, anim = story_frames(ch, step, tl, els, first=(ch != last_chapter))
            last_chapter = ch
            plan.append((fn, anim, dur(narr), (f"第{ch}話「{step}」", tl, narr)))
        elif kind == "quiz":
            _, ch, q, a, b, ans, narr_q, narr_a = sc
            fq, aq = quiz_frames(ch, q, a, b, ans, False)
            fa, aa = quiz_frames(ch, q, a, b, ans, True)
            plan.append((fq, aq, max(dur(narr_q), 5.0), (f"第{ch}話 クイズ", f"{q}  A:{a} / B:{b}", narr_q)))
            plan.append((fa, aa, dur(narr_a), (f"第{ch}話 答え", "AB"[ans] + "：" + (a, b)[ans], narr_a)))
            last_chapter = ch
        elif kind == "card":
            last_chapter = None
            _, idx, narr = sc
            year, country, kindx, title, facts, picto, before, after, headline, source = cw.EVENTS[idx - 1]
            rows = [[(s, cw.color_of(c)) for s, c in row] for row in title]
            diff = after - before
            delta = f"{'いい派' if diff > 0 else '悪い派'} +{abs(diff)}議席"
            card = Card(year, country, kindx, rows, facts, picto, before, after, delta, source)
            plan.append((card.frame, Card.ANIM_END, max(dur(narr), Card.ANIM_END + 1.0),
                         (f"研究カード {year}", f"{before}→{after}", narr)))
        elif kind in ("seats", "seats8"):
            _, idx, narr = sc
            year, _, _, _, _, _, before, after, headline, _ = cw.EVENTS[idx - 1]
            plan.append(((lambda y, h, b, a: lambda t: parliament_frame(y, h, b, a, t))(year, headline, before, after),
                         2.6, max(dur(narr), 3.6), (f"開票速報 {year}", f"{before}→{after}", narr)))
    return plan


def write_script(plan):
    total = 0.0
    lines = ["# 台本(物語版):コーヒー10年戦争 〜「いい派」vs「悪い派」論争の行方〜", "",
             "作成：2026-11-21 / 状態：初稿。`scripts/coffee_story.py` の SCENES から自動で作っています(台本を直すときは SCENES を直す)。", "",
             f"ナレーション合計：約{sum(len(p[3][2]) for p in plan):,}字。場面の長さは合成したナレーション(1.5倍の速さ)の長さで決まる。", "",
             "| 時間 | 場面 | 画面のテロップ・内容 | ナレーション |", "|---|---|---|---|"]
    for _, _, sec, (name, tl, narr) in plan:
        m, s = divmod(int(total), 60)
        lines.append(f"| {m}:{s:02d} | {name} | {tl} | {narr} |")
        total += sec
    m, s = divmod(int(total), 60)
    lines += ["", f"合計：約{m}分{s:02d}秒", "",
              "## 公開前に原文で確認すること",
              "- 第1話：1981年の研究(MacMahon ら、NEJM)の人数 369人/644人、1986年の追試の内容",
              "- 第2話：「タバコを吸う人が少なかった女性では関係がほぼ見られなかった」(IARC 2016 の評価文書)",
              "- 第3話:EPIC の追跡期間「16年あまり」、血液を調べた人数「約1万4千人」(論文では14,800人)",
              "- 第4話：訴えたのは 2010年・約90社(報道)。「8年続いた」裁判",
              "- 第6話:1983年のトロムソの研究は約1万4千人(7,213人+7,368人)。煮出しと濾したコーヒーの比較実験は1985年。2020年の論文の著者にテレ博士(Thelle)が入っていること",
              "- 第7話：日本の研究の人数 18,609人・40〜79歳",
              "- 第8話：くじ引き実験の数字(歩数+1,058歩、期外収縮 約1.5倍、睡眠 397分 vs 432分)",
              "- そのほかは `content/coffee_war.md` の「要確認」と同じ", ""]
    with open(SCRIPT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    write_narration_txt(plan)
    return total


def write_narration_txt(plan):
    """外部のナレーション生成サービスに渡すテキスト(場面の見出しつき/本文だけ)。"""
    base = os.path.splitext(SCRIPT_MD)[0].replace("_story", "")
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


def voice_for(i, narr, cache, emotion=None):
    """場面のナレーション音声(キャッシュあり)。"""
    narrate.MM_EMOTION = emotion
    import hashlib
    import numpy as np
    import soundfile as sf
    from narrate import RATE, synth
    os.makedirs(cache, exist_ok=True)
    from narrate import voice_key
    from narrate import mm_text
    key = hashlib.md5(f"{voice_key()}|{mm_text(narr)}".encode()).hexdigest()[:12]   # 送る文章が同じなら作り直さない
    path = os.path.join(cache, f"{key}.wav")
    if not os.path.exists(path):
        sf.write(path, synth(narr), RATE)
    a, _ = sf.read(path, dtype="float32")
    return np.asarray(a)


def main():
    os.makedirs(OUT, exist_ok=True)
    plan = build_plan()
    if "--script" in sys.argv:
        total = write_script(plan)
        print(f"台本：{SCRIPT_MD}(約{int(total // 60)}分{int(total % 60):02d}秒、{len(plan)}場面)")
        return
    import numpy as np
    import soundfile as sf
    from narrate import RATE
    LEAD, TAIL = 0.25, 0.4
    voices = []
    new_plan = []
    for i, (fn, anim, sec, meta) in enumerate(plan):
        v = voice_for(i, meta[2], os.path.join(OUT, "voice"), INTRO_EMOTION if meta[0] in INTRO_SCENES else None)
        extra = 2.0 if "クイズ" in meta[0] else 0.0   # クイズは考える時間
        sec = max(anim + 0.3 if anim else 2.0, LEAD + len(v) / RATE + TAIL + extra)
        if "研究カード" in meta[0]:
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
    out = os.path.join(OUT, "coffee_story_draft.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", wav, "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-c:a", "aac", "-b:a", "160k",
                    "-shortest", out], check=True)
    shutil.rmtree(seg_dir)
    print("done:", out)


if __name__ == "__main__":
    sys.exit(main())
