#
import requests
from bs4 import BeautifulSoup
import json


def get_google_news_articles(query: str) -> str:
    """
    Google Newsを検索し、記事のタイトル、URL、スニペットのリストをJSON形式で返す関数。
    これがAI Studioの「ツール」として呼び出される。
    """

    # ユーザーが指摘した、ニュース検索用のURL
    url = f"https://www.google.com/search?q={query}&tbm=nws&tbs=qdr:d"

    # PCからのアクセスのふりをするためのヘッダー
    headers = {
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # 1. HTMLの取得
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # エラーがあればここで例外を発生させる

    # 2. HTMLの解析 (Beautiful Soupの出番)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 3. 主要な情報の抽出
    # Googleの検索結果のHTML構造は変更される可能性があるため、このセレクタは一例です。
    # ニュース記事の各項目を囲んでいるdivタグを探す。
    news_items = soup.find_all('div', class_='SoaBEf')

    articles = []
    for item in news_items:
        # aタグからURLとタイトルを抽出
        link_tag = item.find('a')
        if link_tag:
            url = link_tag['href']
            if link_tag.find('div', role='heading'):
                title = link_tag.find('div', role='heading').text
            else:
                title = "タイトルなし"

        # スニペット（短い要約）を抽出
        snippet_tag = item.find('div', class_='GI74Re')
        if snippet_tag:
            snippet = snippet_tag.text

        # 抽出した情報を辞書にまとめる
        if link_tag and snippet_tag:
            articles.append({
                "title": title,
                "url": url,
                "snippet": snippet
            })

    # 4. データの構造化 (PythonのリストをJSON文字列に変換)
    # この綺麗なJSON文字列を最終的にGeminiに返す
    return json.dumps(articles, ensure_ascii=False, indent=2)


# --- 関数の実行テスト ---
if __name__ == '__main__':
    economic_news_json = get_google_news_articles("経済")
    print(economic_news_json)
