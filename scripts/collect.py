"""
情報収集スクリプト
- Zenn RSS（AI・機械学習・自動化タグ）
- HackerNews RSS（100pt以上）
- GitHub Trending（今日のトレンド）
① 前日の👍リアクション記事をスプシ「お気に入り」に追記
② 今日の記事を1件1メッセージで投稿
"""

import os
import json
import time
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
import gspread
from google.oauth2.service_account import Credentials

# ── 設定 ──────────────────────────────────────────
SLACK_WEBHOOK_URL           = os.environ["SLACK_WEBHOOK_URL_PERSONAL"]
SLACK_BOT_TOKEN             = os.environ["SLACK_BOT_TOKEN"]
SLACK_CHANNEL               = os.environ["SLACK_CHANNEL"]
SPREADSHEET_ID              = os.environ["SPREADSHEET_ID"]
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]

MAX_ITEMS_PER_SOURCE = 5

RSS_FEEDS = [
    {"name": "Zenn AI",     "url": "https://zenn.dev/topics/ai/feed",             "emoji": "🤖"},
    {"name": "Zenn ML",     "url": "https://zenn.dev/topics/machinelearning/feed", "emoji": "🧠"},
    {"name": "Zenn 自動化", "url": "https://zenn.dev/topics/automation/feed",     "emoji": "⚙️"},
    {"name": "HackerNews",  "url": "https://hnrss.org/frontpage?points=100",      "emoji": "🔥"},
]

SLACK_HEADERS = {
    "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
    "Content-Type": "application/json",
}


# ── RSS収集 ───────────────────────────────────────
def fetch_rss(feed_info):
    parsed = feedparser.parse(feed_info["url"])
    items = []
    for entry in parsed.entries[:MAX_ITEMS_PER_SOURCE]:
        items.append({
            "source":    feed_info["name"],
            "emoji":     feed_info["emoji"],
            "title":     entry.get("title", ""),
            "url":       entry.get("link", ""),
            "published": entry.get("published", ""),
        })
    return items


# ── GitHub Trendingスクレイピング ─────────────────
def fetch_github_trending():
    url     = "https://github.com/trending?since=daily"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp    = requests.get(url, headers=headers, timeout=10)
    soup    = BeautifulSoup(resp.text, "html.parser")
    items = []
    for repo in soup.select("article.Box-row")[:MAX_ITEMS_PER_SOURCE]:
        h2 = repo.select_one("h2 a")
        if not h2:
            continue
        repo_path   = h2.get("href", "").strip("/")
        full_name   = repo_path.replace("/", " / ")
        desc_el     = repo.select_one("p")
        description = desc_el.get_text(strip=True) if desc_el else ""
        star_el     = repo.select_one("a[href$='/stargazers']")
        stars       = star_el.get_text(strip=True) if star_el else "?"
        items.append({
            "source":    "GitHub Trending",
            "emoji":     "⭐",
            "title":     f"{full_name}（★{stars}）— {description}",
            "url":       f"https://github.com/{repo_path}",
            "published": datetime.now(timezone.utc).isoformat(),
        })
    return items


# ── 1件1メッセージでSlack投稿 ─────────────────────
def post_to_slack(all_items):
    today = datetime.now().strftime("%Y/%m/%d")

    # ヘッダーメッセージ
    requests.post(
        SLACK_WEBHOOK_URL,
        json={"channel": SLACK_CHANNEL, "text": f"📰 *情報収集まとめ {today}*"},
        timeout=10,
    )
    time.sleep(0.5)

    current_source = None
    for item in all_items:
        # ソースが変わったらセクションヘッダー投稿
        if item["source"] != current_source:
            current_source = item["source"]
            requests.post(
                SLACK_WEBHOOK_URL,
                json={"channel": SLACK_CHANNEL, "text": f"{item['emoji']} *{item['source']}*"},
                timeout=10,
            )
            time.sleep(0.3)

        # 記事を1件ずつ投稿（Bot APIで投稿してts=メッセージIDを取得）
        resp = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers=SLACK_HEADERS,
            json={
                "channel": SLACK_CHANNEL,
                "text": f"• {item['title']}\n  → {item['url']}",
            },
            timeout=10,
        )
        time.sleep(0.3)

    print(f"Slack投稿完了: {len(all_items)}件")


# ── 前日の👍リアクション記事を取得 ───────────────
def fetch_liked_items():
    """前日にC0B55CF29C0チャンネルで👍リアクションがついたメッセージを取得"""
    yesterday_start = datetime.now(timezone.utc) - timedelta(hours=24)
    yesterday_end   = datetime.now(timezone.utc)

    resp = requests.get(
        "https://slack.com/api/conversations.history",
        headers=SLACK_HEADERS,
        params={
            "channel": SLACK_CHANNEL,
            "oldest":  str(yesterday_start.timestamp()),
            "latest":  str(yesterday_end.timestamp()),
            "limit":   200,
        },
        timeout=10,
    )
    data = resp.json()
    if not data.get("ok"):
        print(f"Slack履歴取得エラー: {data.get('error')}")
        return []

    liked = []
    for msg in data.get("messages", []):
        reactions = msg.get("reactions", [])
        thumbsup = [r for r in reactions if r["name"] in ("thumbsup", "+1")]
        if thumbsup:
            text = msg.get("text", "")
            # 「• タイトル\n  → URL」形式からURLを抽出
            lines = text.split("\n")
            title = lines[0].replace("• ", "").strip() if lines else text
            url   = lines[1].replace("  → ", "").strip() if len(lines) > 1 else ""
            liked.append({
                "title": title,
                "url":   url,
                "ts":    msg.get("ts", ""),
            })

    print(f"👍リアクション記事: {len(liked)}件")
    return liked


# ── お気に入りシートに追記 ────────────────────────
def save_liked_to_spreadsheet(liked_items, sh):
    if not liked_items:
        return
    ws  = sh.worksheet("お気に入り")
    now = datetime.now().strftime("%Y-%m-%d")
    # 既存URLを取得して重複チェック
    existing_urls = set(ws.col_values(3)[1:])  # C列（URL）のヘッダー除く
    rows = [
        [now, item["title"], item["url"], ""]
        for item in liked_items
        if item["url"] not in existing_urls
    ]
    if rows:
        ws.append_rows(rows)
    print(f"お気に入り追記: {len(rows)}件")


# ── Spreadsheet初期化（初回のみ） ─────────────────
def init_spreadsheet(sh):
    existing = [ws.title for ws in sh.worksheets()]
    if "収集ログ" not in existing:
        ws = sh.add_worksheet(title="収集ログ", rows=5000, cols=7)
        ws.append_row(["収集日時", "ソース", "タイトル", "URL", "公開日", "お気に入り", "メモ"])
        ws.format("A1:G1", {"textFormat": {"bold": True}})
    if "ダッシュ" not in existing:
        ws = sh.add_worksheet(title="ダッシュ", rows=30, cols=5)
        ws.update([["📊 情報収集ダッシュボード"]], "A1")
        ws.format("A1", {"textFormat": {"bold": True, "fontSize": 14}})
        ws.update([["ソース", "総件数"]], "A3")
        ws.format("A3:B3", {"textFormat": {"bold": True}})
        sources = ["Zenn AI", "Zenn ML", "Zenn 自動化", "HackerNews", "GitHub Trending"]
        rows = [[src, f"=COUNTIF(収集ログ!B:B,A{i})"] for i, src in enumerate(sources, start=4)]
        ws.update(rows, "A4")
        last = 3 + len(sources)
        ws.update([["合計", f"=SUM(B4:B{last})"]], f"A{last+1}")
        ws.format(f"A{last+1}:B{last+1}", {"textFormat": {"bold": True}})
        ws.update([["最終更新", ""]], "A11")
    if "お気に入り" not in existing:
        ws = sh.add_worksheet(title="お気に入り", rows=200, cols=4)
        ws.append_row(["追加日", "タイトル", "URL", "メモ"])
        ws.format("A1:D1", {"textFormat": {"bold": True}})


# ── Spreadsheet蓄積 ───────────────────────────────
def save_to_spreadsheet(all_items, sh):
    init_spreadsheet(sh)
    log_ws = sh.worksheet("収集ログ")
    now    = datetime.now().strftime("%Y-%m-%d %H:%M")
    # 既存URLを取得して重複チェック
    existing_urls = set(log_ws.col_values(4)[1:])  # D列（URL）のヘッダー除く
    rows = [
        [now, item["source"], item["title"], item["url"], item["published"], "", ""]
        for item in all_items
        if item["url"] not in existing_urls
    ]
    if rows:
        log_ws.append_rows(rows)
    dash_ws = sh.worksheet("ダッシュ")
    dash_ws.update([[now]], "B11")
    print(f"スプシ追記完了: {len(rows)}件")


# ── メイン ────────────────────────────────────────
def main():
    # Google認証（共通）
    creds = Credentials.from_service_account_info(
        json.loads(GOOGLE_SERVICE_ACCOUNT_JSON),
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)

    # ① 前日の👍記事をお気に入りに追記
    liked = fetch_liked_items()
    save_liked_to_spreadsheet(liked, sh)

    # ② 今日の記事を収集
    all_items = []
    for feed in RSS_FEEDS:
        try:
            items = fetch_rss(feed)
            all_items.extend(items)
            print(f"{feed['name']}: {len(items)}件")
        except Exception as e:
            print(f"{feed['name']} エラー: {e}")
    try:
        items = fetch_github_trending()
        all_items.extend(items)
        print(f"GitHub Trending: {len(items)}件")
    except Exception as e:
        print(f"GitHub Trending エラー: {e}")

    if not all_items:
        print("収集0件、終了")
        return

    # ③ Slack投稿（1件1メッセージ）
    post_to_slack(all_items)

    # ④ スプシ蓄積
    save_to_spreadsheet(all_items, sh)

    print(f"完了: 合計{len(all_items)}件")


if __name__ == "__main__":
    main()
