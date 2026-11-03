# 自動更新サイト(楽天アフィリエイト)

Threads とは別に、**検索から人が来るサイト**を自動で作って育てるための仕組みです。
1つのリポジトリで、複数のサイトを管理できるようにしてあります(いまは①ふるさと納税だけ)。

| サイト | フォルダ | 状態 |
|---|---|---|
| ① ふるさと納税コスパ比較 | `sites/furusato/` | 作成済み |
| ③ 楽天セール「買い時」トラッカー | (予定) | ①の `history.csv` で価格の記録をためはじめています |
| ② 日用品の単価比較 | (予定) | ①の仕組みを使い回して作る予定です |

---

## ① ふるさと納税コスパ比較

楽天ふるさと納税の返礼品を、**寄付額1万円あたりに届く量**(お米なら何kg、トイレットペーパーなら何ロールか)で並べるサイトです。

### しくみ(毎日自動)
```
楽天API ──fetch.py──▶ data/snapshot.json ──build.py──▶ dist/furusato/(HTML) ──▶ Cloudflare Pages(公開)
                         └▶ data/history.csv(価格の記録。③で使う)
```
- **AIの文章は使っていません。** ページの中身は、楽天のデータを計算した結果です(量産された薄いページと判断されにくくするため)
- 商品名から量を**はっきり読み取れた返礼品だけ**を比べます。容量や回数を選べる返礼品は、寄付額と量の対応が分からないので、別の一覧にしています
- 比べられる返礼品が3件未満のジャンルは、自動でページを作りません(中身の薄いページを出さないため)
- 全ページに「広告(PR)」の表示を入れ、リンクには `rel="sponsored"` を付けています(ステマ規制対策)

### ファイル
| ファイル | 役割 |
|---|---|
| `config.json` | サイト名、運営者名、**ジャンル(検索キーワード・除外ワード)** |
| `overrides.json` | 人の目で確かめた量の修正や、載せたくない返礼品の指定 |
| `fetch.py` | 楽天APIから取得する(約2分) |
| `build.py` | HTMLを作る |
| `quantity.py` / `rank.py` | 量の読み取りと並べ替え |
| `style.css` | 見た目 |

### 手元で動かす
```bash
python3 sites/furusato/build.py --demo --out dist/demo
```
```bash
python3 sites/furusato/fetch.py
```
```bash
python3 sites/furusato/build.py
```
```bash
cd dist/furusato && python3 -m http.server 8000
```
最後のコマンドのあと、ブラウザで http://localhost:8000 を開くと確認できます。

---

## 公開までの準備(最初に1回だけ)

### 1. 運営者情報を書く
`sites/furusato/config.json` の `operator_name`(ニックネーム可)と `contact`(メールアドレスか、お問い合わせフォームのURL)を書き換えます。アフィリエイトサイトでは、運営者と連絡先の表示が必要です。

### 2. Cloudflare に登録して、Pages のプロジェクトを作る(無料)
1. https://dash.cloudflare.com/ でアカウントを作る
2. 「Workers & Pages」→「作成」→「Pages」→「アセットをアップロード」で、プロジェクト名(例: `furusato-cospa`)を決めて作る(中身は空のままで大丈夫です)
3. 公開URLは `https://プロジェクト名.pages.dev` になります
4. 「マイプロフィール」→「APIトークン」→「トークンを作成」→「Cloudflare Pages の編集」のテンプレートでトークンを作り、控えておく
5. アカウントID(ダッシュボードの右側か、URLに出ている英数字)を控えておく

> 独自ドメイン(例: `furusato-cospa.com`、年1,500円ほど)は、Cloudflare で買うのがいちばん簡単です。Pages の「カスタムドメイン」で設定します。**検索の評価はドメインにつくので、早めに決めるのがおすすめです。**

### 3. 楽天ウェブサービスに、公開URLを登録する
GitHub Actions(自動実行の仕組み)は、毎回ちがうIPアドレスから楽天APIを呼びます。そのため、IPアドレスではなく**サイトのURL**で許可します。
1. 楽天ウェブサービス → アプリ情報の確認 → アプリの編集
2. 「許可されたWebサイト」に、公開URL(例: `https://furusato-cospa.pages.dev`)を追加

### 4. GitHub に設定を入れる
リポジトリの **Settings → Secrets and variables → Actions** で登録します。

**Secrets(他人に見えない値)**
| 名前 | 値 |
|---|---|
| `RAKUTEN_APPLICATION_ID` | 楽天のアプリケーションID |
| `RAKUTEN_ACCESS_KEY` | 楽天のアクセスキー(pk_〜) |
| `RAKUTEN_AFFILIATE_ID` | 楽天のアフィリエイトID |
| `RAKUTEN_REFERER` | 手順3で登録したURL |
| `CLOUDFLARE_API_TOKEN` | 手順2で作ったトークン |
| `CLOUDFLARE_ACCOUNT_ID` | CloudflareのアカウントID |

**Variables(見えてもよい値)**
| 名前 | 値 |
|---|---|
| `FURUSATO_BASE_URL` | 公開URL(例: `https://furusato-cospa.pages.dev`) |
| `CF_PAGES_PROJECT` | Pagesのプロジェクト名(例: `furusato-cospa`) |

### 5. 自動実行を始める
毎日の自動実行は、**このブランチを `main` に取り込んだ後**に動きます(GitHub の決まりで、定時実行は既定のブランチでしか動きません)。
取り込んだら、**Actions → furusato-site → Run workflow** で1回手で動かし、緑のチェックが付けば公開完了です。以降は毎日5時ごろ(日本時間)に自動で更新されます。

> うまくいかないときは、Actions の赤いバツをクリックしてエラーを Claude に見せてください。
> `403 CLIENT_IP_NOT_ALLOWED` が出る場合は、手順3の登録URLと `RAKUTEN_REFERER` が完全に同じか(末尾の `/` も含めて)確認してください。

### 6. Google に知らせる
公開したら、[Google Search Console](https://search.google.com/search-console) にサイトを登録し、`公開URL/sitemap.xml` を送信します。検索に出始めるまで、数日〜数週間かかります。

---

## 週に1回やること(15分)
自動化しても、**人の目のチェックがあるサイトのほうが長く評価されます**。
1. 各ジャンルの上位5件を開き、**量と寄付額が商品ページと合っているか**を確かめる
2. ずれていたら `overrides.json` に書く(例は中にあります)
   - 量の読み間違い → `"amount": 10000`(gで書く。10kgなら10000)
   - 比べるのがふさわしくない返礼品(セット品など) → `"exclude": true`
3. ジャンルに関係ない返礼品が混ざっていたら、`config.json` の `exclude` に言葉を足す
4. 変えたら保存(commit・push)。次の自動更新で反映されます

## ジャンルを増やすには
`config.json` の `categories` に1つ足すだけです。`family` は量の種類(`weight`=重さ、`volume`=液体、`roll`=ロール、`box`=箱)。
足したら `python3 sites/furusato/fetch.py --only 新しいslug` で試し、`build.py` で比較できる件数が3件以上あるか確認します。

## 注意
- 寄付額・在庫は毎日変わります。ページには取得日時を表示しています
- 「最安」「No.1」などの言葉は使っていません。順位は「1万円あたりの量」という一つの基準での並びです
- 控除の上限額の計算はしていません(人によって違い、間違えると迷惑をかけるため)。総務省のページへの案内だけにしています
