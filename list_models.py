#
import tomllib
import google.generativeai as genai

with open(".secrets.toml", "rb") as s:
    secrets = tomllib.load(s)

# 1. APIキーを設定
#    ご自身のAPIキーに書き換えるか、環境変数から読み込みます。
#    ※ 環境変数 GOOGLE_API_KEY に設定しておくのがおすすめです。
# API_KEY = "ここにあなたのAPIキーを貼り付けます"
API_KEY = secrets["API_KEY"]
genai.configure(api_key=API_KEY)


print("利用可能なモデル:")
# 2. 利用可能なモデルのリストを取得
for m in genai.list_models():
    # 3. テキスト生成 (generateContent) ができるモデルだけをフィルタリング
    if 'generateContent' in m.supported_generation_methods:
        # 4. モデル名を表示
        print(f"  - {m.name}")
