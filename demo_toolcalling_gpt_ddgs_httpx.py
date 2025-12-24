import json
import httpx
from openai import OpenAI
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
#ex 「昨日の日経平均の終値と、主な値動きの要因を詳しく教えて」

client = OpenAI()

# --- ツール1: Web検索 ---
def web_search(query: str):
    """Web検索を行い、URLとタイトルのリストを返します。"""
    print(f"\n[System] Search Query: '{query}'")
    try:
        results = []
        with DDGS() as ddgs:
            # max_results=3 で上位3件に絞る
            for r in ddgs.text(query, region='jp-jp', max_results=3):
                results.append({"title": r['title'], "url": r['href'], "snippet": r['body']})
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

# --- ツール2: Webページ訪問 (スクレイピング) ---
def visit_web_page(url: str):
    """指定されたURLにアクセスし、ページのテキスト本文を取得します。"""
    print(f"\n[System] Visiting: {url}")
    try:
        # 最近のWebサイトはUser-Agentがないと拒否されることが多いので偽装します
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        with httpx.Client(timeout=10.0, follow_redirects=True, headers=headers) as client:
            resp = client.get(url)
            resp.raise_for_status()
            
            # HTMLからテキストを抽出
            soup = BeautifulSoup(resp.content, "html.parser")
            
            # scriptやstyleタグを除去
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text(separator="\n")
            
            # 空白行を削除して整形
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            clean_text = "\n".join(lines)
            
            # 長すぎるとトークン制限にかかるので、先頭5000文字程度に制限
            return clean_text[:5000]
            
    except Exception as e:
        return json.dumps({"error": f"Failed to read page: {str(e)}"})

# --- ツール定義 ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "検索エンジンで情報を探します。URLを知るために使います。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "検索キーワード"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "visit_web_page",
            "description": "特定のURLのWebページの中身（本文）を読み込みます。詳細な情報を得るために使います。",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "アクセスするURL"}
                },
                "required": ["url"],
            },
        },
    }
]

available_functions = {
    "web_search": web_search,
    "visit_web_page": visit_web_page,
}

def main():
    messages = [
        {"role": "system", "content": """
あなたはWebブラウジングができるAIアシスタントです。
以下の手順でユーザーの質問に答えてください。
1. まず `web_search` で関連情報を検索する。
2. 得られた検索結果のURLから、有望そうなものを `visit_web_page` で閲覧する（最大3つまで）。
3. ページの内容を元に、ユーザーの質問に対する包括的な回答を作成する。
"""}
    ]

    print("=== Browsing Agent (type 'exit' to quit) ===")

    while True:
        user_input = input("\nUser: ").strip()
        if user_input.lower() == "exit": break
        if not user_input: continue

        messages.append({"role": "user", "content": user_input})

        # --- AIの自律ループ (Agent Loop) ---
        # ユーザーに回答を返すまで、AIが納得するまでツールを使い続けるループ
        while True:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
            
            msg = response.choices[0].message
            tool_calls = msg.tool_calls

            # ツール呼び出しがある場合
            if tool_calls:
                messages.append(msg) # 思考履歴を追加
                
                for tool_call in tool_calls:
                    fname = tool_call.function.name
                    fargs = json.loads(tool_call.function.arguments)
                    
                    # 実行
                    func = available_functions.get(fname)
                    if func:
                        # 検索やページ訪問の実行
                        if fname == "visit_web_page":
                            result = func(url=fargs["url"])
                        else:
                            result = func(**fargs)
                        
                        # 結果を履歴に追加
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": fname,
                            "content": result
                        })
                
                # ループの先頭に戻り、ツールの結果を持った状態でもう一度AIに考えさせる
                # (まだ情報が足りなければさらにツールを呼ぶし、十分なら回答を生成する)
                continue
            
            else:
                # ツール呼び出しがなく、最終回答が生成された場合
                final_answer = msg.content
                print(f"\nAI: {final_answer}")
                messages.append({"role": "assistant", "content": final_answer})
                break # 自律ループを抜けてユーザー入力待ちへ

if __name__ == "__main__":
    main()
