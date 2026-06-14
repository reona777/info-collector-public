# info-collector

> Zenn・HackerNews・GitHub Trendingの記事を毎日自動収集し、Slack投稿とスプレッドシート蓄積を行う情報収集パイプライン

エンジニアが毎日行う「技術記事のチェック」を自動化。RSSフィード・スクレイピング・GitHub APIから記事を収集・フィルタリングしてSlackへ投稿。👍リアクションをつけた記事は翌日自動でお気に入りに保存されます。

## 機能

- **RSS収集**: Zenn（AI / 機械学習 / 自動化）、HackerNews（100pt以上）から最新記事を取得
- **GitHub Trending**: 当日のトレンドリポジトリをスクレイピングで取得
- **Slack投稿**: 1件1メッセージで投稿。👍リアクションをつけると翌日お気に入りに自動保存
- **スプレッドシート蓄積**: 収集ログ・ダッシュボード・お気に入りの3シートで管理

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

GitHub Actionsで毎日自動実行する場合は、上記5つの環境変数をGitHub Secretsに登録してから **Actions → Run workflow** で実行してください。
