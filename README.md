# info-collector

Zenn・HackerNews・GitHub Trending の記事を毎日収集し、Slack に投稿 + Google スプレッドシートに蓄積する自動化スクリプト。

## 機能

- **RSS収集**: Zenn（AI / 機械学習 / 自動化）・HackerNews（100pt以上）から最新記事を取得
- **GitHub Trending**: 当日のトレンドリポジトリをスクレイピング
- **Slack投稿**: 1件1メッセージで投稿。👍リアクションをつけると翌日お気に入りに自動保存
- **スプレッドシート蓄積**: 収集ログ・ダッシュボード・お気に入りの3シートで管理

## セットアップ

### 必要なもの

- Python 3.11+
- Slack ワークスペース（Bot Token + Incoming Webhook）
- Google サービスアカウント（Sheets / Drive 権限）
- Google スプレッドシート

### インストール

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r scripts/requirements.txt
```

### 環境変数

| 変数名 | 説明 |
|--------|------|
| `SLACK_WEBHOOK_URL_PERSONAL` | Incoming Webhook URL |
| `SLACK_BOT_TOKEN` | Bot Token（`xoxb-...`） |
| `SLACK_CHANNEL` | 投稿先チャンネル ID |
| `SPREADSHEET_ID` | Google スプレッドシートの ID |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | サービスアカウント JSON（文字列） |

### 実行

```bash
python scripts/collect.py
```

## GitHub Actions

`.github/workflows/collect.yml` に手動実行（`workflow_dispatch`）トリガーが設定済み。

上記5つの環境変数を GitHub Secrets に登録してから **Actions → Run workflow** で実行できる。
