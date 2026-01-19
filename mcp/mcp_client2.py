# client2.py
import asyncio
import os
import sys

from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# サーバーの設定 (server.py が同じ場所にある前提)
server_params = StdioServerParameters(
    command="python",
    args=["mcp_server.py"],
)

async def main():
    # 1. MCPサーバーと接続開始
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 2. ツール定義の取得と変換
            tools_list = await session.list_tools()
            gemini_tools = []
            for tool in tools_list.tools:
                gemini_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                })

            # 3. Gemini クライアント初期化
            client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
            model_id = "gemini-flash-lite-latest"
            
            # 会話履歴を保持するリスト
            chat_history = []

            print("=== Gemini + MCP Chat Client Started ===")
            print("Type 'exit' to quit.\n")

            # 4. チャットループ開始
            while True:
                user_input = input("You: ")
                if user_input.lower() in ["exit", "quit"]:
                    break

                # ユーザーの発言を履歴に追加
                chat_history.append(types.Content(
                    role="user",
                    parts=[types.Part(text=user_input)]
                ))

                # --- 1回目の推論: ツールを使うべきか判断 ---
                response = client.models.generate_content(
                    model=model_id,
                    contents=chat_history,
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(function_declarations=gemini_tools)]
                    )
                )

                # Geminiの応答（思考/ツール呼び出し）を履歴に追加
                # これをしないと「文脈」が途切れます
                chat_history.append(response.candidates[0].content)

                # ツール呼び出しが含まれているかチェック
                function_called = False
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        function_called = True
                        fc = part.function_call
                        print(f"[System] Calling MCP Tool: {fc.name}({fc.args})...")

                        # --- MCP ツール実行 ---
                        try:
                            result = await session.call_tool(fc.name, arguments=fc.args)
                            tool_output = result.content[0].text
                            print(f"[System] Tool Output: {tool_output}")
                        except Exception as e:
                            tool_output = f"Error: {str(e)}"

                        # --- 結果を Gemini に返す準備 ---
                        # FunctionResponse を作成して履歴に追加します
                        response_part = types.Part(
                            function_response=types.FunctionResponse(
                                name=fc.name,
                                response={"result": tool_output} 
                            )
                        )
                        # Gemini のルール上、関数の結果は role="user" として扱います
                        chat_history.append(types.Content(
                            role="user", 
                            parts=[response_part]
                        ))

                        # --- 2回目の推論: 結果を踏まえて最終回答 ---
                        final_response = client.models.generate_content(
                            model=model_id,
                            contents=chat_history,
                             # 2回目もツール定義を入れておくと連続実行も可能です
                            config=types.GenerateContentConfig(
                                tools=[types.Tool(function_declarations=gemini_tools)]
                            )
                        )
                        
                        # 最終回答を表示＆履歴へ
                        final_text = final_response.text
                        print(f"Gemini: {final_text}")
                        chat_history.append(final_response.candidates[0].content)

                # ツール呼び出しがなかった場合（普通の雑談など）
                if not function_called:
                    text = response.text
                    if text:
                        print(f"Gemini: {text}")

if __name__ == "__main__":
    # Windowsの非同期ループ対策
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
