# client.py
import asyncio
import os

from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 実行するサーバーの設定（先ほど作ったファイルを指定）
server_params = StdioServerParameters(
    command="python",
    args=["mcp_server.py"], # 同じフォルダに server.py がある前提
)

async def main():
    # 1. MCPサーバーに接続
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 2. サーバーから使えるツール一覧を取得
            tools_list = await session.list_tools()
            
            # Gemini用にツール定義を変換
            # (MCPのスキーマはGeminiと互換性が高いので、input_schemaをそのまま渡せます)
            gemini_tools = []
            for tool in tools_list.tools:
                gemini_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                })

            # 3. Gemini クライアントの準備
            client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
            
            # 4. ユーザーからの質問（計算が必要な内容）
            prompt = "123 と 456 を足すといくつ？"
            print(f"User: {prompt}")

            # 5. Gemini に問い合わせ (ツール定義を渡す)
            response = client.models.generate_content(
                model="gemini-flash-lite-latest",
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(function_declarations=gemini_tools)]
                )
            )

            # 6. Gemini が「ツールを使いたい」と言ってきたかチェック
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    fc = part.function_call
                    print(f"Gemini: ツール '{fc.name}' を引数 {fc.args} で実行したいようです...")

                    # 7. MCP経由でサーバーのツールを実行
                    result = await session.call_tool(fc.name, arguments=fc.args)
                    print(f"MCP Server: 実行結果 -> {result.content[0].text}")

                    # (本来はこの結果をGeminiに送り返して最終回答を作りますが、
                    #  Hello World なのでここで終了します)

if __name__ == "__main__":
    asyncio.run(main())
