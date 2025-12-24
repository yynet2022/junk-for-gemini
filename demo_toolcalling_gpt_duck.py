import json
# pip install openai duckduckgo-search
from openai import OpenAI
from duckduckgo_search import DDGS # Google検索の代わりの無料検索ライブラリ

client = OpenAI()

# --- ツール: Web検索機能 ---
def web_search(query: str):
    """
    Web検索を行い、上位の結果を返します。
    """
    print(f"\n[System] 検索実行中: '{query}' ...")
    try:
        # DuckDuckGoで検索 (上位3件を取得)
        results = []
        with DDGS() as ddgs:
            # ddgs.text は内部で httpx を使って通信しています
            for r in ddgs.text(query, region='jp-jp', max_results=3):
                results.append({
                    "title": r['title'],
                    "body": r['body'],
                    "href": r['href']
                })
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

# --- ツール定義 ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "インターネット検索を行います。最新のニュース、株価、天気、あるいはAIが知らない知識が必要な場合に使用します。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "検索キーワード (例: '日経平均 昨日', '東京 天気')"
                    }
                },
                "required": ["query"],
            },
        },
    }
]

available_functions = {"web_search": web_search}

def main():
    messages = [
        {"role": "system", "content": "あなたはWeb検索を活用できる有能なアシスタントです。"}
    ]

    print("=== Search AI (type 'exit' to quit) ===")

    while True:
        user_input = input("\nUser: ").strip()
        if user_input.lower() == "exit": break
        if not user_input: continue

        messages.append({"role": "user", "content": user_input})

        # 1. AIへの問い合わせ
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        
        msg = response.choices[0].message
        tool_calls = msg.tool_calls

        if tool_calls:
            # AIが「検索したい」と言ってきた場合
            messages.append(msg) # 思考過程を履歴に追加

            for tool_call in tool_calls:
                fname = tool_call.function.name
                fargs = json.loads(tool_call.function.arguments)
                
                # 検索関数の実行
                if fname == "web_search":
                    tool_result = web_search(query=fargs["query"])
                    
                    # 結果を表示（デバッグ用）
                    # print(f"[System] 検索結果: {tool_result[:100]}...") 

                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": fname,
                        "content": tool_result
                    })

            # 2. 検索結果を含めて再度AIに回答させる
            response2 = client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            ai_content = response2.choices[0].message.content
            print(f"AI: {ai_content}")
            messages.append({"role": "assistant", "content": ai_content})
        
        else:
            # 検索不要な場合
            print(f"AI: {msg.content}")
            messages.append({"role": "assistant", "content": msg.content})

if __name__ == "__main__":
    main()
