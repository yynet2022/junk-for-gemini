# pip install chromadb
import chromadb
from openai import OpenAI

client = OpenAI()

# --- 1. テキストをベクトル(数字の列)に変換する関数 ---
# これがRAGの肝です。「意味」を「数字」に変換します。
def get_embedding(text: str):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small" # 安くて高性能な最新モデル
    )
    # 1536次元の浮動小数点のリストが返ってきます
    return response.data[0].embedding

# --- 2. ChromaDBの準備 ---
# ローカルの "./my_rag_db" フォルダにデータを保存する設定
chroma_client = chromadb.PersistentClient(path="./my_rag_db")

# コレクション（RDBでいうテーブルのようなもの）を作成
# すでにあったらそれを取得、なければ新規作成
collection = chroma_client.get_or_create_collection(name="company_knowledge")

# --- 3. 登録するデータ（ダミーの社内規定） ---
documents = [
    "交通費規定：自宅から会社までの往復運賃を月額上限5万円まで全額支給します。",
    "リモートワーク規定：週3回まで許可されます。申請は前日の18時までに行ってください。",
    "経費精算：毎月25日締め切りです。領収書の原本提出が必須です。",
    "福利厚生：オフィス内のドリンクサーバーは無料です。金曜17時からはビールも可。",
]

print("データをベクトル化して登録中...")

# データを一つずつDBに追加
for i, doc in enumerate(documents):
    # (A) テキストをベクトル化
    vector = get_embedding(doc)
    
    print(f"登録中: {doc[:10]}... (Vector dim: {len(vector)})")
    
    # (B) DBに保存
    collection.upsert(
        ids=[str(i)],       # ID (一意である必要あり)
        embeddings=[vector],# ベクトルデータ (検索に使われる)
        documents=[doc]     # 元のテキスト (検索結果として人間に見せる用)
    )

print("完了！ './my_rag_db' フォルダに保存されました。")
