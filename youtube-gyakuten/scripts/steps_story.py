"""一日1万歩の呪縛 物語版：主な研究を物語にして、研究カードと議席でつなぐ(新常識クロニクル 第4回)。

  .venv/bin/python scripts/steps_story.py           -> output/steps_story/steps_story_draft.mp4(ナレーションつき)
  .venv/bin/python scripts/steps_story.py --script  -> content/steps_war_story.md(台本)だけ作り直す
  .venv/bin/python scripts/steps_story.py --voice   -> 声と台本だけ(映像は作らない)

赤ワインの回(wine_story.py)と同じ型。冒頭はサムネイル(「一日1万歩の呪縛」)の続きとして、最初の一言から本題に入る。
読み方(2026-11-24 指示):一日=イチニチ、1万歩=イチマンポ、年号の年=ネン、8=ハチ、数字のあとの人=ニン。
台本の文字はそのままにして、声に送る文章だけを voice_text() で読み方に直す。
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
import steps_war as sw  # noqa: E402
from steps_war import calendar, curve, flag_nl, flag_pl, man_char, pedometer, shoe, town, walker  # noqa: E402
from thumbnail import EPISODES, series_card  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "output", "steps_story")
SCRIPT_MD = os.path.join(HERE, "..", "content", "steps_war_story.md")
EVENTS = sw.EVENTS
EPISODE = "steps_war"
import narrate  # noqa: E402
# 1万歩の回で読み間違えやすい語(他の回の声のキャッシュを変えないよう、この回だけで足す)
narrate.MM_DICT += ["万歩計/まんぽけい", "歩数計/ほすうけい", "歩数/ほすう", "速歩き/はやあるき", "頭打ち/あたまうち",
                    "呪縛/じゅばく", "認知症/にんちしょう", "厚生労働省/こうせいろうどうしょう", "京都大学/きょうとだいがく",
                    "山佐時計計器/やまさとけいけいき", "合言葉/あいことば", "上限/じょうげん", "中之条町/なかのじょうまち",
                    "群馬県/ぐんまけん", "青柳幸利/あおやぎゆきとし", "東京都健康長寿医療センター/とうきょうとけんこうちょうじゅいりょうセンター",
                    "24時間/にじゅうよじかん", "20分/にじゅっぷん", "60歳/ろくじゅっさい", "60歳以上/ろくじゅっさいいじょう", "60歳未満/ろくじゅっさいみまん",
                    "65歳以上/ろくじゅうごさいいじょう", "72歳/ななじゅうにさい", "15ポイント/じゅうごポイント",
                    "高血圧/こうけつあつ", "糖尿病/とうにょうびょう", "持病/じびょう", "大部分/だいぶぶん", "一時/いちじ",
                    "東京オリンピック/とうきょうオリンピック", "17の研究/じゅうななのけんきゅう", "12の研究/じゅうにのけんきゅう",
                    "26の研究/にじゅうろくのけんきゅう", "57の研究/ごじゅうななのけんきゅう", "15の調査/じゅうごのちょうさ",
                    "2か月後/にかげつご", "4年あまり/よねんあまり", "1週間/いっしゅうかん", "高齢/こうれい", "元気な人/げんきなひと"]
import motion  # noqa: E402
motion.LABELS[:] = ["必要派", "不要派"]   # この回は「いい派・悪い派」ではなく「必要派・不要派」(2026-11-24 指示)
narrate.NUM_STYLE = "dict"           # 数字・議席・対は数字のまま送り、読みは辞書で(卵・赤ワインの回と同じ)
narrate.ICHINICHI_PAUSE = 0.03
narrate.PAUSE_SHORT = 0
narrate.PAUSE_QUOTE_HA = 0
narrate.TEXT_READ += [("下がり", "さがり")]

# ---------- 声に送る文章の読み方(この回の指示。台本の文字は変えない) ----------
HATCHI_GAP = "<#0.05#>"   # 「ジュウ」「ヒャク」のすぐあとの8は「バチ」と濁るので、ごく短い間をはさんで「ハチ」と読ませる(赤ワインの回と同じ)
KANJI = "〇一二三四五六七八九"
YAKU_GAP = "<#0.05#>"   # 「約」のあとの間(0.1 は「置きすぎ」だった。0 だと間がない)


def kata(t):
    return "".join(chr(ord(c) + 0x60) if "ぁ" <= c <= "ゖ" else c for c in t)


def hachi(t):
    return re.sub(r"(じゅう|ひゃく|ぴゃく|びゃく)はち", lambda m: m.group(1) + HATCHI_GAP + "はち", t)


def year_voice(y):
    """2024 → ニセンニジュウヨネン、1965 → センキュウヒャク、ロクジュウゴネン(年号はカタカナ+読点の候補D。4で終わる年は「ヨネン」、年はネン)。"""
    y = int(y)
    head = "にせん" if y // 1000 == 2 else "せんきゅうひゃく"
    rest = y % 1000 if y // 1000 == 2 else y % 100
    r = narrate.kana(rest)
    r = (r[:-2] + "よ") if rest % 10 == 4 else r
    sep = "" if y // 1000 == 2 else "、"   # 2000年代は読点なし(赤ワインの回の「ニセンニネン」に合わせる)、1900年代は候補D(読点あり)
    return kata(head) + (sep + kata(hachi(r)) if rest else "") + "ネン"


def steps_voice(n):
    """8700 → ハッセンナナヒャッポ(歩の読み方:いっぽ・さんぽ・ろっぽ・はっぽ・じゅっぽ・ひゃっぽ・せんぽ・まんぽ、ほかは「ほ」)。"""
    k = hachi(narrate.big_kana(n))
    for end, rep in (("いち", "いっぽ"), ("さん", "さんぽ"), ("ろく", "ろっぽ"), ("はち", "はっぽ"), ("じゅう", "じゅっぽ"),
                     ("ひゃく", "ひゃっぽ"), ("ぴゃく", "ぴゃっぽ"), ("びゃく", "びゃっぽ"), ("せん", "せんぽ"), ("ぜん", "ぜんぽ"),
                     ("まん", "まんぽ")):
        if k.endswith(end):
            return kata(k[: -len(end)] + rep)
    return kata(k + "ほ")


def kanji_big(n):
    man, rest = divmod(n, 10000)
    return ((narrate.kanji_num(man) or "") + "万" if man else "") + (narrate.kanji_num(rest) if rest else "")


def voice_text(narr):
    # 2007年:カタカナ・ひらがな・数字+辞書・漢字では「とし」と読まれた。ナナとネンの間にごく短い間を入れたら直った(2026-11-28 候補Aに決定)
    narr = narr.replace("2007年", "ニセンナナ<#0.03#>ネン")
    t = re.sub(r"(\d{4})年", lambda m: year_voice(m.group(1)), narr)
    t = t.replace("一日", "イチニチ").replace("下がった", "さがった").replace("得をする", "とくをする")
    # 2026-11-24 の指摘:焦る=アセル、1月=イチガツ、十分=ジュウブン、41%=ヨンジュウイチパーセント、青柳幸利=アオヤギユキトシ
    t = (t.replace("焦った", "アセった").replace("1月", "イチガツ").replace("十分", "ジュウブン")
          .replace("41%", "ヨンジュウイチパーセント").replace("青柳幸利", "アオヤギユキトシ"))
    # 2回目の指摘(2026-11-24):3月=サンガツ、7万8千人=ナナマンハッセンニン、「は約」=ワヤク(「早く」と聞こえた)
    t = t.replace("3月", "サンガツ").replace("約7万8千人", "約ななまんはっせんにん").replace("については約", "についてわ約")
    # 4回目の指摘(2026-11-28):群馬県中之条町=ぐんまけん、なかのじょうまち(群馬県のあとに少しの間)
    t = t.replace("群馬県の中之条町", "ぐんまけん、なかのじょうまち")
    # 歩数:「6,000歩から8,000歩」「1万2千歩」「1万歩」→ カタカナ(1万歩=イチマンポ)
    t = re.sub(r"([\d,]+万?(?:\d+千)?)歩", lambda m: steps_voice(narrate.jp_number(m.group(1))), t)
    # 数字+人 → 漢数字+「にん」(赤ワインの回で「ヒト」と読まれたのを直した書き方)
    t = re.sub(r"([\d,]+万?(?:\d+千)?)人", lambda m: kanji_big(narrate.jp_number(m.group(1))) + "にん", t)
    # 「約」のあとに、ほんの少しの間(2026-11-24 指摘)
    t = re.sub(r"約(?=[\dァ-ヶ一二三四五六七八九十百千万])", "約" + YAKU_GAP, t)
    return t


_voice_for = cs.voice_for


def _steps_voice_for(i, narr, cache, emotion=None, fresh=False):
    # 「ついに逆転」の場面は落ち着いた声(赤ワインの回と同じ)。笑い・はしゃいだ声は使わない
    return _voice_for(i, voice_text(narr), cache, emotion=emotion or ("calm" if "逆転です" in narr else None), fresh=fresh)


cs.voice_for = _steps_voice_for

# 場面だけの読み方辞書(その場面の声だけ変わる。ほかの場面の声は作り直さない)
# 4回目の指摘(2026-11-28):3:44・4:01 の「必要派」の派を「は」と読ませる。かなの「は」は助詞の「わ」、カタカナ1文字は笑い声になるので、辞書で指定する
SCENE_TONE = {"必要派も黙って": ["必要派/ひつようは"]}
_mm_tone = narrate.mm_tone


def _scene_tone(text):
    extra = [e for k, v in SCENE_TONE.items() if k in text for e in v]
    return _mm_tone(text) + extra if extra else _mm_tone(text)


narrate.mm_tone = _scene_tone
cs.STEP_COLORS.update({"どうやって？": BAD, "なぜ調べた？": INK, "結果": GOOD, "なぜ1万？": BAD})


def E(f):
    return f


# ---------- 場面 ----------
# ("story", 話数, 見出し, テロップ, [要素], ナレーション) / ("card", 研究番号, ナレーション) / ("seats", 研究番号, ナレーション)
SCENES = [
    # 冒頭：サムネイル(一日1万歩の呪縛)の続きから、すぐ本題に入る
    ("hook", "「一日1万歩、歩きましょう」。スマホの歩数を見て、今日はまだ足りない、と焦ったこと、ありませんか？ ところがこの1万歩、実は、研究から生まれた数字ではなかったんです。"),
    ("title", "一日1万歩は、どこから来て、本当に必要なのか。60年にわたる論争を、データで判定します。新常識クロニクル、今日のテーマは「一日1万歩の呪縛」です。"),
    # ルール説明(短く)
    ("rules_intro", "見方はかんたん。研究の歴史を選挙に見立てます。議席は100。オレンジは、一日1万歩は必要、と考える必要派。青は、そんなに歩かなくていい、と考える不要派です。スタートは50対50です。"),
    ("rules", "研究が出るたびに、勝った側に議席が移ります。国などの公式な判断は15議席、たくさんの研究のまとめは10議席、数万人以上の調査は6議席、条件が限られた結果は3議席です。",
     ["公式な判断", "まとめ", "数万人", "条件が限られた"]),
    ("chapter_start", "それでは、行ってみましょう！第1話。物語は、1965年の日本から始まります。", "第1話", "万歩計の誕生"),

    # 第1話 万歩計の誕生
    ("story", 1, "はじまり", "1965年 日本の時計メーカーが、腰につける歩数計「万歩計」を発売",
     [E(lambda d: year_tag(d, 420, 360, "1965年")), E(lambda d: pedometer(d, 560, 600, 330)),
      E(lambda d: arrow(d, 800, 890, 600)), E(lambda d: walker(d, 1080, 440, 300, fill=(255, 226, 196))),
      E(lambda d: words(d, 1470, 600, "一日1万歩", 96, GOOD))],
     "1965年、東京オリンピックの翌年。日本の時計メーカー、山佐時計計器が、腰につける歩数計を発売します。その名も「万歩計」。合言葉は「一日1万歩、歩こう」でした。"),
    ("story", 1, "なぜ1万？", "覚えやすく、キリのいい数字。「万」の字は、歩く人の姿にも見える",
     [E(lambda d: man_char(d, 500, 590, 360)), E(lambda d: arrow(d, 760, 850, 600)),
      E(lambda d: walker(d, 1040, 440, 300)),
      E(lambda d: words(d, 1470, 540, "根拠は", 64)), E(lambda d: words(d, 1470, 670, "研究ではない", 84, BAD))],
     "では、なぜ1万なのか。覚えやすくて、キリがいい。漢字の「万」は、歩く人の姿にも見える、とも言われます。つまり、1万という数字は、研究で決まったものではなかったんです。"),
    ("card", 1, "それでも、この合言葉は、日本中に広まりました。必要派がまず3議席。"),
    ("card", 2, "やがて1万歩は、世界へ。2004年、アメリカとカナダの研究者が、歩数の目安をまとめます。5,000歩未満は、座りがちな生活。1万歩以上なら、活動的な生活。1万歩は、健康な大人の目安として、ちょうどいい、と。"),
    ("card", 3, "2007年には、26の研究をまとめた分析が出ます。歩数計をつけると、歩数が一日約2,500歩増え、血圧も下がった。特に、1万歩などの目標を決めた人ほど、よく歩いていました。"),
    ("seats", 3, "必要派が73議席、不要派が27議席。一日1万歩は、世界の健康の合言葉になりました。"),

    # 第2話 中之条町の挑戦
    ("story", 2, "なぜ調べた？", "お年寄りに毎日1万歩はきつい。本当に必要なのは、どんな歩き方？",
     [E(lambda d: sw.person(d, 520, 370, 310)), E(lambda d: words(d, 520, 735, "毎日1万歩はきつい", 50, BAD)),
      E(lambda d: magnifier(d, 900, 580, 110)),
      E(lambda d: words(d, 1420, 520, "本当に必要な", 64)), E(lambda d: words(d, 1420, 650, "歩き方は？", 100))],
     "ところが日本で、ある疑問を持った研究者がいました。東京都健康長寿医療センターの、青柳幸利さんです。お年寄りに、毎日1万歩はきつい。本当に必要なのは、どんな歩き方なのか。"),
    ("story", 2, "どうやって？", "群馬県中之条町。65歳以上の住民 約5,000人に、24時間つける計測器",
     [E(lambda d: town(d, 470, 590, 440)), E(lambda d: pedometer(d, 860, 600, 200, num="")),
      E(lambda d: words(d, 1400, 520, "約5,000人", 96)), E(lambda d: words(d, 1400, 650, "2000年から 24時間", 56))],
     "舞台は、群馬県の中之条町。2000年から、65歳以上の住民、約5,000人に、歩数と歩く速さを測る小さな計測器を、24時間つけてもらいました。"),
    ("story", 2, "結果", "一日8,000歩、そのうち20分は少し速歩き。それで病気の予防には十分",
     [E(lambda d: walker(d, 470, 430, 320, fill=(214, 228, 250))), E(lambda d: arrow(d, 720, 810, 600)),
      E(lambda d: words(d, 1300, 500, "8,000歩", 130, BAD)), E(lambda d: words(d, 1300, 660, "うち20分は速歩き", 64))],
     "見えてきた答えは、一日8,000歩。そのうち20分は、会話ができるくらいの速歩き。これで、高血圧や糖尿病などの予防には、十分だというんです。"),
    ("card", 4, "1万歩でなくてもいい。不要派が6議席を取ります。"),

    # 第3話 1万歩の出どころ
    ("story", 3, "なぜ調べた？", "2019年 ハーバード大学のリー教授が1万歩の根拠を探すと、行き着いたのは万歩計の宣伝",
     [E(lambda d: year_tag(d, 420, 360, "2019年")), E(lambda d: magnifier(d, 470, 600, 130)),
      E(lambda d: arrow(d, 680, 770, 600)), E(lambda d: pedometer(d, 960, 600, 280)),
      E(lambda d: words(d, 1450, 540, "根拠は", 64)), E(lambda d: words(d, 1450, 670, "宣伝だった", 96, BAD))],
     "2019年、アメリカ、ハーバード大学のリー教授は、1万歩の根拠を探しました。たどり着いたのは、研究ではなく、日本の万歩計の宣伝。そこで、自分たちで確かめることにしたんです。"),
    ("story", 3, "どうやって？", "平均72歳の女性 約1万7千人。1週間、計測器をつけてもらい、4年あまり追いかけた",
     [E(lambda d: cw.crowd(d, 280, 430, 5, 2, 120, fill=(250, 214, 226))),
      E(lambda d: words(d, 1330, 520, "約1万7千人", 96)), E(lambda d: words(d, 1330, 650, "平均72歳の女性", 60))],
     "対象は、平均72歳の女性、約1万7千人。1週間、歩数を測る計測器をつけてもらい、その後、4年あまり追いかけました。"),
    ("story", 3, "結果", "約4,400歩でも死亡リスク41%減。7,500歩あたりで頭打ち",
     [E(lambda d: curve(d, 300, 380, 600, 350, "plateau", BAD)), E(lambda d: words(d, 600, 775, "歩数 →", 40, SUB)),
      E(lambda d: words(d, 1400, 500, "約4,400歩で -41%", 72, BAD)), E(lambda d: words(d, 1400, 640, "7,500歩で頭打ち", 72, BAD))],
     "結果、一日約4,400歩の人でも、約2,700歩の人より、死亡リスクが41%低い。そして、7,500歩あたりで、効果は頭打ちになりました。1万歩まで歩かなくても、よかったんです。"),
    ("card", 5, "不要派が6議席を取ります。"),
    ("card", 6, "しかし、必要派も黙っていません。2020年、アメリカの4,840人の調査では、一日8,000歩の人は、4,000歩の人より、死亡リスクが51%低く、1万2千歩なら65%低い。歩けば歩くほどいい、という結果です。必要派が3議席。"),
    ("card", 7, "2022年の3月には、15の調査、約4万7千人をまとめた分析が出ます。60歳以上では、6,000歩から8,000歩で、効果が頭打ち。60歳未満でも、8,000歩から1万歩でした。不要派が10議席を取ります。"),
    ("card", 8, "ところが同じ年の9月、デンマークなどの研究チームが、イギリスの約7万8千人を調べ、1万歩近く歩く人は、認知症になるリスクが51%低い、と発表。必要派が、6議席を取り戻しました。"),
    ("card", 9, "2023年には、京都大学などのチームが、別の見方を示します。8,000歩以上歩く日が、週に1日か2日あるだけで、10年間で亡くなる割合が、15ポイントほど低かったんです。毎日でなくてもいい。不要派が3議席。"),

    # 第4話 多いほどいい？ ちょうどいい？
    ("story", 4, "どうやって？", "2023年 ポーランドの研究チーム。17の研究・約23万人で、歩数の上限を調べた",
     [E(lambda d: year_tag(d, 420, 360, "2023年")), E(lambda d: flag_pl(d, 420, 560, 220)),
      E(lambda d: cw.papers(d, 640, 450, 260, 5)),
      E(lambda d: words(d, 1400, 520, "歩くほどいい？", 80)), E(lambda d: words(d, 1400, 650, "どこかで頭打ち？", 80, BAD))],
     "では、歩けば歩くほど、体にいいのか。それとも、どこかで頭打ちになるのか。2023年、ポーランドの研究チームが、17の研究、約23万人のデータをまとめて調べました。"),
    ("story", 4, "結果", "1,000歩増えるごとに死亡リスク15%減。2万歩まで上限は見つからなかった",
     [E(lambda d: curve(d, 300, 380, 600, 350, "rise", GOOD)), E(lambda d: words(d, 600, 775, "歩数 →", 40, SUB)),
      E(lambda d: words(d, 1400, 500, "2万歩まで", 80)), E(lambda d: words(d, 1400, 650, "上限なし", 120, GOOD))],
     "結果、1,000歩増えるごとに、死亡リスクは15%下がり、2万歩まで調べても、上限は見つかりませんでした。"),
    ("card", 10, "必要派が10議席を取り戻し、67議席になりました。"),
    ("story", 4, "ちょうどいい", "オランダの研究チーム。12の研究・約11万人で「効果がいちばん大きくなる歩数」を計算",
     [E(lambda d: flag_nl(d, 420, 560, 220)), E(lambda d: cw.papers(d, 640, 450, 260, 5)),
      E(lambda d: words(d, 1400, 520, "いちばん効果が", 70)), E(lambda d: words(d, 1400, 650, "大きい歩数は？", 80, BAD))],
     "その2か月後、オランダの研究チームが、別の答えを出します。12の研究、約11万人をまとめ、効果がいちばん大きくなる歩数を、計算したんです。"),
    ("story", 4, "結果", "死亡は約8,700歩、心臓・血管の病気は約7,100歩でほぼ最大。それ以上はほとんど変わらない",
     [E(lambda d: curve(d, 300, 380, 600, 350, "plateau", BAD)), E(lambda d: words(d, 600, 775, "歩数 →", 40, SUB)),
      E(lambda d: words(d, 1400, 500, "死亡 約8,700歩", 72, BAD)), E(lambda d: words(d, 1400, 640, "心臓 約7,100歩", 72, BAD))],
     "答えは、死亡については約8,700歩、心臓や血管の病気については約7,100歩。それより多く歩いても、効果はほとんど増えませんでした。"),
    ("card", 11, "不要派が10議席を取ります。"),
    ("card", 12, "そして2024年1月、日本の厚生労働省が、新しい運動のガイドを出します。目安は、大人が一日8,000歩以上、高齢者は6,000歩以上。国の目安も、1万歩ではありませんでした。"),
    ("seats", 12, "必要派が42議席、不要派が58議席。ついに、逆転です。"),
    ("card", 13, "2025年には、オーストラリアの研究チームが、57の研究をまとめます。一日7,000歩の人は、2,000歩の人より、死亡リスクが47%低い。1万歩なら、さらに少し得をする病気もありましたが、効果の大部分は、7,000歩までで得られていました。差し引きで、不要派が7議席を取ります。"),

    ("final", "最終結果は、必要派が35議席。一時は73議席あった必要派が、大きく議席を減らしました。ただ、当選確実はまだ出せません。ほとんどが観察研究で、もともと元気な人ほど、よく歩いているだけ、という可能性も残るからです。"),
    ("summary", "今日のまとめです。1万歩は、研究ではなく、万歩計の宣伝から生まれた数字でした。目安は、一日7,000歩から8,000歩。高齢の方は、6,000歩ほどでも十分です。少し速歩きを混ぜると、なおいいでしょう。もちろん、1万歩歩ける人は、歩いてもかまいません。持病のある方や、ひざが痛む方は、お医者さんに相談してくださいね。60年続いた、1万歩の呪縛。数字に追われず、自分のペースで歩きましょう。",
     ["万歩計の宣伝", "7,000歩から", "速歩き", "持病"]),
    ("next", "次回のテーマは「サウナは長生きのもと？」。フィンランドの男性を、20年追いかけた研究から始まります。"),
    ("outro", "新常識クロニクルでは、これからも、健康や暮らしの、いい派と悪い派の論争を、どんどん分析していきます。次に取り上げてほしい論争があれば、ぜひコメントで教えてください。チャンネル登録と高評価も、よろしくお願いします！"),
]


# ---------- 1万歩の回だけの画面 ----------
def hook_maker(narr):
    """万歩計がポンと出て「一日1万歩」→ 歩く人 →「実は研究から生まれた数字ではなかった」のハンコ。"""
    def make(alen, lead):
        at = lambda k: lead + narr.index(k) / len(narr) * alen  # noqa: E731
        t1, t2, t3 = max(lead, at("一日1万歩") - 0.1), at("スマホ"), at("研究から")

        def frame(t):
            im, d = stage()
            lay = blank()
            dd = ImageDraw.Draw(lay)
            k1 = seg(t, t1, t1 + 0.4)
            if k1 > 0:
                pedometer(dd, 760, 560, 380 * (0.6 + 0.4 * out_back(k1)))
            k2 = seg(t, t2, t2 + 0.4)
            if k2 > 0:
                walker(dd, 1200, 380, 330 * (0.6 + 0.4 * out_back(k2)), fill=(255, 226, 196))
            im = im.convert("RGBA")
            im.alpha_composite(lay)
            d = ImageDraw.Draw(im)
            if k1 > 0:
                chip(d, W / 2, 190, "一日1万歩、歩きましょう", GOOD, int(64 * (0.6 + 0.4 * out_back(k1))))
            k3 = seg(t, t3, t3 + 0.45)
            if k3 > 0:
                sc = 1.5 - 0.5 * out_back(k3)
                cx, cy = W / 2, 900
                bw, bh = 640 * sc, 80 * sc
                d.rounded_rectangle([cx - bw, cy - bh, cx + bw, cy + bh], radius=24 * sc, fill=BAD, outline=WHITE,
                                    width=max(3, int(8 * sc)))
                text(d, (cx, cy), "実は、研究から生まれた数字ではない", int(64 * sc), WHITE, anchor="mm")
            return im.convert("RGB")
        return frame, t3 + 0.8
    return WithAudio(make)


def rules_frame_maker(narr, keys):
    rows = [("国などの公式な判断", "15議席"), ("たくさんの研究のまとめ", "10議席"),
            ("数万人以上の追跡調査", "6議席"), ("条件が限られた結果", "3議席")]

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
    for x, lab, c in ((W / 2 - 420, "必要派:一日1万歩は必要", GOOD), (W / 2 + 420, "不要派:そんなにいらない", BAD)):
        k = seg(t, 0.8, 1.2)
        if k > 0:
            chip(d, x, 300, lab, c, int(46 * (0.6 + 0.4 * out_back(k))))
    return im


def summary_maker(narr, keys):
    items = [("1万歩は", "万歩計の宣伝から生まれた数字", BAD), ("目安は", "一日7,000〜8,000歩", BAD),
             ("少し", "速歩きを混ぜると、なおいい", GOOD), ("持病・ひざの痛みがある人は", "お医者さんに相談", INK)]

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


TOPICS = ["サウナは長生きのもと？", "朝ごはんは食べるべき？", "塩は減らすほどいい？", "牛乳は体にいい？", "日光浴は体にいい？",
          "1日2リットルの水は必要？"]


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
                f"{motion.LABELS[0] if diff > 0 else motion.LABELS[1]} +{abs(diff)}議席", source)


def build_plan():
    """(描く関数, 動く秒数, 合計秒数, 台本の行) のリスト。"""
    plan, last_chapter = [], None
    for sc in SCENES:
        kind, narr = sc[0], sc[-1] if sc[0] not in ("rules", "summary", "chapter_start") else sc[1]
        if kind == "hook":
            plan.append((hook_maker(narr), 0, dur(narr), ("つかみ", "一日1万歩、歩きましょう → 実は研究から生まれた数字ではない", narr)))
        elif kind == "title":
            img = os.path.join(OUT, "00_title.png")
            series_card(*EPISODES[EPISODE]).save(img)
            from PIL import Image
            plan.append(((lambda im: lambda t: im)(Image.open(img)), 0, dur(narr), ("タイトル", "新常識クロニクル:一日1万歩の呪縛", narr)))
        elif kind == "rules_intro":
            plan.append((rules_intro_frame, 1.3, dur(narr), ("ルール説明", "100議席・必要派 vs 不要派・50対50", narr)))
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
    lines = ["# 台本(物語版):一日1万歩の呪縛 〜「必要派」vs「不要派」論争の行方〜", "",
             "作成：2026-11-24 / 状態：初稿。`scripts/steps_story.py` の SCENES から自動で作っています(台本を直すときは SCENES を直す)。", "",
             f"ナレーション合計：約{sum(len(p[3][2]) for p in plan):,}字。場面の長さは合成したナレーションの長さで決まる。", "",
             "必要派(オレンジ)=「一日1万歩は必要(多いほどいい)」、不要派(青)=「そんなに歩かなくていい(7,000〜8,000歩で十分)」。", "",
             "読み方(2026-11-24 指示):一日=イチニチ、1万歩=イチマンポ、年号の年=ネン、8=ハチ、数字のあとの人=ニン。台本の文字は変えず、声に送る文章だけ `voice_text()` で直す(年号=カタカナ+読点、歩数=カタカナ、人数=漢数字+にん、ジュウ・ヒャクのあとの8は短い間+ハチ)。", "",
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
    lines += ["", "1965年の万歩計は研究ではないが、1万歩が広まった出発点として「条件が限られた結果」と同じ3議席にしている。",
              "1つの発表に両方の結果がある場合は差し引き(2025年 Ding らは 不要派+10 から「1万歩でさらに少し得」の 必要派+3 を引いて 不要派+7)。",
              "2022年9月の del Pozo Cruz らは、デンマーク(南デンマーク大学)などのチームがイギリスのデータ(UK Biobank)を使った研究。2023年3月の Inoue らは、京都大学などのチームがアメリカのデータ(NHANES)を使った研究。", "",
              "## 公開前に原文で確認すること",
              "- **1965年 万歩計**:山佐時計計器の「万歩計」発売年は資料で1964年・1965年とまちまち。社史・公式サイトで確認する。「万の字が歩く人に見える」は俗説として「とも言われます」とぼかした",
              "- 2004年 Tudor-Locke & Bassett(Sports Med 2004;34:1-8):5,000歩未満=座りがち、1万歩は健康な大人の目安として妥当、高齢者・持病のある人には多すぎる可能性(要旨で確認)。「活動的=1万歩以上」の区分は本文で確認",
              "- 2007年 Bravata ら(JAMA 2007;298:2296-304):26研究・2,767人、ランダム化試験で +2,491歩/日、収縮期血圧 −3.8mmHg、1万歩などの目標が増加の予測因子(確認済み)",
              "- **2010年 中之条研究**(Aoyagi & Shephard, Geriatr Gerontol Int 2010 ほか):65歳以上 約5,000人・2000年〜、「8,000歩・うち中強度20分」。論文の書誌と「8,000歩・20分」がどの論文の結論かを原文で確認する。青柳幸利さんの所属(東京都健康長寿医療センター研究所)も確認",
              "- 2019年 Lee ら(JAMA Intern Med 2019;179:1105-12):16,741人・平均72歳・平均4.3年、約4,400歩で約2,700歩より死亡が低い、約7,500歩で頭打ち(確認済み)。**HR 0.59(=−41%)は本文で確認**。万歩計の宣伝が由来という記述も本文で確認",
              "- **2020年 Saint-Maurice ら(JAMA 2020;323:1151-60)**:4,840人・40歳以上、8,000歩は4,000歩より死亡 HR 0.49(−51%)、1万2千歩は HR 0.35(−65%)。原文で確認",
              "- 2022年3月 Paluch ら(Lancet Public Health 2022;7:e219-28):15コホート・47,471人、60歳以上は6,000〜8,000歩、60歳未満は8,000〜10,000歩で頭打ち(確認済み)",
              "- 2022年9月 del Pozo Cruz ら(JAMA Neurology 2022):78,430人、約9,800歩で認知症 −51%(HR 0.49)、3,800歩で −25%(確認済み)",
              "- 2023年3月 Inoue ら(JAMA Netw Open 2023;6:e235174):3,101人、8,000歩以上の日が週1〜2日で10年死亡の調整リスク差 −14.9ポイント(確認済み。台本は「15ポイントほど」)",
              "- 2023年8月 Banach ら(Eur J Prev Cardiol 2023):17研究・226,889人、1,000歩ごとに死亡 −15%、2万歩まで上限なし(確認済み)",
              "- 2023年10月 Stens ら(JACC 2023;82:1483-94):12研究・111,309人、死亡は8,763歩、心血管病は7,126歩で最大(確認済み。台本は「約8,700歩」「約7,100歩」)",
              "- **2024年1月 厚生労働省「健康づくりのための身体活動・運動ガイド2023」**:成人は1日約8,000歩以上(歩行60分以上に相当)、高齢者は約6,000歩以上(40分以上)。高齢者の数字を推奨シートで確認する",
              "- 2025年 Ding ら(Lancet Public Health 2025;10:e668-81):57研究、7,000歩は2,000歩より死亡 −47%(HR 0.53)(確認済み)。「1万歩でさらに少し得をする病気」は本文の図で確認",
              "- 次回予告のサウナ(Laukkanen ら, JAMA Intern Med 2015、フィンランドの男性 約2,300人・約20年)は次回作るときに確認", ""]
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
    narr = voice_text(narr)
    t = re.sub(r"<#[\d.]+#>", "", narrate.mm_text(narr))
    for entry in narrate.mm_tone(narr)[len(narrate.MM_DICT):]:
        k, v = entry.split("/", 1)
        t = t.replace(k, v)
    return len(t)


def voiced_sec(narr, v):
    """声の長さから、わざと入れた間(<#秒#>。実際は指定の約2.5倍あく)を引いた秒数。"""
    from narrate import RATE
    pauses = sum(float(x) for x in re.findall(r"<#([\d.]+)#>", narrate.mm_text(voice_text(narr))))
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
    if "--voice" in sys.argv:   # 声と台本だけ(映像は作らない)。動画と同じ間隔でつないだ音声も書き出す
        parts = []
        for v, (_, _, sec, _) in zip(voices, plan):
            a = np.zeros(int(round(sec * RATE)), dtype="float32")
            vv = v[: max(0, len(a) - int(LEAD * RATE))]
            a[int(LEAD * RATE): int(LEAD * RATE) + len(vv)] = vv
            parts.append(a)
        wav = os.path.join(OUT, "narration.wav")
        sf.write(wav, np.concatenate(parts), RATE)
        mp3 = os.path.join(OUT, "steps_narration.mp3")
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
    out = os.path.join(OUT, "steps_story_draft.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", wav, "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-ar", "48000", "-c:a", "aac", "-b:a", "160k", "-shortest", out], check=True)
    shutil.rmtree(seg_dir)
    print("done:", out)


if __name__ == "__main__":
    sys.exit(main())
