import json
import httpx
from openai import OpenAI

# APIキー設定 (環境変数推奨)
client = OpenAI()

# --- ツール1: ビットコイン価格取得 (CoinDesk API) ---
def get_bitcoin_price(currency: str = "USD"):
    """現在のビットコイン価格を取得する"""
    url = "https://api.coindesk.com/v1/bpi/currentprice.json"
    try:
        with httpx.Client(timeout=10.0) as http:
            resp = http.get(url)
            resp.raise_for_status()
            data = resp.json()
            # 簡略化のためレートのみ抽出
            rate = data["bpi"]["USD"]["rate"]
            return json.dumps({"currency": "USD", "price": rate})
    except Exception as e:
        return json.dumps({"error": str(e)})

# --- ツール2: 現在地のIP情報取得 (ip-api.com) ---
def get_current_ip_info():
    """現在のIPアドレスと、そこから推測される国・都市情報を取得する"""
    url = "http://ip-api.com/json/"
    try:
        with httpx.Client(timeout=10.0) as http:
            resp = http.get(url)
            resp.raise_for_status()
            data = resp.json()
            # 必要な情報だけ選別して返す
            result = {
                "ip": data.get("query"),
                "country": data.get("country"),
                "city": data.get("city"),
                "isp": data.get("isp")
            }
            return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})

# --- ツール定義 (Schema) ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_bitcoin_price",
            "description": "現在のビットコイン(BTC)価格を取得します。",
            "parameters": {
                "type": "object",
                "properties": {
                    "currency": {"type": "string", "default": "USD"}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_ip_info",
            "description": "ユーザーの現在のIPアドレスと、物理的な位置情報（国、都市）を取得します。",
            "parameters": {
                "type": "object",
                "properties": {}, # 引数は不要
            },
        },
    }
]

# 実行する関数をマッピング
available_functions = {
    "get_bitcoin_price": get_bitcoin_price,
    "get_current_ip_info": get_current_ip_info,
}

def main():
    # 会話履歴を保持するリスト (Systemプロンプトでキャラ付け)
    messages = [
        {"role": "system", "content": "あなたは優秀なネットワーク兼金融アシスタントです。質問には簡潔に答えてください。"}
    ]

    print("=== AI Assistant (type 'exit' to quit) ===")
    print("Capabilities: 1. Bitcoin Price, 2. IP Location Info")

    while True:
        # ユーザー入力の受付
        user_input = input("\nUser: ").strip()
        if user_input.lower() == "exit":
            print("System: 終了します。")
            break
        if not user_input:
            continue

        # ユーザーの発言を履歴に追加
        messages.append({"role": "user", "content": user_input})

        # --- 1回目のAPI呼び出し (回答またはツール要求) ---
        try:
            response = client.chat.completions.create(
                model="gpt-4o", # gpt-3.5-turbo 等でも可
                messages=messages,
                tools=tools,
                tool_choice="auto", # AIに判断を委ねる
            )
        except Exception as e:
            print(f"System Error: {e}")
            continue

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # --- 分岐処理 ---
        if tool_calls:
            # A. ツールを使う必要がある場合
            
            # 1. AIの「ツールを使いたい」という思考を履歴に追加 (必須)
            messages.append(response_message)
            
            # 2. 要求された全ツールを実行 (並列呼び出し対応)
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions.get(function_name)
                
                if function_to_call:
                    # 引数があればパース（今回はあまり使いませんが汎用的に）
                    function_args = json.loads(tool_call.function.arguments)
                    
                    print(f"[System] Tool Calling: {function_name} ...")
                    
                    # 関数実行
                    function_response = function_to_call(**function_args)
                    
                    # 3. 実行結果を履歴に追加
                    messages.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": function_response,
                        }
                    )
            
            # 4. ツールの結果を踏まえて、もう一度AIに回答を生成させる
            second_response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
            )
            final_content = second_response.choices[0].message.content
            
            # AIの最終回答を表示＆履歴に追加
            print(f"AI: {final_content}")
            messages.append({"role": "assistant", "content": final_content})

        else:
            # B. ツールが不要な場合 (普通の会話)
            final_content = response_message.content
            print(f"AI: {final_content}")
            messages.append({"role": "assistant", "content": final_content})

if __name__ == "__main__":
    main()
