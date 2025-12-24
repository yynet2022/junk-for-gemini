##
## リモートワークは何時までに申請すればいい？
## お酒飲んでもいいんだっけ？
##
import json
import chromadb
from openai import OpenAI

client = OpenAI()

# --- 1. ChromaDBへの接続 ---
chroma_client = chromadb.PersistentClient(path="./my_rag_db")
collection = chroma_client.get_collection(name="company_knowledge")

# --- 2. 埋め込み関数の再定義 ---
def get_embedding(text: str):
    resp = client.embeddings.create(input=text, model="text-embedding-3-small")
    return resp.data[0].embedding

# --- 3. ツール: 社内知識の検索 (Retrieval) ---
def search_internal_knowledge(query: str):
    """
    社内規定やルールについて検索します。
    """
    print(f"\n[System] RAG検索実行: '{query}'")
    
    # (A) 質問文をベクトル化
    query_vector = get_embedding(query)
    
    # (B) ベクトル同士の距離が近いものを検索 (Cos類似度など)
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=2 # 上位2件を取得
    )
    
    # 結果の整形
    found_texts = results['documents'][0] # リストのリストになっているので[0]
    
    if not found_texts:
        return "関連する情報は見つかりませんでした。"
    
    # AIに読ませるためにテキストを結合して返す
    return "\n---\n".join(found_texts)

# --- 4. ツール定義 ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_internal_knowledge",
            "description": "社内の規定、交通費、リモートワーク、福利厚生などの質問に答えるために使用します。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "検索したい内容"}
                },
                "required": ["query"],
            },
        },
    }
]

available_functions = {"search_internal_knowledge": search_internal_knowledge}

# --- 5. メインループ (前のコードと同じ構造) ---
def main():
    messages = [
        {"role": "system", "content": "あなたは社内の総務アシスタントです。わからないことはツールを使って調べてください。"}
    ]
    print("=== Internal Wiki AI (type 'exit' to quit) ===")

    while True:
        user_input = input("\nUser: ").strip()
        if user_input.lower() == "exit": break
        if not user_input: continue

        messages.append({"role": "user", "content": user_input})

        # --- AI Agent Loop ---
        while True:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
            
            msg = response.choices[0].message
            tool_calls = msg.tool_calls

            if tool_calls:
                messages.append(msg)
                
                for tool_call in tool_calls:
                    fname = tool_call.function.name
                    fargs = json.loads(tool_call.function.arguments)
                    
                    if fname == "search_internal_knowledge":
                        # ツール実行
                        result = search_internal_knowledge(query=fargs["query"])
                        
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": fname,
                            "content": result
                        })
                # ループ継続（検索結果を持って再考）
                continue
            
            else:
                print(f"\nAI: {msg.content}")
                messages.append({"role": "assistant", "content": msg.content})
                break

if __name__ == "__main__":
    main()
