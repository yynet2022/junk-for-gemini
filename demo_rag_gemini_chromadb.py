#
# pip install google-genai chromadb
import chromadb
# https://ai.google.dev/gemini-api/docs/migrate?hl=ja
from google import genai
import os
import tomllib

with open(".secrets.toml", "rb") as s:
    secrets = tomllib.load(s)
client = genai.Client(api_key=secrets.get("API_KEY"))

DBNAME="./db.my_rag_gemini"

# --- 1. Embedding関数の定義 (Gemini版) ---
def get_gemini_embedding(text: str):
    # Geminiの最新Embeddingモデル
    model = "models/text-embedding-004"
    
    # embed_content メソッドを使います
    result = client.models.embed_content(
        model=model,
        contents=text,
        # 重要: DBに保存するデータを作る時は 'retrieval_document' を指定
        config={'task_type': "retrieval_document",
                'title': '社内規定'}  # documentの場合はtitleがあると精度が良い（任意）
    )
    return result.embeddings

# --- 2. ChromaDBの準備 ---
# 保存先（OpenAI版と混ざらないように）
chroma_client = chromadb.PersistentClient(path=DBNAME)

# コレクション作成
collection = chroma_client.get_or_create_collection(name="company_knowledge")

# --- 3. 登録データ ---
documents = [
    "交通費規定：自宅から会社までの往復運賃を月額上限5万円まで全額支給します。",
    "リモートワーク規定：週3回まで許可されます。申請は前日の18時までに行ってください。",
    "経費精算：毎月25日締め切りです。領収書の原本提出が必須です。",
    "福利厚生：オフィス内のドリンクサーバーは無料です。金曜17時からはビールも可。",
]

print("Geminiでベクトル化して登録中...")

for i, doc in enumerate(documents):
    try:
        # (A) Geminiでベクトル化 (768次元のリストが返ります)
        vector = get_gemini_embedding(doc)[0].values
        
        print(f"登録中: {doc[:10]}... (Vector dim: {len(vector)})")
        
        # (B) DBに保存
        collection.upsert(
            ids=[str(i)],
            embeddings=[vector],
            documents=[doc]
        )
    except Exception as e:
        print(f"Error: {e}")

print(f"完了！ '{DBNAME}' に保存されました。")
