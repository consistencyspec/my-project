"""卵は1日1個まで？ 物語版：主な研究を物語にして、研究カードと議席でつなぐ(新常識クロニクル 第2回)。

  .venv/bin/python scripts/egg_story.py           -> output/egg_story/egg_story_draft.mp4(ナレーションつき)
  .venv/bin/python scripts/egg_story.py --script  -> content/egg_war_story.md(台本)だけ作り直す

コーヒー回(coffee_story.py)と同じ部品を使う。違いは冒頭：サムネイルからすぐ本題に入れるよう、
番組紹介を短くし、最初の一言から卵の話をする。場面の長さは合成したナレーションの長さで決まる。
"""
import os
import shutil
import subprocess
import sys

from PIL import ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frames import BAD, GOOD, INK, PANEL, SUB, TRIM, W, WHITE, arrow, font, heart, line, panel, stage, text  # noqa: E402
from motion import Card, blank, out_back, parliament_frame, seg  # noqa: E402
import coffee_war as cw  # noqa: E402
import coffee_story as cs  # noqa: E402
from coffee_story import WithAudio, chapter_start_frame, chip, magnifier, story_frames, words, year_tag  # noqa: E402
import egg_war as ew  # noqa: E402
from egg_war import (bacon, butter, egg, eggs_row, flag_jp, fried, grass, liver, rabbit, struck, vessel,  # noqa: E402
                     wine, yolk)
from thumbnail import EPISODES, series_card  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "output", "egg_story")
SCRIPT_MD = os.path.join(HERE, "..", "content", "egg_war_story.md")
EVENTS = ew.EVENTS
import narrate  # noqa: E402
# 卵の回で読み間違えやすい語(コーヒー回の声のキャッシュを変えないよう、この回だけで足す)
narrate.MM_DICT += ["750mg/ななひゃくごじゅうミリグラム", "600mg/ろっぴゃくミリグラム", "300mg/さんびゃくミリグラム",
                    "200mg/にひゃくミリグラム", "LDL/エルディーエル", "1〜6回/いちからろっかい", "半個/はんこ",
                    "2個目/にこめ", "1個/いっこ", "2個/にこ", "週3個/しゅうさんこ", "黄身/きみ", "主に/おもに",
                    "草食/そうしょく", "肝臓/かんぞう", "飽和脂肪/ほうわしぼう", "脂質異常症/ししついじょうしょう",
                    "食事摂取基準/しょくじせっしゅきじゅん", "51年前/ごじゅういちねんまえ", "17年/じゅうななねん",
                    "白身/しろみ", "返り咲/かえりざ", "悪玉/あくだま", "見方/みかた", "暮れ/くれ", "6つ/むっつ",
                    "3つ/みっつ", "1つ目/ひとつめ", "2つ目/ふたつめ", "3つ目/みっつめ", "50対50/ごじゅうたいごじゅう",
                    "100年/ひゃくねん", "14年/じゅうよねん", "動脈硬化/どうみゃくこうか"]
cs.STEP_COLORS.update({"どうやって？": BAD, "なぜ調べた？": INK, "なぜ？": INK})


def E(f):
    return f


# ---------- 場面 ----------
# 種類はコーヒー回と同じ。("story", 話数, 見出し, テロップ, [要素], ナレーション) / ("card", 研究番号, ナレーション) / ("seats", 研究番号, ナレーション)
SCENES = [
    # 冒頭：サムネイル(卵は1日1個まで？)の続きから、すぐ本題に入る
    ("hook", "「卵は1日1個まで」。そう聞いて、2個目をがまんしたこと、ありませんか？ ところがこのルール、日本の国の基準からは、2015年に消えているんです。"),
    ("title", "卵は、なぜ悪者にされ、なぜ許されたのか。100年以上にわたる論争を、データで判定します。新常識クロニクル、今日のテーマは「卵は1日1個まで？」です。"),
    # ルール説明(短く)
    ("rules_intro", "見方はかんたん。研究の歴史を選挙に見立てます。議席は100。オレンジが「卵は食べていい」派、青が「控えるべき」派。スタートは50対50です。"),
    ("rules", "研究が出るたびに、勝った側に議席が移ります。国や大きな学会の公式な判断は15議席、たくさんの研究のまとめは10議席、数十万人の調査は6議席、条件が限られた結果は3議席です。",
     ["公式な判断", "まとめ", "数十万人", "条件が限られた"]),
    ("chapter_start", "それでは、行ってみましょう！第1話。物語は、100年以上前のロシアから始まります。", "第1話", "すべての始まり"),

    # 第1話 ウサギと「週3個」
    ("story", 1, "はじまり", "1913年 ロシアの研究者が、ウサギに卵の黄身を食べさせると、血管に脂がたまった",
     [E(lambda d: year_tag(d, 420, 360, "1913年")), E(lambda d: rabbit(d, 400, 640, 210)),
      E(lambda d: words(d, 640, 600, "＋", 90)), E(lambda d: yolk(d, 790, 600, 80)),
      E(lambda d: arrow(d, 920, 1010, 600)), E(lambda d: vessel(d, 1300, 600, 420, 190)),
      E(lambda d: words(d, 1300, 730, "血管に脂がたまった", 56, BAD))],
     "1913年、ロシアの研究者アニチコフは、ウサギに卵の黄身や、コレステロールを食べさせました。すると、ウサギの血管の壁に脂がたまり、動脈硬化が起きたんです。"),
    ("story", 1, "落とし穴", "ただしウサギは草食。ふだんコレステロールをほとんど食べない動物",
     [E(lambda d: rabbit(d, 450, 560, 260)), E(lambda d: grass(d, 760, 700, 150)),
      E(lambda d: words(d, 1300, 520, "ウサギは", 64)), E(lambda d: words(d, 1300, 640, "草食", 120, BAD))],
     "ただし、ウサギは草食動物。ふだんの食事にコレステロールはほとんどなく、体が処理に慣れていません。それでも、「食べたコレステロールが血管を詰まらせる」という考えは、広まっていきます。"),
    ("card", 1, "悪い派、まず3議席。"),
    ("story", 1, "週3個まで", "1968年 米国心臓協会「コレステロールは1日300mg未満、卵は週3個まで」",
     [E(lambda d: year_tag(d, 420, 360, "1968年")), E(lambda d: heart(d, 420, 440, 200, fill=(220, 70, 70))),
      E(lambda d: eggs_row(d, 780, 600, 3, 170, 135)),
      E(lambda d: words(d, 1420, 540, "週3個まで", 96, BAD)), E(lambda d: words(d, 1420, 670, "1日300mg未満", 60))],
     "そして1968年、アメリカ心臓協会が、こう勧めます。コレステロールは1日300mg未満、卵は週に3個まで。この数字が、世界中に広がりました。"),
    ("card", 2, "悪い派、一気に15議席。"),
    ("seats", 2, "悪い派68、いい派32。卵は、すっかり悪者です。"),

    # 1999〜2013(カード)
    ("card", 3, "反撃は1999年。アメリカのハーバード大学が、約12万人を最長14年追いかけると、卵を1日1個食べても、心臓病や脳卒中は増えていませんでした。ただし、糖尿病の人だけは高め。差し引きで、いい派3議席。"),
    ("card", 4, "ところが日本では2005年、厚生労働省の食事摂取基準に、コレステロールの上限の目安が入ります。男性は1日750mg未満、女性は600mg未満。悪い派、80議席に。"),
    ("card", 5, "その翌年、日本の約9万人を追いかけた研究では、卵をよく食べる人でも、心臓病が増える関係は見られませんでした。いい派、26議席。"),
    ("card", 6, "2013年には、中国の研究チームが世界の研究をまとめて、1日1個までなら、心臓病も脳卒中も増えない、と発表。ここでも、糖尿病の人は例外でした。"),

    # 第2話 日本が上限をやめた
    ("story", 2, "大転換", "2015年 日本の国の基準から、コレステロールの上限が消えた",
     [E(lambda d: year_tag(d, 420, 360, "2015年")), E(lambda d: flag_jp(d, 420, 560, 240)),
      E(lambda d: cw.label(d, 760, 500, 420, 160, "上限の目安")), E(lambda d: struck(d, 750, 500, 1190, 660)),
      E(lambda d: words(d, 1520, 580, "撤廃", 130, GOOD))],
     "そして2015年、大きな転換が起きます。日本の食事摂取基準から、コレステロールの上限が消えたんです。"),
    ("story", 2, "なぜ？", "血液中のコレステロールの多くは、体の中(主に肝臓)で作られている",
     [E(lambda d: liver(d, 470, 560, 380)), E(lambda d: words(d, 470, 730, "肝臓", 56)),
      E(lambda d: words(d, 1250, 470, "多くは体の中で", 64)), E(lambda d: words(d, 1250, 580, "作られる", 96, GOOD)),
      E(lambda d: egg(d, 1080, 730, 90)), E(lambda d: words(d, 1330, 730, "食事からは一部", 52))],
     "理由は、体の仕組みにあります。血液の中のコレステロールは、多くが体の中、主に肝臓で作られています。食事からたくさん入ると、肝臓が作る量を減らして、調整してくれるんです。"),
    ("story", 2, "結論", "「食べる量と血液の値の関係を示す、十分な根拠がない」",
     [E(lambda d: cw.papers(d, 360, 450, 240, 5)), E(lambda d: magnifier(d, 760, 600, 100)),
      E(lambda d: words(d, 1330, 520, "十分な根拠が", 72)), E(lambda d: words(d, 1330, 650, "ない", 110, GOOD))],
     "食べる量と、血液の中の値の関係を示す十分な根拠がない。そう判断して、上限の目安をやめたんです。"),
    ("card", 7, "いい派、15議席。48議席まで迫ります。"),
    ("card", 8, "翌2016年、アメリカも続きます。国の食事指針から、1日300mgという上限が消えました。"),
    ("seats", 8, "いい派63、悪い派37。ついに逆転です！"),
    ("card", 9, "2018年には、中国の約42万人の調査で、毎日卵を食べる人は、食べない人より、心臓や血管の病気が11%少ないと報告されます。"),

    # 第3話 ふたたび悪者に？
    ("story", 3, "反撃", "2019年 アメリカの6つの調査、約3万人を17年あまり追いかけた",
     [E(lambda d: year_tag(d, 420, 360, "2019年")), E(lambda d: cw.crowd(d, 280, 430, 5, 2, 120)),
      E(lambda d: words(d, 1330, 520, "約3万人", 96)), E(lambda d: words(d, 1330, 650, "17年あまり", 64))],
     "ところが2019年、悪い派が反撃します。アメリカの6つの調査をまとめ、約3万人を17年あまり追いかけた研究です。"),
    ("story", 3, "結果", "卵が1日半個増えるごとに、心臓・血管の病気+6%、死亡+8%",
     [E(lambda d: egg(d, 400, 560, 230, half=True)), E(lambda d: words(d, 400, 720, "1日半個", 56, BAD)),
      E(lambda d: arrow(d, 600, 690, 580)), E(lambda d: cw.broken_heart(d, 880, 500, 200)),
      E(lambda d: words(d, 880, 720, "+6%", 72, BAD)), E(lambda d: words(d, 1420, 580, "死亡 +8%", 100, BAD))],
     "結果は、卵を1日に半個多く食べるごとに、心臓や血管の病気が6%、死亡が8%増える、というもの。「卵はやっぱり体に悪い」と、大きなニュースになりました。"),
    ("card", 10, "悪い派、6議席を取り返します。"),
    ("story", 3, "51年後", "2019年12月 米国心臓協会「健康な人なら、卵は1日1個まで大丈夫」",
     [E(lambda d: year_tag(d, 420, 360, "2019年12月")), E(lambda d: heart(d, 420, 440, 200, fill=(220, 70, 70))),
      E(lambda d: egg(d, 800, 590, 200)), E(lambda d: cw.check(d, 900, 480, 50)),
      E(lambda d: words(d, 1420, 530, "1日1個まで", 90, GOOD)), E(lambda d: words(d, 1420, 660, "高齢者は2個まで", 56))],
     "でも同じ年の暮れ、あのアメリカ心臓協会が、新しい見解を出します。健康な人なら、卵は1日1個まで大丈夫。コレステロールの値が正常な高齢者なら、2個まで。51年前に「週3個まで」と言った、あの協会です。"),
    ("card", 11, "いい派、15議席。"),
    ("seats", 11, "いい派78、悪い派22。大きく差が開きました。"),
    ("card", 12, "ただ、日本の2020年版の基準では、脂質異常症の人は、コレステロールを1日200mg未満に、とされました。卵1個で、ほぼこの量です。"),
    ("card", 13, "さらに2021年、アメリカの約52万人の調査で、卵を1日半個多く食べるごとに、死亡リスクが7%高い、という結果も。一方、白身だけなら、むしろ低めでした。"),
    ("card", 14, "それでも2025年、オーストラリアの70歳以上、約8,700人の調査では、卵を週に1〜6回食べる人は、ほとんど食べない人より、心臓病で亡くなるリスクが29%低かったんです。"),

    # 第4話 真犯人
    ("story", 4, "なぜ調べた？", "悪いのは卵のコレステロール？ それとも一緒に食べる「飽和脂肪」？",
     [E(lambda d: fried(d, 420, 560, 300)), E(lambda d: words(d, 680, 560, "＋", 90)),
      E(lambda d: bacon(d, 940, 520, 300)), E(lambda d: butter(d, 960, 660, 200)),
      E(lambda d: words(d, 1450, 520, "真犯人は", 64)), E(lambda d: words(d, 1450, 650, "どっち？", 100, BAD))],
     "そして2025年、ついに「真犯人」を探す実験が行われます。卵は、ベーコンやバターと一緒に食べることが多い。悪いのは卵のコレステロールなのか、それとも、肉やバターに多い「飽和脂肪」なのか。"),
    ("story", 4, "どうやって？", "61人が3つの食事を5週間ずつ。順番はくじで決めた",
     [E(lambda d: chip(d, 960, 400, "① 卵 毎日2個 ＋ 飽和脂肪 少なめ", GOOD, 50)),
      E(lambda d: chip(d, 960, 560, "② 卵なし ＋ 飽和脂肪 多め", BAD, 50)),
      E(lambda d: chip(d, 960, 720, "③ 卵 週1個 ＋ 飽和脂肪 多め", BAD, 50))],
     "南オーストラリア大学のチームは、健康な61人に、3つの食事を5週間ずつ試してもらいました。1つ目は、卵を毎日2個、でも飽和脂肪は少なめ。2つ目は、卵なしで、飽和脂肪は多め。3つ目は、卵は週1個で、飽和脂肪は多め。"),
    ("story", 4, "結果", "悪玉(LDL)コレステロールが一番低かったのは、卵を毎日2個食べた食事",
     [E(lambda d: eggs_row(d, 330, 540, 2, 200, 150)), E(lambda d: cw.check(d, 580, 430, 50)),
      E(lambda d: words(d, 400, 720, "いちばん低い", 60, GOOD)),
      E(lambda d: words(d, 1300, 470, "上げていたのは", 60)), E(lambda d: words(d, 1300, 600, "飽和脂肪", 110, BAD))],
     "結果、悪玉と呼ばれるLDLコレステロールがいちばん低かったのは、なんと、卵を毎日2個食べた食事。値を上げていたのは、卵のコレステロールではなく、飽和脂肪のほうだったんです。"),
    ("card", 15, "ただし、61人で5週間ずつという小さな実験。いい派、3議席です。"),

    ("final", "最終結果、いい派75議席。それでも当選確実が出せないのは、多くが、食べる人と食べない人を比べただけの研究だからです。食べる量が多いほどリスクが高い、というアメリカの結果も、まだ残っています。"),
    ("summary", "今日のまとめです。健康な人なら、1日1個は気にしなくてよさそう。気をつけたいのは、卵そのものより、一緒に食べるベーコンやバターなどの飽和脂肪。そして、糖尿病や脂質異常症の方は控えめに。心配な方は、お医者さんに相談してくださいね。100年かけて、悪者から返り咲いた卵。でも、まだ当選確実ではありません。",
     ["健康な人", "気をつけたい", "糖尿病", "心配な方"]),
    ("next", "次回のテーマは「お酒は少しなら体にいい？」。赤ワインは体にいい、という話は本当なのでしょうか。"),
    ("outro", "新常識クロニクルでは、これからも、健康や暮らしの「いい派」と「悪い派」の論争を、どんどん分析していきます。次に取り上げてほしい論争があれば、ぜひコメントで教えてください。チャンネル登録と高評価も、よろしくお願いします！"),
]


# ---------- 卵の回だけの画面 ----------
def hook_maker(narr):
    """卵が1個出て「1日1個まで」→ 2個目に✕(がまん)→「2015年 国の基準から消えた」のハンコ。"""
    def make(alen, lead):
        at = lambda k: lead + narr.index(k) / len(narr) * alen  # noqa: E731
        t1, t2, t3 = at("卵は") - 0.1, at("2個目"), at("2015年")

        def frame(t):
            im, d = stage()
            lay = blank()
            dd = ImageDraw.Draw(lay)
            k1 = seg(t, t1, t1 + 0.4)
            if k1 > 0:
                egg(dd, 720, 520, 300 * (0.6 + 0.4 * out_back(k1)))
            k2 = seg(t, t2, t2 + 0.4)
            if k2 > 0:
                egg(dd, 1200, 520, 300 * (0.6 + 0.4 * out_back(k2)), fill=(236, 232, 224))
            im = im.convert("RGBA")
            im.alpha_composite(lay)
            d = ImageDraw.Draw(im)
            if k1 > 0:
                chip(d, W / 2, 190, "卵は1日1個まで", GOOD, int(64 * (0.6 + 0.4 * out_back(k1))))
            k2b = seg(t, t2 + 0.5, t2 + 0.9)
            if k2b > 0:
                cw.cross(d, 1300, 390, 60 * out_back(k2b))
                text(d, (1200, 760), "がまん…", 56, WHITE, anchor="mm")
            k3 = seg(t, t3, t3 + 0.45)
            if k3 > 0:
                sc = 1.5 - 0.5 * out_back(k3)
                cx, cy = W / 2, 900
                bw, bh = 640 * sc, 80 * sc
                d.rounded_rectangle([cx - bw, cy - bh, cx + bw, cy + bh], radius=24 * sc, fill=(220, 60, 60), outline=WHITE,
                                    width=max(3, int(8 * sc)))
                text(d, (cx, cy), "2015年 国の基準から消えた", int(68 * sc), WHITE, anchor="mm")
            return im.convert("RGB")
        return frame, t3 + 0.8
    return WithAudio(make)


def rules_frame_maker(narr, keys):
    rows = [("国・大きな学会の公式な判断", "15議席"), ("たくさんの研究のまとめ", "10議席"),
            ("数十万人の追跡調査", "6議席"), ("条件が限られた結果", "3議席")]

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
                text(d, (cx - hw + 50 * sc, cy), k, int(52 * sc), INK, anchor="lm")
                text(d, (cx + hw - 50 * sc, cy), v, int(60 * sc), GOOD, anchor="rm")
            text(d, (W / 2, 880), "※ 議席は演出のための目安です", 36, SUB, heavy=False, anchor="mm")
            return im
        return frame, times[-1] + 0.6
    return WithAudio(make)


def rules_intro_frame(t):
    im = parliament_frame("", "研究の歴史を選挙に見立てる", 50, 50, t, tag="見方")
    d = ImageDraw.Draw(im)
    for x, lab, c in ((W / 2 - 400, "卵は食べていい", GOOD), (W / 2 + 400, "控えるべき", BAD)):
        k = seg(t, 0.8, 1.2)
        if k > 0:
            chip(d, x, 300, lab, c, int(46 * (0.6 + 0.4 * out_back(k))))
    return im


def summary_maker(narr, keys):
    items = [("健康な人なら", "1日1個は気にしなくてよさそう", GOOD), ("気をつけたいのは", "ベーコン・バターなどの飽和脂肪", BAD),
             ("糖尿病・脂質異常症の人は", "控えめに", BAD), ("心配な人は", "お医者さんに相談", INK)]

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


def next_frame(t):
    im, d = stage()
    text(d, (W / 2, 260), "次回の論争", 70, TRIM, anchor="mm")
    k = out_back(seg(t, 0.3, 0.8))
    if k > 0:
        im = im.convert("RGBA")
        lay = blank()
        wine(ImageDraw.Draw(lay), W / 2, 360, 340 * (0.6 + 0.4 * k), color=WHITE)
        im.alpha_composite(lay)
        im = im.convert("RGB")
        d = ImageDraw.Draw(im)
    text(d, (W / 2, 850), "お酒は少しなら体にいい？", 100, WHITE, anchor="mm")
    return im


TOPICS = ["お酒は少しなら体にいい？", "1日1万歩は必要？", "サウナは長生きのもと？", "朝ごはんは食べるべき？", "塩は減らすほどいい？", "牛乳は体にいい？"]


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


# ---------- 組み立て ----------
def dur(narr):
    return max(3.0, len(narr) / 8.0 + 0.8)


def card_of(idx):
    year, country, kindx, title, facts, picto, before, after, headline, source = EVENTS[idx - 1]
    rows = [[(s, cw.color_of(c)) for s, c in row] for row in title]
    diff = after - before
    return Card(year, country, kindx, rows, facts, picto, before, after,
                f"{'いい派' if diff > 0 else '悪い派'} +{abs(diff)}議席", source)


def build_plan():
    """(描く関数, 動く秒数, 合計秒数, 台本の行) のリスト。"""
    plan, last_chapter = [], None
    for sc in SCENES:
        kind, narr = sc[0], sc[-1] if sc[0] not in ("rules", "summary", "chapter_start") else sc[1]
        if kind == "hook":
            plan.append((hook_maker(narr), 0, dur(narr), ("つかみ", "卵は1日1個まで → 2015年 国の基準から消えた", narr)))
        elif kind == "title":
            img = os.path.join(OUT, "00_title.png")
            series_card(*EPISODES["egg_war"]).save(img)
            from PIL import Image
            plan.append(((lambda im: lambda t: im)(Image.open(img)), 0, dur(narr), ("タイトル", "新常識クロニクル:卵は1日1個まで？", narr)))
        elif kind == "rules_intro":
            plan.append((rules_intro_frame, 1.3, dur(narr), ("ルール説明", "100議席・食べていい派 vs 控えるべき派・50対50", narr)))
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
            idx = sc[1]
            e = EVENTS[idx - 1]
            plan.append((card_of(idx).frame, Card.ANIM_END, max(dur(narr), Card.ANIM_END + 1.0),
                         (f"研究カード {e[0]}", f"{e[6]}→{e[7]}", narr)))
        elif kind == "seats":
            year, _, _, _, _, _, before, after, headline, _ = EVENTS[sc[1] - 1]
            plan.append(((lambda y, h, b, a: lambda t: parliament_frame(y, h, b, a, t))(year, headline, before, after),
                         2.6, max(dur(narr), 3.6), (f"開票速報 {year}", f"{before}→{after}", narr)))
        elif kind == "final":
            plan.append((lambda t: cw.final_frame(EVENTS[-1][7], t), 2.6, dur(narr), ("結果", "", narr)))
        elif kind == "summary":
            plan.append((summary_maker(sc[1], sc[2]), 0, dur(sc[1]), ("まとめ", "", sc[1])))
        elif kind == "next":
            plan.append((next_frame, 1.0, dur(narr), ("次回予告", "お酒は少しなら体にいい？", narr)))
        elif kind == "outro":
            plan.append((outro_frame, 4.2, dur(narr), ("エンディング", "チャンネル登録・今後の論争", narr)))
    return plan


def write_script(plan):
    total = 0.0
    lines = ["# 台本(物語版):卵は1日1個まで？ 〜「いい派」vs「悪い派」論争の行方〜", "",
             "作成：2026-11-22 / 状態：初稿。`scripts/egg_story.py` の SCENES から自動で作っています(台本を直すときは SCENES を直す)。", "",
             f"ナレーション合計：約{sum(len(p[3][2]) for p in plan):,}字。場面の長さは合成したナレーションの長さで決まる。", "",
             "冒頭はサムネイル(「卵は1日1個まで？」)の続きとして、最初の一言から本題に入る。番組紹介はタイトル画面の1文だけ。", "",
             "| 時間 | 場面 | 画面のテロップ・内容 | ナレーション |", "|---|---|---|---|"]
    for _, _, sec, (name, tl, narr) in plan:
        m, s = divmod(int(total), 60)
        lines.append(f"| {m}:{s:02d} | {name} | {tl} | {narr} |")
        total += sec
    m, s = divmod(int(total), 60)
    lines += ["", f"合計：約{m}分{s:02d}秒", "",
              "## 議席の推移", "", "| # | 年 | 国 | 種類 | 前 → 後 | 出典 |", "|---|---|---|---|---|---|"]
    for i, e in enumerate(EVENTS, 1):
        lines.append(f"| {i} | {e[0]} | {e[1]} | {e[2]} | {e[6]} → {e[7]} | {e[9].replace('出典：', '')} |")
    lines += ["", "1つの発表に「いい結果」と「悪い結果」がある場合は差し引き(1999年・2013年は いい派+6/+10 から糖尿病の人の結果 −3)。",
              "米国心臓協会(AHA)は政府機関ではないが、影響の大きい学会の公式勧告として15議席にしている。", "",
              "## 公開前に原文で確認すること",
              "- 第1話:アニチコフ(Anitschkow)の1913年の実験。ウサギに与えたのが「卵黄」と「純粋なコレステロール」の両方であること",
              "- 1968年 AHA の「卵は週3個まで・1日300mg未満」(二次資料で確認済み。原文は AHA の1968年の声明)",
              "- 1999年 Hu ら(JAMA):約12万人(男性 約3.8万人を8年、女性 約8万人を14年)、糖尿病の人でリスクが高い",
              "- **2005年版の食事摂取基準のコレステロール目標量(男性750mg未満/女性600mg未満、18歳以上)**:検索では数字を確かめられなかった。厚生労働省の2005年版・2010年版の本文で確認する",
              "- 2006年 JPHC(Nakamura ら):90,735人で卵の摂取と心臓病の関係なし(確認済み)。年齢「40〜69歳」",
              "- 2013年 Rong ら(BMJ):「17の報告」、糖尿病の人で心臓病リスクが高い",
              "- 2015年版の食事摂取基準:撤廃の理由の書き方(「目標量を算定するのに十分な科学的根拠が得られなかった」)",
              "- 2016年 アメリカの食事指針(2015-2020):300mgの上限を外したが「できるだけ少なく」とも書いている",
              "- 2018年 China Kadoorie Biobank:416,213人(確認済み)、追跡期間「約9年」",
              "- **2019年 Zhong ら(JAMA)**:29,615人・中央値17.5年・半個ごとに心臓病+6%/死亡+8%(検索では人数と%を確かめられなかった)",
              "- 2019年12月 AHA(Carson ら):健康な人は1日1個、コレステロール値が正常な高齢者は1日2個まで(二次資料で確認)",
              "- 2020年版の食事摂取基準:脂質異常症の重症化予防のため200mg/日未満が望ましい(確認済み)。卵1個(約50g)のコレステロール量",
              "- 2021年 Zhuang ら(PLOS Medicine):521,120人・中央値16年・半個ごとに死亡+7%(確認済み)。白身・卵代替品は低め",
              "- 2025年1月 ASPREE(Nutrients):8,756人・70歳以上、週1〜6回で心臓病による死亡-29%(確認済み。全死亡は-17%)",
              "- 2025年7月 Carter ら(AJCN):61人・各5週間のクロスオーバー試験(確認済み)", ""]
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


def main():
    os.makedirs(OUT, exist_ok=True)
    plan = build_plan()
    if "--script" in sys.argv:
        total = write_script(plan)
        print(f"台本：{SCRIPT_MD}(約{int(total // 60)}分{int(total % 60):02d}秒、{len(plan)}場面、目安)")
        return
    import numpy as np
    import soundfile as sf
    from narrate import RATE
    LEAD, TAIL = 0.35, 0.55
    voices, new_plan = [], []
    for i, (fn, anim, sec, meta) in enumerate(plan):
        v = cs.voice_for(i, meta[2], os.path.join(OUT, "voice"))
        sec = max(anim + 0.3 if anim else 2.0, LEAD + len(v) / RATE + TAIL)
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
    if "--voice" in sys.argv:   # 声と台本だけ(映像は作らない)
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
    out = os.path.join(OUT, "egg_story_draft.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", wav, "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-ar", "48000", "-c:a", "aac", "-b:a", "160k", "-shortest", out], check=True)
    shutil.rmtree(seg_dir)
    print("done:", out)


if __name__ == "__main__":
    sys.exit(main())
