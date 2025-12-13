import json
import os
import google.generativeai as genai

# --- 設定 ---
API_KEY = os.getenv("GOOGLE_API_KEY", "あなたの_API_KEY_をここに入力")
INPUT_FILE = "titles.json"
OUTPUT_FILE = "title-jp.json"

# Geminiの設定
genai.configure(api_key=API_KEY)

def translate_all_at_once():
    # 1. JSONファイルの読み込み
    if not os.path.exists(INPUT_FILE):
        print(f"エラー: {INPUT_FILE} が見つかりません。")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        print("データが空です。")
        return

    print(f"{len(data)} 件のデータを読み込みました。一括翻訳を実行中...")

    # 2. プロンプトの作成
    # データ量が非常に多い場合でも、Gemini 1.5 Flashは100万トークンまで扱えるため
    # 基本的にそのまま渡して大丈夫です。
    prompt = f"""
    You are a professional translator for academic papers (Physics, AI, Engineering).
    
    Please process the following JSON data.
    For each item in the list, translate the "title" value into Japanese suitable for an academic context.
    Add a new key "title_jp" to each item with the translation.
    
    Output the result as a raw JSON list. Do not use Markdown code blocks.
    
    Input JSON:
    {json.dumps(data, ensure_ascii=False)}
    """

    # 3. API呼び出し (JSONモードを使用)
    # response_mime_type="application/json" を指定することで、確実にJSONが返ってきます
    model = genai.GenerativeModel(
        "gemini-flash-lite-latest",
        generation_config={"response_mime_type": "application/json"}
    )

    try:
        response = model.generate_content(prompt)
        
        # 結果のテキストをJSONとしてパース
        translated_data = json.loads(response.text)
        
        # 4. ファイルへの保存
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(translated_data, f, indent=2, ensure_ascii=False)
            
        print(f"成功！ '{OUTPUT_FILE}' に保存しました。")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        # エラー時のデバッグ用に生のレスポンスを表示することをお勧めします
        if 'response' in locals():
            print("Raw response:", response.text)

if __name__ == "__main__":
    translate_all_at_once()
