#
import tomllib
import google.generativeai as genai

with open(".secrets.toml", "rb") as s:
    secrets = tomllib.load(s)

# --- APIキーの読み込み（変更なし） ---
API_KEY = secrets["API_KEY"]
genai.configure(api_key=API_KEY)

# --- モデルの初期化（変更なし） ---
system_prompt = 'ハードボイルド口調で答えてください。'
model = genai.GenerativeModel(
    'gemini-flash-latest',
    system_instruction=system_prompt)

# --- ここからがチャット用のコード ---
# 1. チャットセッションを開始
chat = model.start_chat(history=[])

print("チャットを開始します。終了するには 'quit' と入力してください。")

# 2. 無限ループでユーザーからの入力を待ち受ける
while True:
    user_input = input("あなた: ")

    if user_input.lower() == 'quit':
        print("チャットを終了します。")
        break

    # 3. 履歴を考慮して応答を生成
    response = chat.send_message(user_input)

    print(f"Gemini: {response.text}")

    # --- トークン数を表示するコードを追加 ---
    print("\n--- トークン情報 ---")
    print(f"入力トークン数: {response.usage_metadata.prompt_token_count}")
    print(f"出力トークン数: {response.usage_metadata.candidates_token_count}")
    print(f"合計トークン数: {response.usage_metadata.total_token_count}")

# 4. (おまけ) 最後に会話の履歴全体を見てみる
print("\n--- 会話履歴 ---")
for message in chat.history:
    print(f"[{message.role}]: {message.parts[0].text}")
