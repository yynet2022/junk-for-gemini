import json
import os
import httpx
from openai import OpenAI

# --- 設定 ---
# 環境変数 'OPENAI_API_KEY' が設定されている前提ですが、ここに直接書いても動きます
API_KEY = os.getenv("OPENAI_API_KEY", "あなたの_API_KEY_をここに入力")

INPUT_FILE = "titles.json"
OUTPUT_FILE = "title-jp.json"

def translate_with_gpt():
    # 1. JSONファイルの読み込み
    if not os.path.exists(INPUT_FILE):
        print(f"エラー: {INPUT_FILE} が見つかりません。")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        print("データが空です。")
        return

    print(f"{len(data)} 件のデータを読み込みました。GPT-4o-mini で一括翻訳中...")

    # 2. httpx クライアントの作成 (タイムアウトなどを設定可能)
    # ユーザーの指定通り httpx を明示的に使用します
    http_client = httpx.Client(
        timeout=60.0,  # 一括処理なので少し長めに設定
        # proxy="http://proxy.example.com:8080", # プロキシが必要な場合はここで設定可能
    )

    # OpenAI クライアントの初期化 (http_clientを注入)
    client = OpenAI(
        api_key=API_KEY,
        http_client=http_client
    )

    # 3. プロンプトの作成
    # GPTのJSONモードはルートがオブジェクトである必要があるため、
    # データを "items" キーの下に配置するよう指示します。
    system_prompt = """
    You are a professional translator for academic papers (Physics, AI, Engineering).
    Output valid JSON only.
    """

    user_prompt = f"""
    Translate the "title" of the following papers into Japanese suitable for an academic context.
    Return the result as a JSON object with a key "items".
    The "items" list should contain objects with the original "title" and the translated "title_jp".

    Input Data:
    {json.dumps(data, ensure_ascii=False)}
    """

    try:
        # 4. API呼び出し
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # コスパ最強モデル
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}  # JSONモードを強制
        )

        # 5. レスポンスの解析
        content = response.choices[0].message.content
        result_json = json.loads(content)
        
        # "items" キーの中身を取り出す
        translated_data = result_json.get("items", [])

        # 6. ファイルへの保存
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(translated_data, f, indent=2, ensure_ascii=False)

        print(f"成功！ '{OUTPUT_FILE}' に保存しました。")
        print(f"消費トークン: {response.usage.total_tokens}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    translate_with_gpt()
