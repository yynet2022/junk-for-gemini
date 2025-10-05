#
# ※注意
# このスクリプトは動いていない。Google Search がうまく動かない。
# Not supported. と言われる。
# これの代替として、自分で Google 検索する仕組みに移行。
# news_bot.py を参照
#
import tomllib
import google.generativeai as genai
from google.generativeai.types import Tool

with open(".secrets.toml", "rb") as s:
    secrets = tomllib.load(s)

# 1. APIキーを設定
#    先ほどコピーしたご自身のAPIキーに書き換えてください。
# API_KEY = "ここにあなたのAPIキーを貼り付けます"
API_KEY = secrets["API_KEY"]
genai.configure(api_key=API_KEY)

# 2. モデルを選択
#    今回は最も標準的な gemini-pro を使います。
# model = genai.GenerativeModel('gemini-pro-latest')
# もしくは、バージョンを明記する
# model = genai.GenerativeModel('gemini-2.5-pro')
#
system_prompt = 'ハードボイルド口調で答えてください。'
model = genai.GenerativeModel(
    'gemini-2.5-flash',
    tools=[Tool(google_search_retrieval={})],
    system_instruction=system_prompt)

# 3. Geminiに送るメッセージ（プロンプト）を作成
prompt = "自民党新総裁となった人は誰？"

# 4. メッセージを送信して、応答を生成
response = model.generate_content(prompt)

# 5. 応答からテキストだけを取り出して表示
print("Geminiからの応答:")
print(response.text)

# --- トークン数を表示するコードを追加 ---
print("\n--- トークン情報 ---")
print(f"入力トークン数: {response.usage_metadata.prompt_token_count}")
print(f"出力トークン数: {response.usage_metadata.candidates_token_count}")
print(f"合計トークン数: {response.usage_metadata.total_token_count}")
