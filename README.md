# info-collector

> Zenn・HackerNews・GitHub Trendingの記事を毎日自動収集し、Slack投稿とスプレッドシート蓄積を行う情報収集パイプライン

エンジニアが毎日行う「技術記事のチェック」を自動化。RSSフィード・スクレイピング・GitHub APIから記事を収集・フィルタリングしてSlackへ投稿。👍リアクションをつけた記事は翌日自動でお気に入りに保存されます。

## 機能

- **RSS収集**: Zenn（AI / 機械学習 / 自動化）、HackerNews（100pt以上）から最新記事を取得
- **GitHub Trending**: 当日のトレンドリポジトリをスクレイピングで取得
- **Slack投稿**: 1件1メッセージで投稿。👍リアクションをつけると翌日お気に入りに自動保存
- **スプレッドシート蓄積**: 収集ログ・ダッシュボード・お気に入りの3シートで管理

## 背景・導入経緯

技術的なインプットのために毎日 Zenn・HackerNews・GitHub Trending を手動でチェックしていたが、確認作業自体に時間がかかり、気になった記事も後から見返せずに埋もれることが多かった。

RSS とスクレイピングを組み合わせて自動収集・Slack 投稿することで、記事を能動的に探す作業をなくした。Slack の👍リアクションをお気に入りのフラグとして使うことで、「後で読む」リストを追加アプリなしにそのまま実現している。

## 技術スタック

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-2088FF?style=flat&logo=github-actions&logoColor=white)
![Slack](https://img.shields.io/badge/Slack-4A154B?style=flat&logo=slack&logoColor=white)
![Google Sheets](https://img.shields.io/badge/Google%20Sheets-34A853?style=flat&logo=google-sheets&logoColor=white)

- **Python 3.11+**
- **feedparser** — RSSフィード取得
- **Slack Bot API** — メッセージ投稿・リアクション監視
- **gspread** — スプレッドシート書き込み
- **GitHub Actions** — 毎日の自動実行

## パイプライン

```
Zenn RSS / HackerNews RSS / GitHub Trending（スクレイピング）
  ↓  重複除去・スコアフィルタ
collect.py
  ↓  1件1メッセージでSlack投稿
Slack（👍リアクション = お気に入りフラグ）
  ↓  翌日の実行時にリアクションを確認して自動保存
Google スプレッドシート（収集ログ / ダッシュボード / お気に入り）
```

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r scripts/requirements.txt
```

| 環境変数 | 説明 |
|---|---|
| `SLACK_WEBHOOK_URL_PERSONAL` | Incoming Webhook URL |
| `SLACK_BOT_TOKEN` | Bot Token（`xoxb-...`） |
| `SLACK_CHANNEL` | 投稿先チャンネルID |
| `SPREADSHEET_ID` | Google スプレッドシートID |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | サービスアカウントJSON（文字列） |

## 実行

```bash
python scripts/collect.py
```

## スプレッドシートの構成

初回実行時に3つのシートを自動生成します。

| シート | 内容 |
|---|---|
| 収集ログ | 収集日時・ソース・タイトル・URL・公開日・お気に入り・メモ。URLで重複を除外して追記 |
| ダッシュ | ソース別の件数を `COUNTIF` で集計（値ではなく数式を置くので、ログが増えれば自動で追従する） |
| お気に入り | 👍が付いた記事を翌日の実行時に転記 |

## GitHub Actions

ワークフローは `workflow_dispatch` のみで、`schedule` は置いていません。上記5つの環境変数をGitHub Secretsに登録してから **Actions → 情報収集 daily → Run workflow** で実行します。

定刻に動かしたい場合、GitHub Actionsの `schedule` は混雑時に数十分ずれるため、外部cronサービスからGitHub APIの `workflow_dispatch` を叩くほうが確実です（そのパターンは [github-actions-scheduler](https://github.com/reona777/github-actions-scheduler) にまとめてあります）。

## ファイル構成

```
info-collector/
├── scripts/
│   ├── collect.py          # 収集・Slack投稿・スプレッドシート蓄積
│   └── requirements.txt
└── .github/workflows/
    └── collect.yml         # 手動実行（workflow_dispatch）
```

## ライセンス

MIT
