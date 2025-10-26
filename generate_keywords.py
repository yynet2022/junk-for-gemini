# -*- coding:utf-8 -*-

import tomllib
import google.generativeai as genai
import json

# --- APIキーなどの取得 ---
with open(".secrets.toml", "rb") as s:
    secrets = tomllib.load(s)

# --- APIキーの読み込み ---
API_KEY = secrets["API_KEY"]
genai.configure(api_key=API_KEY)

# --- モデルの初期化 ---
SYSTEM_PROMPT = '''
## 指示
* 私が指定する単語（カテゴリ）で、検索する際に役立つ関連キーワードを、まずは以下の２つの種類に分けて最低2個、最大5個ずつ提案しなさい。
    - （ほぼ）普遍的な関連語句: 指定した単語（カテゴリ）のニュースや学習において、時代を問わず基本となる重要なキーワード。
    - 「今」を反映する関連語句: 指定した単語（カテゴリ）での現在の情勢や政策、トレンドを反映した、今まさに注目されているキーワード。
* その上で、さらなる関連語句として、「普遍的な関連語句」に関連する語句と「旬な関連語句」に関連する語句を、まとめて最低2個、最大5個提案しなさい。

## 出力形式
* それぞれの関連語句を、以下の JSON 形式で出力しなさい。
* 語句は、検索でそのまま使えるような **シンプルな単語や略称** にしなさい。（良い例: "GDP", "GX"、悪い例: "AI・機械学習", "UNIX/Linux"）
* description の **簡易説明** に、その語句の簡易的な説明（必要であれば正式名称も含む）を入れなさい。

## 注意点
* 関連語句は、ユニークであること。同じ単語を複数回出力させないこと。
* ユーザーは日本人であることを前提とし、関連語句の表記（英語、カタカナ、ひらがな、漢字）は、日本での浸透度合いを考慮すること。例えば OS AI DX などは英語 (ASCII) でよいが、例えばクラウド、セキュリティなどは英語よりカタカナ表記が適切。
{
  "universal": [
    {"name": "語句1", "description": "簡易説明"},
    {"name": "語句2", "description": "簡易説明"},
    ...
  ],
  "current": [
    {"name": "語句A", "description": "簡易説明"},
    {"name": "語句B", "description": "簡易説明"},
    ...
  ],
  "related": [
    {"name": "語句I", "description": "簡易説明"},
    {"name": "語句II", "description": "簡易説明"},
    ...
  ]
}
'''  # noqa: E501

# --- GenerationConfig で JSON 出力を指定 ---
GENERATION_CONFIG = {
    "response_mime_type": "application/json",
}

# --- Gemini モデルの作成 ---
model = genai.GenerativeModel(
    'gemini-flash-latest',
    system_instruction=SYSTEM_PROMPT,
    generation_config=GENERATION_CONFIG
)


def generate_keywords_by(name, prompt, jsonfile, is_debug=False):

    # メッセージを送信して、応答を生成
    response = model.generate_content(prompt)

    if is_debug:
        print("Response from Gemini (raw JSON text):")
        print(response.text)

    try:
        # --- response.text を json.loads でパース ---
        data = json.loads(response.text)
        data["name"] = name

        with open(jsonfile, "w", encoding='utf-8') as fp:
            json.dump(data, fp, ensure_ascii=False)

        if is_debug:
            print("\n--- Parsed Python data (dictionary) ---")
            print(data)

            print("\n--- Data access example ---")
            print("Universal terms:")
            # dataが辞書なので、キーを指定してアクセスできる
            for item in data.get("universal", []):
                print(f"- {item['name']}: {item['description']}")

            print("\nCurrent terms:")
            for item in data.get("current", []):
                print(f"- {item['name']}: {item['description']}")

            print("\nRelated terms:")
            for item in data.get("related", []):
                print(f"- {item['name']}: {item['description']}")

    except json.JSONDecodeError:
        print("\nError: Response from Gemini was not valid JSON.")
        print("Raw text:", response.text)

    # --- トークン数を表示するコードを追加 ---
    print("\n--- Token usage ---")
    print(f"Input tokens: {response.usage_metadata.prompt_token_count}")
    print(f"Output tokens: {response.usage_metadata.candidates_token_count}")
    print(f"Total tokens: {response.usage_metadata.total_token_count}")


# Gemini に送るメッセージ（プロンプト）を作成
# word = '経済'
# word = 'IT'
# word = 'テクノロジー（ただし IT は除く）'
list = [['経済', '経済', 'economy.json'],
        ['IT',   'IT',   'it.json'],
        ['テクノロジー', 'テクノロジー（ただし IT は除外）', 'technology.json'],
        ['半導体', '半導体', 'semiconductor.json'],
        ]
for i in list:
    print(*i)
    generate_keywords_by(*i)
