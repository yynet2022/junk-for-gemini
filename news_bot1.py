#
import tomllib
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import json


# --- ステップ1: 前回作成した検索関数を定義 ---
def get_google_news_articles(query: str) -> str:
    """
    最新のニュースを Google 検索で検索し、記事のタイトル、URL、スニペットのリストをJSON形式で返す関数。

    ex) get_google_news_articles(query='経済')

    これがAI Studioの「ツール」として呼び出される。
    """
    print(f"--- ツール実行: get_google_news_articles(query='{query}') ---")

    # url = f"https://www.google.com/search?q={query}&tbm=nws&tbs=qdr:d"
    url = f"https://www.google.com/search?q={query}" \
        "+-site:youtube.com+-site:nicovideo.jp+-site:dailymotion.com" \
        "&tbm=nws&tbs=qdr:d"

    headers = {
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    # soup = BeautifulSoup(response.text, 'html.parser')
    soup = BeautifulSoup(response.text, 'lxml')
    news_items = soup.find_all('div', class_='SoaBEf')

    articles = []
    # for item in news_items[:3]:  # 3件絞り
    for item in news_items:
        link_tag = item.find('a')
        if link_tag:
            url = link_tag['href']
            if link_tag.find('div', role='heading'):
                title = link_tag.find('div', role='heading').text
            else:
                title = "タイトルなし"

        snippet_tag = item.find('div', class_='GI74Re')
        if snippet_tag:
            snippet = snippet_tag.text

        if link_tag and snippet_tag:
            articles.append({
                "title": title,
                "url": url,
                "snippet": snippet
            })

    print(f"--- 検索結果 {len(news_items)}件 (JSON) ---")
    print(json.dumps(articles, ensure_ascii=False, indent=2))
    return json.dumps(articles, ensure_ascii=False)


# --- メインの処理 ---
with open(".secrets.toml", "rb") as s:
    secrets = tomllib.load(s)

API_KEY = secrets["API_KEY"]
genai.configure(api_key=API_KEY)


# --- ステップ2: モデルを定義する際に「ツール」を登録 ---
system_prompt = 'あなたは優秀なニュースアナリストです。事実に基づいて、客観的に情報を要約してください。'
model = genai.GenerativeModel(
    'gemini-flash-latest',  # Function Callingに対応したモデルを選択
    system_instruction=system_prompt,
    tools=[get_google_news_articles]  # ここで自作関数をツールとして渡す
)

# チャットセッションを開始
chat = model.start_chat(enable_automatic_function_calling=True)

# --- ステップ3: ツールをトリガーするようなプロンプトを送信 ---
prompt = "経済に関する最新のニュースを検索して、重要なポイントを要約してください。"
print(f"あなた: {prompt}")

# メッセージを送信
response = chat.send_message(prompt)

# --- ステップ4: 応答からテキストだけを取り出して表示 ---
# enable_automatic_function_calling=True のおかげで、
# SDKが裏側でツール実行と結果送信を自動でやってくれる
print("\nGeminiからの応答:")
print(response.text)
