# pip install numpy
import numpy as np
# pip install google-genai
# https://ai.google.dev/gemini-api/docs/migrate?hl=ja
from google import genai
import os
import tomllib

with open(".secrets.toml", "rb") as s:
    secrets = tomllib.load(s)
client = genai.Client(api_key=secrets.get("API_KEY"))

# --- 2. ベクトル化関数 (Gemini) ---
OUTPUT_DIMENSIONALITY = None
MODEL = "models/text-embedding-004"
def get_embedding(doc):
    result = client.models.embed_content(
        model=MODEL,
        contents=doc['text'],
        config=genai.types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            title=doc['title'],
            output_dimensionality=OUTPUT_DIMENSIONALITY,
        ),
    )
    return np.array(result.embeddings[0].values)

# --- 3. 自作データベース (ただのリスト) ---
# ここに辞書形式でデータを詰め込みます
my_simple_db = []

documents = [
    {"title": "交通費規定", "text": "自宅から会社までの往復運賃を月額上限5万円まで全額支給します。"},
    {"title": "リモートワーク規定", "text": "申請は前日の18時までに行ってください。"},
    {"title": "リモートワーク規定", "text": "週3回まで許可されます。"},
    {"title": "経費精算規定", "text": "毎月25日締め切りです。領収書の原本提出が必須です。"},
    {"title": "福利厚生", "text": "オフィス内のドリンクサーバーは無料です。金曜17時からはビールも可。"},
]

print("データをベクトル化してメモリに保存中...")

for doc in documents:
    # ベクトル化
    vector = get_embedding(doc)
    
    # リストに追加 (これがDBへの保存と同じこと)
    my_simple_db.append({
        "text": doc['text'],
        "title": doc['title'],
        "vector": vector
    })

print(f"完了。{len(my_simple_db)}件のデータを保持しています。\n")


# --- 4. 検索エンジンの心臓部 (コサイン類似度) ---
# これが ChromaDB の中で行われている計算の正体です。
def cosine_similarity(v1, v2):
    # 内積をとって、長さで割る = 角度の近さを計算
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def search(query_text):
    print(f"[System] 検索クエリ: {query_text}")
    
    # (A) 質問をベクトル化（task_typeはqueryにする）
    result = client.models.embed_content(
        model=MODEL,
        contents=query_text,
        config=genai.types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=OUTPUT_DIMENSIONALITY),
    )
    query_vec = np.array(result.embeddings[0].values)

    # (B) 全データと比較計算
    results = []
    for item in my_simple_db:
        # ここで類似度スコアを計算！
        score = cosine_similarity(query_vec, item['vector'])
        results.append({
            "title": item['title'],
            "text": item['text'],
            "score": score
        })
    
    # (C) スコアが高い順に並び替え
    results.sort(key=lambda x: x['score'], reverse=True)
    for x in results:
        print(x['score'], x['title'], x['text'])
    return results

# --- 5. 実行してみる ---
user_query = "リモートワークっていつまでに申請？"
top_result = search(user_query)

print("-" * 30)
print(f"最も近いデータ (スコア: {top_result[0]['score']:.4f})")
print(f"タイトル: {top_result[0]['title']}")
print(f"内容: {top_result[0]['text']}")
print("-" * 30)

t = [f'{x["title"]}:{x["text"]}' for x in top_result]
print(t)
# --- 6. 生成AIに回答させる ---
print("Geminiに回答を生成させます...")
prompt = f"""
以下の情報を元に質問に答えてください。
情報: {t}
質問: {user_query}
"""
response = client.models.generate_content(
    model='gemini-flash-latest',
    contents=prompt)
print(f"Gemini: {response.text}")
