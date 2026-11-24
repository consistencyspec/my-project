"""赤ワインは体にいい？ 物語版：主な研究を物語にして、研究カードと議席でつなぐ(新常識クロニクル 第3回)。

  .venv/bin/python scripts/wine_story.py           -> output/wine_story/wine_story_draft.mp4(ナレーションつき)
  .venv/bin/python scripts/wine_story.py --script  -> content/wine_war_story.md(台本)だけ作り直す
  .venv/bin/python scripts/wine_story.py --voice   -> 声と台本だけ(映像は作らない)

卵の回(egg_story.py)と同じ型。冒頭はサムネイル(「赤ワインは体にいい？」)の続きとして、最初の一言から本題に入る。
読み上げ：「29%」は数字のあとにパーセント、「1日1杯」は 1日 のあとに少し間を置く(scripts/narrate.py の共通ルール)。
"""
import os
import re
import shutil
import subprocess
import sys

from PIL import ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frames import BAD, GOOD, INK, PANEL, SUB, TRIM, W, WHITE, arrow, bean, font, heart, line, panel, stage, text  # noqa: E402
from motion import Card, blank, out_back, parliament_frame, seg  # noqa: E402
import coffee_war as cw  # noqa: E402
import coffee_story as cs  # noqa: E402
from coffee_story import WithAudio, chapter_start_frame, chip, magnifier, story_frames, words, year_tag  # noqa: E402
import wine_war as ww  # noqa: E402
from wine_war import (bottle, cheese, dna, ex_drinker, flag_fr, glass, globe, grapes, mouse, red_face,  # noqa: E402
                      tv)
from egg_war import wine  # noqa: E402
from thumbnail import EPISODES, series_card  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "output", "wine_story")
SCRIPT_MD = os.path.join(HERE, "..", "content", "wine_war_story.md")
EVENTS = ww.EVENTS
EPISODE = "wine_war"
import narrate  # noqa: E402
# 赤ワインの回で読み間違えやすい語(他の回の声のキャッシュを変えないよう、この回だけで足す)
narrate.MM_DICT += ["赤ワイン/あかワイン", "3〜5杯/さんからごはい", "1杯/いっぱい", "0杯/ぜろはい", "何百本/なんびゃっぽん",
                    "18か国/じゅうはっかこく", "195か国/ひゃくきゅうじゅうごかこく", "87の研究/はちじゅうななのけんきゅう",
                    "13の研究/じゅうさんのけんきゅう", "150g/ひゃくごじゅうグラム", "20g/にじゅうグラム", "40g/よんじゅうグラム",
                    "WHO/ダブリューエイチオー", "60ミニッツ/シックスティミニッツ", "脂っこい/あぶらっこい", "脂/あぶら",
                    "酒石酸/しゅせきさん", "脳卒中/のうそっちゅう", "乳がん/にゅうがん", "大腸がん/だいちょうがん",
                    "純アルコール/じゅんアルコール", "体質/たいしつ", "皮/かわ", "一生/いっしょう", "一方/いっぽう",
                    "主役/しゅやく", "見方/みかた", "飲酒/いんしゅ", "休肝日/きゅうかんび", "全米/ぜんべい",
                    "50対50/ごじゅうたいごじゅう", "4割/よんわり", "40〜59歳/よんじゅうからごじゅうきゅうさい",
                    "65歳/ろくじゅうごさい", "9年/きゅうねん", "1つ目/ひとつめ", "2つ目/ふたつめ", "生まれつき/うまれつき",
                    "下戸/げこ", "強い人/つよいひと", "弱い人/よわいひと", "高リスク/こうリスク"]
# 読み方の設定(この回)。卵の回と同じく、数字・年号・人数・議席は数字のまま送り、読みは辞書で(2026-11-24)
narrate.NUM_STYLE = "dict"
narrate.ICHINICHI_PAUSE = 0.03      # 「1日」のあとにごく短い間(「置きすぎ」の指摘で 0.25→0.03)
narrate.PAUSE_SHORT = 0
narrate.PAUSE_QUOTE_HA = 0
narrate.TEXT_READ += [("下がった", "さがった"), ("1,232人", "千二百三十二にん"), ("78議席", "ななじゅうはち議席"),
                      ("飲む国", "のむくに"), ("WHOヨーロッパ", "WHO<#0.15#>ヨーロッパ"),
                      ("18か国", "じゅうはっかこく"), ("195か国", "ひゃくきゅうじゅうごかこく"), ("60ミニッツ", "シックスティミニッツ"),
                      ("150g", "ひゃくごじゅうグラム"), ("20g", "にじゅうグラム"), ("40g", "よんじゅうグラム"),
                      ("40〜59歳", "よんじゅっさいからごじゅうきゅうさい")]
# 場面ごとの声の差しかえ(台本の文字は変えず、送る文章だけ)。聞き取りで確かめた(2026-11-24)
cs.VOICE_FIX += [("1979年のイギリスから", "センキュウヒャクナナジュウキュウネンのイギリスから")]   # 漢数字・数字だと「1919年」と聞こえた
cs.STEP_COLORS.update({"どうやって？": BAD, "なぜ調べた？": INK, "落とし穴": BAD, "結果": GOOD})


def E(f):
    return f


# ---------- 場面 ----------
# ("story", 話数, 見出し, テロップ, [要素], ナレーション) / ("card", 研究番号, ナレーション) / ("seats", 研究番号, ナレーション)
SCENES = [
    # 冒頭：サムネイル(赤ワインは体にいい？)の続きから、すぐ本題に入る
    ("hook", "「赤ワインは体にいい」。そう聞いて、健康のつもりでグラスを傾けたこと、ありませんか？ ところが今、WHOは「安全な飲酒量はない」と言っているんです。"),
    ("title", "赤ワインは、なぜ体にいいと言われ、なぜ疑われるようになったのか。40年以上にわたる論争を、データで判定します。新常識クロニクル、今日のテーマは「赤ワインは体にいい？」です。"),
    # ルール説明(短く)
    ("rules_intro", "見方はかんたん。研究の歴史を選挙に見立てます。議席は100。オレンジは、少しなら体にいい、と考える派の色。青は、飲まないほうがいい、と考える派の色です。スタートは50対50です。"),
    ("rules", "研究が出るたびに、勝った側に議席が移ります。国やWHOなどの公式な判断は15議席、たくさんの研究のまとめは10議席、数十万人の調査は6議席、条件が限られた結果は3議席です。",
     ["公式な判断", "まとめ", "数十万人", "条件が限られた"]),
    ("chapter_start", "それでは、行ってみましょう！第1話。物語は、1979年のイギリスから始まります。", "第1話", "フレンチ・パラドックス"),

    # 第1話 フレンチ・パラドックス
    ("story", 1, "はじまり", "1979年 イギリスの研究者が18か国を比べると、ワインを多く飲む国ほど心臓病の死亡が少なかった",
     [E(lambda d: year_tag(d, 420, 360, "1979年")), E(lambda d: cw.flags(d, 260, 470, 10, 110)),
      E(lambda d: arrow(d, 900, 990, 600)), E(lambda d: glass(d, 1130, 450, 230)),
      E(lambda d: heart(d, 1420, 470, 180)), E(lambda d: words(d, 1300, 760, "ワインの国は心臓病が少ない", 56, GOOD))],
     "1979年、イギリスの研究者たちが、18か国の統計を比べました。すると、ワインをたくさん飲む国ほど、心臓病で亡くなる人が少なかったんです。"),
    ("card", 1, "ただし、国ごとの平均を比べただけ。食事や医療の違いも混ざっています。いい派がまず3議席。"),
    ("story", 1, "パラドックス", "フランス人はバターやチーズをたっぷり食べるのに、心臓病が少ない",
     [E(lambda d: flag_fr(d, 400, 520, 220)), E(lambda d: cheese(d, 720, 540, 280)),
      E(lambda d: words(d, 1000, 540, "なのに", 64)), E(lambda d: heart(d, 1300, 440, 200)),
      E(lambda d: words(d, 1300, 720, "心臓病が少ない", 64, GOOD))],
     "そして注目されたのが、フランスです。フランス人は、バターやチーズなど、脂っこいものをたっぷり食べるのに、心臓病が少ない。この不思議は「フレンチ・パラドックス」と呼ばれました。"),
    ("story", 1, "テレビ", "1991年 アメリカの人気番組が「答えは赤ワイン」と紹介。赤ワインの売り上げが急増",
     [E(lambda d: year_tag(d, 420, 360, "1991年")), E(lambda d: tv(d, 520, 590, 380, "答えは赤ワイン？")),
      E(lambda d: bottle(d, 1020, 400, 360)), E(lambda d: bottle(d, 1180, 400, 360)), E(lambda d: bottle(d, 1340, 400, 360)),
      E(lambda d: words(d, 1550, 600, "売り上げ↑", 72, GOOD))],
     "1991年、アメリカの人気番組「60ミニッツ」が、フランスの研究者ルノーの「答えは赤ワインだ」という説を紹介します。放送のあと、アメリカでは赤ワインの売り上げが、4割ほど伸びたと言われています。"),
    ("card", 2, "翌年、ルノーは医学誌ランセットに、この説を発表。いい派が3議席を取ります。"),
    ("card", 3, "1995年には、デンマークで約1万3千人を10年以上追いかけた研究が出ます。ワインを1日3〜5杯飲む人は、飲まない人より、死亡リスクが49%低い。一方、ビールでは差がありませんでした。"),
    ("card", 4, "日本でも1999年、40〜59歳の男性を追いかけた研究で、純アルコールで週150g未満、少しだけ飲む人の死亡リスクが、飲まない人より36%低い、という結果が出ます。"),
    ("card", 5, "2002年には、イタリアの研究チームが、約21万人分の研究をまとめて、ワインを飲む人は、心臓や血管の病気が32%少ない、と発表しました。"),
    ("seats", 5, "いい派が78議席、悪い派が22議席。赤ワインは体にいい、という話は、すっかり常識になりました。"),

    # 第2話 主役はレスベラトロール？
    ("story", 2, "主役は？", "注目された成分「レスベラトロール」。ぶどうの皮に多いポリフェノール",
     [E(lambda d: grapes(d, 460, 590, 340)), E(lambda d: arrow(d, 680, 770, 600)),
      E(lambda d: glass(d, 920, 450, 260)),
      E(lambda d: words(d, 1430, 520, "レスベラトロール", 80, GOOD)), E(lambda d: words(d, 1430, 640, "ぶどうの皮に多い", 52))],
     "では、赤ワインの何が体にいいのか。注目されたのが、ぶどうの皮に多い「レスベラトロール」という成分です。皮ごと仕込む赤ワインには、白ワインより多く含まれています。"),
    ("story", 2, "マウス", "2006年 高カロリーの餌のマウスにレスベラトロールを与えると、長生きした",
     [E(lambda d: year_tag(d, 420, 360, "2006年")), E(lambda d: mouse(d, 520, 600, 420)),
      E(lambda d: grapes(d, 900, 600, 200)),
      E(lambda d: words(d, 1420, 540, "死亡 -31%", 100, GOOD)), E(lambda d: words(d, 1420, 670, "高カロリーの餌でも", 52))],
     "2006年、アメリカの研究チームが、高カロリーの餌を食べるマウスに、レスベラトロールを与えると、死亡リスクが31%下がった、と発表。「赤ワインの成分で長生き」と、世界中で話題になりました。"),
    ("card", 6, "ただし、マウスの実験です。いい派が3議席を取ります。"),
    ("story", 2, "落とし穴", "マウスと同じ量を赤ワインでとるには、毎日何百本も飲む計算になる",
     [E(lambda d: mouse(d, 400, 560, 300)), E(lambda d: words(d, 400, 720, "マウスと同じ量", 52)),
      E(lambda d: arrow(d, 640, 730, 580)),
      E(lambda d: bottle(d, 880, 400, 330)), E(lambda d: bottle(d, 1000, 400, 330)), E(lambda d: bottle(d, 1120, 400, 330)),
      E(lambda d: words(d, 1500, 520, "毎日", 64)), E(lambda d: words(d, 1500, 650, "何百本", 110, BAD))],
     "ところが、ここに落とし穴があります。マウスと同じ量を、体重に合わせて赤ワインでとろうとすると、毎日何百本も飲む計算になるんです。"),
    ("story", 2, "キャンティ", "2014年 ワインの産地キャンティ地方で、尿のレスベラトロールを測った",
     [E(lambda d: year_tag(d, 420, 360, "2014年")), E(lambda d: grapes(d, 420, 600, 300)),
      E(lambda d: cw.crowd(d, 640, 450, 4, 2, 140)),
      E(lambda d: words(d, 1500, 540, "長生きと", 64)), E(lambda d: words(d, 1500, 660, "関係なし", 100, BAD))],
     "2014年、イタリアのワインの産地、キャンティ地方で、65歳以上の783人の尿から、レスベラトロールの量を測り、約9年追いかけました。結果、多くとっている人でも、長生きとの関係は見られませんでした。"),
    ("card", 7, "悪い派が3議席を取り返します。"),

    # 第3話 「飲まない人」の落とし穴
    ("story", 3, "なぜ調べた？", "「飲まない人」の中に、病気でお酒をやめた人が混ざっていた",
     [E(lambda d: words(d, 960, 330, "「飲まない人」のグループ", 60)),
      E(lambda d: bean(d, 560, 430, 280)), E(lambda d: words(d, 560, 770, "一生飲まない人", 48)),
      E(lambda d: ex_drinker(d, 1240, 430, 280)), E(lambda d: words(d, 1300, 770, "病気でやめた人", 48, BAD))],
     "そして、悪い派の大きな反撃が始まります。カギは「飲まない人」のグループ。実はその中に、病気になって、お酒をやめた人が混ざっていたんです。もともと体が弱い人がいれば、飲まない人の死亡リスクは高く見えてしまいます。"),
    ("story", 3, "どうやって？", "87の研究を集め、「一生飲まない人」とだけ比べ直した",
     [E(lambda d: cw.papers(d, 360, 420, 300, 5)), E(lambda d: arrow(d, 700, 790, 600)),
      E(lambda d: words(d, 1300, 500, "87の研究", 90)),
      E(lambda d: words(d, 1300, 640, "偏りがないのは13だけ", 60, BAD))],
     "2016年、カナダの研究チームは、87の研究を集めて、比べる相手を「一生飲まない人」などに直して計算し直しました。偏りなく比べられていた研究は、87のうち、わずか13でした。"),
    ("story", 3, "結果", "比べる相手を直すと、少しだけ飲む人の「長生き」は消えた",
     [E(lambda d: glass(d, 470, 430, 280)), E(lambda d: words(d, 470, 800, "少しだけ飲む人", 52)),
      E(lambda d: arrow(d, 720, 810, 600)),
      E(lambda d: words(d, 1300, 520, "長生き効果", 80)), E(lambda d: words(d, 1300, 660, "消えた", 120, BAD))],
     "すると、少しだけ飲む人が長生き、という効果は、消えてしまったんです。"),
    ("card", 8, "悪い派が10議席を取ります。"),
    ("card", 9, "2018年には、195か国のデータを分析した研究が、医学誌ランセットに出ます。心臓には少し得があっても、がんなどの害を合わせると、健康への害がいちばん少ないのは、0杯でした。"),

    # 第4話 遺伝子のくじ引き
    ("story", 4, "なぜ調べた？", "お酒に強いか弱いかは、生まれつきの体質(遺伝子)で決まる",
     [E(lambda d: dna(d, 420, 580, 360)),
      E(lambda d: red_face(d, 800, 420, 300)), E(lambda d: words(d, 800, 770, "すぐ赤くなる", 48, BAD)),
      E(lambda d: words(d, 1400, 520, "生まれつきの", 64)), E(lambda d: words(d, 1400, 650, "くじ引き", 110))],
     "では、本当にお酒そのものの効果なのか。そこで使われたのが、遺伝子です。東アジアには、少し飲んだだけで顔が赤くなる、お酒に弱い体質の人がたくさんいます。強いか弱いかは、生まれつき、くじ引きのように決まります。"),
    ("story", 4, "どうやって？", "2019年 中国の約51万人。体質のちがいで、飲む量と病気の関係を調べた",
     [E(lambda d: year_tag(d, 420, 360, "2019年")), E(lambda d: cw.crowd(d, 280, 430, 5, 2, 120)),
      E(lambda d: words(d, 1330, 520, "約51万人", 96)), E(lambda d: words(d, 1330, 650, "体質のくじ引きを利用", 56))],
     "2019年、イギリスと中国のチームは、中国の約51万人を調べました。お酒に弱い体質の人は、自然と飲む量が少なくなります。体質は生まれつきなので、食事や暮らし方とは関係ありません。だから、体質ごとに病気の数を比べれば、お酒そのものの影響が分かるんです。"),
    ("story", 4, "結果", "体質で飲む量が多い人ほど、脳卒中が多かった。少量でも守る効果なし",
     [E(lambda d: cw.brain(d, 450, 580, 330)), E(lambda d: arrow(d, 690, 780, 600)),
      E(lambda d: words(d, 1300, 500, "飲むほど脳卒中↑", 76, BAD)), E(lambda d: words(d, 1300, 640, "少量でも守る効果なし", 60, BAD))],
     "結果、体質のせいで飲む量が多い人ほど、脳卒中が多く、少しなら脳卒中を防ぐ、という効果は見られませんでした。"),
    ("card", 10, "悪い派が6議席を取ります。これで52対48。いい派の過半数は、ぎりぎりです。"),
    ("card", 11, "そして2023年、WHOヨーロッパ事務局が、公式に発表します。安全な飲酒量はない。少量でも、がんのリスクは上がり、心臓への得は、それを上回らない、と。"),
    ("seats", 11, "いい派が37議席、悪い派が63議席。ついに逆転です！"),
    ("card", 12, "日本でも2024年、厚生労働省が、初めての飲酒ガイドラインを出します。男性の大腸がんは、純アルコールで1日20g、ワインならグラス2杯ほどから、リスクが上がる、などと示しました。"),
    ("card", 13, "一方、2024年の暮れ、アメリカの全米アカデミーズは、少し飲む人は一生飲まない人より、死亡リスクがやや低い、とまとめます。ただし乳がんは高め。差し引きで、いい派が7議席を取ります。"),

    # 第5話 尿で確かめる
    ("story", 5, "なぜ調べた？", "「どれだけ飲んだか」の自己申告は、あてにならない",
     [E(lambda d: glass(d, 470, 430, 280)), E(lambda d: words(d, 470, 800, "申告「グラス1杯」", 48)),
      E(lambda d: magnifier(d, 900, 580, 110)),
      E(lambda d: words(d, 1420, 520, "本当は", 64)), E(lambda d: words(d, 1420, 650, "どれだけ？", 100, BAD))],
     "最後は、スペインからの反撃です。これまでの研究の多くは、どれだけ飲んだかを、本人に答えてもらうだけでした。でも、人は飲んだ量を少なめに答えがちです。"),
    ("story", 5, "どうやって？", "ぶどう特有の成分「酒石酸」を尿で測り、本当にワインを飲んだ量を調べた",
     [E(lambda d: grapes(d, 420, 590, 300)), E(lambda d: arrow(d, 620, 710, 600)),
      E(lambda d: words(d, 1250, 520, "尿の酒石酸", 96)), E(lambda d: words(d, 1250, 650, "地中海食を試した1,232人", 56))],
     "バルセロナ大学などのチームは、ぶどうに多い「酒石酸」という成分を、尿から測りました。対象は、地中海式の食事の試験に参加した、心臓病になりやすい高齢者など、1,232人です。"),
    ("story", 5, "結果", "グラス半分〜1杯ほど飲む人は、心臓・血管の病気が50%少なかった",
     [E(lambda d: glass(d, 470, 430, 280)), E(lambda d: words(d, 470, 800, "1日グラス半分〜1杯", 48, GOOD)),
      E(lambda d: arrow(d, 720, 810, 600)), E(lambda d: heart(d, 1000, 470, 200)),
      E(lambda d: words(d, 1450, 600, "-50%", 140, GOOD))],
     "結果、1日グラス半分から1杯ほど飲んでいた人は、ほとんど飲まない人より、心臓や血管の病気が50%少なかったんです。"),
    ("card", 14, "ただし、心臓病になりやすい人たちの観察研究。いい派が3議席を取ります。"),

    ("final", "最終結果は、いい派が32議席。一時は78議席あった「赤ワインは体にいい」派が、大きく議席を減らしました。ただ、当選確実はまだ出せません。くじ引きの実験で、ワインを飲ませ続けた研究は、まだないからです。"),
    ("summary", "今日のまとめです。体にいいと思って、飲み始める必要はなさそう。少量でも、がんのリスクは上がります。飲むなら、1日グラス1杯ほどまでにして、飲まない日もつくりましょう。そして、顔がすぐ赤くなる方は特に控えめに。心配な方は、お医者さんに相談してくださいね。40年かけて、ヒーローから容疑者になった赤ワイン。でも、まだ判決は出ていません。",
     ["必要は", "がんのリスク", "顔が", "心配な方"]),
    ("next", "次回のテーマは「1日1万歩は必要？」。その数字、どこから来たのでしょうか。"),
    ("outro", "新常識クロニクルでは、これからも、健康や暮らしの、いい派と悪い派の論争を、どんどん分析していきます。次に取り上げてほしい論争があれば、ぜひコメントで教えてください。チャンネル登録と高評価も、よろしくお願いします！"),
]


# ---------- 赤ワインの回だけの画面 ----------
def hook_maker(narr):
    """グラスがポンと出て「赤ワインは体にいい」→ ハート →「WHO 安全な飲酒量はない」のハンコ。"""
    def make(alen, lead):
        at = lambda k: lead + narr.index(k) / len(narr) * alen  # noqa: E731
        t1, t2, t3 = at("赤ワインは") - 0.1, at("健康の"), at("WHO")

        def frame(t):
            im, d = stage()
            lay = blank()
            dd = ImageDraw.Draw(lay)
            k1 = seg(t, t1, t1 + 0.4)
            if k1 > 0:
                wine(dd, 760, 330, 420 * (0.6 + 0.4 * out_back(k1)), color=WHITE)
            k2 = seg(t, t2, t2 + 0.4)
            if k2 > 0:
                heart(dd, 1200, 380, 220 * (0.6 + 0.4 * out_back(k2)))
            im = im.convert("RGBA")
            im.alpha_composite(lay)
            d = ImageDraw.Draw(im)
            if k1 > 0:
                chip(d, W / 2, 190, "赤ワインは体にいい", GOOD, int(64 * (0.6 + 0.4 * out_back(k1))))
            k3 = seg(t, t3, t3 + 0.45)
            if k3 > 0:
                sc = 1.5 - 0.5 * out_back(k3)
                cx, cy = W / 2, 900
                bw, bh = 640 * sc, 80 * sc
                d.rounded_rectangle([cx - bw, cy - bh, cx + bw, cy + bh], radius=24 * sc, fill=BAD, outline=WHITE,
                                    width=max(3, int(8 * sc)))
                text(d, (cx, cy), "WHO「安全な飲酒量はない」", int(68 * sc), WHITE, anchor="mm")
            return im.convert("RGB")
        return frame, t3 + 0.8
    return WithAudio(make)


def rules_frame_maker(narr, keys):
    rows = [("国・WHOなどの公式な判断", "15議席"), ("たくさんの研究のまとめ", "10議席"),
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
    for x, lab, c in ((W / 2 - 400, "少しなら体にいい", GOOD), (W / 2 + 400, "飲まないほうがいい", BAD)):
        k = seg(t, 0.8, 1.2)
        if k > 0:
            chip(d, x, 300, lab, c, int(46 * (0.6 + 0.4 * out_back(k))))
    return im


def summary_maker(narr, keys):
    items = [("健康のために", "飲み始める必要はなさそう", BAD), ("少量でも", "がんのリスクは上がる", BAD),
             ("顔がすぐ赤くなる人は", "特に控えめに", BAD), ("心配な人は", "お医者さんに相談", INK)]

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


NEXT_TITLE = "1日1万歩は必要？"


def next_frame(t):
    im, d = stage()
    text(d, (W / 2, 260), "次回の論争", 70, TRIM, anchor="mm")
    k = out_back(seg(t, 0.3, 0.8))
    if k > 0:
        im = im.convert("RGBA")
        lay = blank()
        cw.foot(ImageDraw.Draw(lay), W / 2, 560, 360 * (0.6 + 0.4 * k))
        im.alpha_composite(lay)
        im = im.convert("RGB")
        d = ImageDraw.Draw(im)
    text(d, (W / 2, 850), NEXT_TITLE, 100, WHITE, anchor="mm")
    return im


TOPICS = ["1日1万歩は必要？", "サウナは長生きのもと？", "朝ごはんは食べるべき？", "塩は減らすほどいい？", "牛乳は体にいい？", "日光浴は体にいい？"]



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
            plan.append((hook_maker(narr), 0, dur(narr), ("つかみ", "赤ワインは体にいい → WHO「安全な飲酒量はない」", narr)))
        elif kind == "title":
            img = os.path.join(OUT, "00_title.png")
            series_card(*EPISODES[EPISODE]).save(img)
            from PIL import Image
            plan.append(((lambda im: lambda t: im)(Image.open(img)), 0, dur(narr), ("タイトル", "新常識クロニクル:赤ワインは体にいい？", narr)))
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
            plan.append((next_frame, 1.0, dur(narr), ("次回予告", NEXT_TITLE, narr)))
        elif kind == "outro":
            plan.append((outro_frame, 4.2, dur(narr), ("エンディング", "チャンネル登録・今後の論争", narr)))
    return plan


def write_script(plan):
    total = 0.0
    lines = ["# 台本(物語版):赤ワインは体にいい？ 〜「いい派」vs「悪い派」論争の行方〜", "",
             "作成：2026-11-23 / 状態：初稿。`scripts/wine_story.py` の SCENES から自動で作っています(台本を直すときは SCENES を直す)。", "",
             f"ナレーション合計：約{sum(len(p[3][2]) for p in plan):,}字。場面の長さは合成したナレーションの長さで決まる。", "",
             "冒頭はサムネイル(「赤ワインは体にいい？」)の続きとして、最初の一言から本題に入る。番組紹介はタイトル画面の1文だけ。", "",
             "読み上げのルール:「49%」は数字のあとに「パーセント」と読む。「1日1杯」「1日20g」のように 1日 のあとに量が続くときは、1日 のあとに少し間(0.25秒)を置く(`scripts/narrate.py` の PERCENT_READING / ICHINICHI_PAUSE)。", "",
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
    lines += ["", "1つの発表に「いい結果」と「悪い結果」がある場合は差し引き(2024年 全米アカデミーズは いい派+10 から乳がんの結果 −3)。",
              "WHO欧州事務局の声明(Lancet Public Health 掲載)は国の基準ではないが、国際機関の公式見解として15議席にしている。",
              "アルコール全般の研究も入れている(1999年 日本・2016年・2018年・2019年・2023年・2024年)。赤ワインだけの研究は少なく、「赤ワインは体にいい」は「お酒は少しなら体にいい」の代表として語られてきたため。", "",
              "## 公開前に原文で確認すること",
              "- 1979年 St Leger ら(Lancet 1979;1:1017-20):18か国、虚血性心疾患の死亡とワイン消費の負の関係(確認済み)",
              "- 1991年「60ミニッツ」:放送後の赤ワインの売り上げ増は資料で「4週間で44%」「1992年に約40%」とまちまち。台本は「4割ほど伸びたと言われています」とぼかした",
              "- 1992年 Renaud & de Lorgeril(Lancet 1992;339:1523-6)「Wine, alcohol, platelets, and the French paradox」:書誌を原文で確認",
              "- 1995年 Grønbæk ら(BMJ 1995;310:1165-9):13,285人・10〜12年、ワイン1日3〜5杯で死亡 RR 0.51(=−49%)、ビールは影響なし(確認済み)",
              "- **1999年 Tsugane ら(Am J Epidemiol 1999;150:1201-7)**:40〜59歳の男性・1990〜96年、週1〜149gで RR 0.64(=−36%)。参照は「飲まない人」。人数(約1万9千人)は未確認のため台本に入れていない",
              "- 2002年 Di Castelnuovo ら(Circulation 2002;105:2836-44):ワインは13研究・209,418人で RR 0.68(=−32%)(確認済み)",
              "- 2006年 Baur ら(Nature 2006;444:337-42):高カロリー食のマウスで死亡 HR 0.69(=−31%)(確認済み)",
              "- **「毎日何百本」**:Baur らの量(体重1kgあたり約22mg/日)を60kgの人に当てはめると約1.3g/日。赤ワインのレスベラトロールは1リットルあたり数mg程度なので、数百本になる(自分で計算。原文の値で確かめる)",
              "- 2014年 Semba ら(JAMA Intern Med 2014;174:1077-84):InCHIANTI・65歳以上783人・約9年、尿のレスベラトロールと死亡・炎症・心臓病・がんに関係なし(確認済み)",
              "- 2016年 Stockwell ら(J Stud Alcohol Drugs 2016;77:185-98):87研究、調整前 RR 0.86 → 調整後 0.97、偏りのない研究は13(確認済み)",
              "- 2018年 GBD 2016 Alcohol Collaborators(Lancet 2018;392:1015-35):195か国、害を最小にする量は0杯(確認済み)。「23種類の病気」は原文で確認",
              "- 2019年 Millwood ら(Lancet 2019;393:1831-42):512,715人、遺伝子は約16万人、遺伝子から予測した飲酒量と脳卒中は正の関係、少量の保護効果なし(確認済み)。心筋梗塞ははっきりしない",
              "- 2023年 WHO欧州(Lancet Public Health 2023;8:e6-e7、2023年1月4日の発表):「No level of alcohol consumption is safe for our health」(確認済み)",
              "- **2024年 厚生労働省「健康に配慮した飲酒に関するガイドライン」(2024年2月19日)**:男性の大腸がんは1日20g以上でリスク上昇、生活習慣病のリスクを高める量は男性40g・女性20g以上。ガイドライン本体(PDF)で表の数字を確認する。「ワインならグラス2杯ほど」はワイン12%・グラス約100mlで計算(20÷0.8÷0.12≒210ml)",
              "- 2024年12月 全米アカデミーズ「Review of Evidence on Alcohol and Health」:少量の飲酒は一生飲まない人より全死亡が低い(中程度の確かさ)、乳がんは高い(確認済み)。「16%低い」は未確認のため台本に入れていない",
              "- 2025年 Domínguez-López ら(Eur Heart J 2025;46:161-72、2024年12月オンライン):PREDIMED 1,232人、尿の酒石酸。グラス半分〜1杯/日(12〜35μg/mL)で HR 0.50(=−50%)。事後に分けた区分であること・対象が心臓病の高リスク者であること(確認済み)", ""]
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
    """声の長さの目安になる文字数(辞書で読ませる数字は読み方の長さで数える。間の記号は除く)。"""
    t = re.sub(r"<#[\d.]+#>", "", narrate.mm_text(narr))
    for entry in narrate.mm_tone(narr)[len(narrate.MM_DICT):]:
        k, v = entry.split("/", 1)
        t = t.replace(k, v)
    return len(t)


def voiced_sec(narr, v):
    """声の長さから、わざと入れた間(<#秒#>。実際は指定の約2.5倍あく)を引いた秒数。"""
    from narrate import RATE
    pauses = sum(float(x) for x in re.findall(r"<#([\d.]+)#>", narrate.mm_text(narr)))
    return max(0.5, len(v) / RATE - 2.5 * pauses)


def check_voices(plan, tries=3):
    """文字数に比べて長すぎる声(変な声・笑い声などが混ざった声)を見つけて作り直す。

    2026-11-23:冒頭の声に4秒ほど変な音が入っていたのに気づけなかったため追加。"""
    import numpy as np
    from narrate import RATE
    cache = os.path.join(OUT, "voice")
    rates = []
    for i, (_, _, _, meta) in enumerate(plan):
        v = cs.voice_for(i, meta[2], cache)
        rates.append(spoken_len(meta[2]) / voiced_sec(meta[2], v))
    med = float(np.median(rates))
    for i, (_, _, _, meta) in enumerate(plan):
        n = 0
        while rates[i] < med * 0.82 and n < tries and "--fix-voices" in sys.argv:   # 作り直しは指定したときだけ(確認済みの声を勝手に変えない)
            n += 1
            print(f"  ! 声が長すぎる({meta[0]}、{rates[i]:.1f}字/秒、ふつうは{med:.1f})ので作り直し {n}/{tries}", flush=True)
            v = cs.voice_for(i, meta[2], cache, fresh=True)
            rates[i] = spoken_len(meta[2]) / voiced_sec(meta[2], v)
        if rates[i] < med * 0.82:
            print(f"  !! 声が長め:{meta[0]}(耳で確認。作り直すなら --fix-voices)", flush=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    plan = build_plan()
    if "--script" in sys.argv:
        total = write_script(plan)
        print(f"台本：{SCRIPT_MD}(約{int(total // 60)}分{int(total % 60):02d}秒、{len(plan)}場面、目安)")
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
    out = os.path.join(OUT, "wine_story_draft.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", wav, "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-ar", "48000", "-c:a", "aac", "-b:a", "160k", "-shortest", out], check=True)
    shutil.rmtree(seg_dir)
    print("done:", out)


if __name__ == "__main__":
    sys.exit(main())
