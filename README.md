# Threads × 楽天アフィリエイト 運用プロジェクト

Threads(スレッズ)の投稿と楽天アフィリエイトで、**月間売上(購入金額の合計)100万円**を目指すための、仕組みと資料のセットです。
**週2時間(毎週土曜)だけ**で回せるように作ってあります。

> ⚠️ **最初に知っておいてほしいこと**
> 目標は保証されたものではありません。フォロワー約70人・週2時間・3か月では、**100万円に届く可能性はとても低く**、12月の売上の現実的な見込みは **約1,000円〜10万円** です。
> 理由と、届くために必要な条件(期間・表示回数・作業時間)は [`docs/strategy.md`](docs/strategy.md) の「3. 逆算表」に正直に書きました。まずここを読んでください。

---

## 何ができるのか

| やりたいこと | 使うもの |
|---|---|
| 戦略(ジャンル・読者・逆算・3か月ロードマップ)を知る | [`docs/strategy.md`](docs/strategy.md) |
| 投稿の型・30日カレンダー・テンプレートを見る | [`docs/content-plan.md`](docs/content-plan.md) |
| 規約・広告表記(PR)・スパム対策を確認する | [`docs/compliance.md`](docs/compliance.md) |
| 毎週2時間で何をするか知る | [`docs/weekly-routine.md`](docs/weekly-routine.md) |
| 投稿文の下書きを作る(自動投稿はしません) | `scripts/generate_drafts.py` |
| 成果(クリック・売上)を記録・集計する | `tracking/` |
| 毎週の振り返りをする | [`tracking/review-guide.md`](tracking/review-guide.md) |

**投稿は、すべてあなたの手で行います。** ツールが作るのは「下書きファイル」だけです。内容を確認して、自分で Threads に投稿してください。

## フォルダの中身

```
my-project/
├── README.md              ← このファイル
├── .env.example           ← IDを入れる設定ファイルの雛形(.env にコピーして使う)
├── docs/                  ← 戦略・投稿設計・規約・週の手順
├── scripts/
│   ├── generate_drafts.py ← 1週間分の下書きを作る(これを実行します)
│   ├── calendar.csv       ← 投稿カレンダー(日付・型・検索キーワード)。書き換え可
│   ├── post_templates.py  ← 投稿文のテンプレート
│   ├── rakuten_client.py  ← 楽天APIを呼ぶ部品
│   └── sample_items.json  ← 練習用のダミー商品
├── tracking/
│   ├── posts.csv          ← 投稿の記録(スプレッドシートで開ける)
│   ├── sales_daily.csv    ← 楽天CSVから取り込んだ日別の成果
│   ├── imports/           ← 楽天アフィリエイトのCSVを置く場所
│   ├── import_report.py   ← CSVの取り込み
│   ├── summarize.py       ← 週次・月次の集計と進捗(100万円まであと何%か)
│   ├── config.json        ← 目標金額・通過点の設定
│   ├── column_map.json    ← CSVの見出し名の対応表
│   └── reports/           ← 週次レポートの保存先
├── output/                ← 作った下書きが入る(GitHubには上げません)
└── tests/                 ← 動作確認用のテスト
```

---

## はじめての準備(第1週の土曜に1回だけ)

### 1. Python を用意する
このツールは Python 3.9 以上で動きます(追加のインストールは不要)。
ターミナル(Mac は「ターミナル」、Windows は「PowerShell」)で次を入力して、バージョンが出れば準備できています。
```
python3 --version
```
出ないときは https://www.python.org/ から Python をインストールしてください(Windows では `python3` の代わりに `python` と入力します)。

### 2. このプロジェクトを手元に置く
GitHub のリポジトリ画面で「Code」→「Download ZIP」でも、`git clone` でもかまいません。ターミナルでそのフォルダ(`my-project`)に移動します。

### 3. 楽天のIDを用意する
次の3つが必要です(ご自身で取得済みの前提です)。

| 名前 | どこで確認するか |
|---|---|
| アプリケーションID | 楽天ウェブサービスのアプリ管理画面(https://webservice.rakuten.co.jp/) |
| アクセスキー(「pk_」で始まる) | 同上。**2026年2月の仕様変更で必要になりました** |
| アフィリエイトID | 楽天アフィリエイトの管理画面 |

### 4. IDを `.env` に書く(ここが大事)
```
cp .env.example .env
```
(Windows は `copy .env.example .env`)
メモ帳などで `.env` を開き、「ここに〜」の部分を自分のIDに置き換えて保存します。

> 🔒 **`.env` は GitHub に上がらない設定にしてあります。** IDやキーを、`.env.example` やプログラムの中、チャット、SNSには**絶対に**書かないでください。もし漏れたら、すぐに楽天側で再発行してください。

> もし 403 エラーが出たら: 楽天ウェブサービスのアプリ登録で「許可されたWebサイト」に入れたURLを、`.env` の `RAKUTEN_REFERER` に書いてください。楽天のAPIは2026年に仕様が変わったため、うまくいかないときは `RAKUTEN_API_ENDPOINT` を楽天の最新ドキュメントのURLに変更してください。

### 5. まず「練習モード」で動かす
IDなしでも動く練習モードがあります(ダミー商品を使います)。
```
python3 scripts/generate_drafts.py --demo --start 2026-10-02 --days 7
```
`output/drafts_2026-10-02_demo.md` ができれば成功です。開いて、投稿文の形を見てみましょう。

### 6. 本番(楽天APIを使う)
```
python3 scripts/generate_drafts.py --start 2026-10-02 --days 7
```
`output/drafts_2026-10-02.md` ができ、`tracking/posts.csv` に下書きの記録が追加されます。

> ⚠️ **私(Claude)は、あなたの本物のIDで実際の楽天APIを呼んではいません。**
> 動作確認は、ダミーのデータと、API応答を模したテストで行いました。**初回は、実際に動くことをあなたの環境で確認してください。**
> エラーが出たら、メッセージ(IDは自動で `***` に隠れます)をそのまま Claude に見せてください。API仕様の変更に合わせて直せます。

### 7. 動作テスト(任意)
```
python3 -m unittest discover -s tests
```
`OK` と出れば、プログラムは正しく動いています。

---

## 毎週の使い方(週2時間・土曜)

詳細は [`docs/weekly-routine.md`](docs/weekly-routine.md)。概要は次のとおりです。

1. **土曜10時にレポートが届く**(下記)→ 読む(10分)
2. **楽天アフィリエイト管理画面から成果のCSVをダウンロード** → `tracking/imports/` に置き、取り込む(15分)
   ```
   python3 tracking/import_report.py tracking/imports/2026-10-10.csv
   ```
3. **先週の投稿の記録を更新**(`tracking/posts.csv` の `status` を `posted`、`posted_date` に日付)(10分)
4. **振り返り**して、来週の型を調整(15分)→ [`tracking/review-guide.md`](tracking/review-guide.md)
5. **来週分の下書きを作る**(5分)
   ```
   python3 scripts/generate_drafts.py --start 次の投稿日 --days 7
   ```
6. **下書きを確認・修正**(40分)。`《 》` を自分の言葉に置き換える。
7. **Threads に投稿・予約**(25分)

### 集計を見る
```
python3 tracking/summarize.py
```
先週の売上、今月の進み具合、100万円に対する割合、型ごとの「増やす/やめる」判定が出ます(`tracking/reports/` にも保存)。

### スプレッドシートで見る
`tracking/posts.csv` と `tracking/sales_daily.csv` は、Excel や Google スプレッドシートでそのまま開けます。編集したら同じ名前の CSV で保存してください。Googleスプレッドシートを使う場合は「ファイル→インポート」で開き、編集後は「ファイル→ダウンロード→CSV」で上書きします。

---

## 毎週土曜10時のレポート

Claude が毎週土曜の朝10時(日本時間)に、`tracking/` のデータを集計して週次レポートを作る設定にしてあります(設定の状態はこのプロジェクトを作ったセッションの最後に報告します)。

**レポートを正確にするには、土曜の朝までに最新の楽天CSVを `tracking/imports/` に置き、取り込んでおく必要があります。** 間に合わなかった週は、前回までのデータでのレポートになります(Claude は楽天の管理画面にはログインできません)。

---

## 変更を保存する(GitHub)
記録(`posts.csv` など)を変えたら、保存しておくと、自動レポートでも使えます。
```
git add tracking
git commit -m "今週の記録を更新"
git push
```
(うまくいかないときは Claude に頼んでください。)

## よくあるつまずき

| 症状 | 対処 |
|---|---|
| `環境変数が足りません` | `.env` を作ったか、「ここに〜」を書き換えたか確認。練習なら `--demo` |
| `HTTP 403` | アクセスキー・許可Webサイト(`RAKUTEN_REFERER`)を確認 |
| `条件に合う商品が足りません` | `scripts/calendar.csv` のキーワードを短く、価格帯を広くする |
| `売上金額の列が見つかりません` | `--show-columns` で見出しを確認 → `tracking/column_map.json` に追加 |
| 文字が化ける(CSV) | Excel では「データ→テキストから」で UTF-8 を選ぶ。または Google スプレッドシートで開く |

## ルール(必ず読む)
広告表記(【PR】)・規約・スパム対策は [`docs/compliance.md`](docs/compliance.md) にまとめています。**すべての広告投稿の先頭に「【PR】」を入れてください。**
