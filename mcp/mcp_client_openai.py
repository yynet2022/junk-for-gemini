import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AsyncOpenAI

# サーバーの設定 (server.py は使い回し)
server_params = StdioServerParameters(
    command="python",
    args=["server.py"],
)

async def main():
    # 1. MCPサーバーと接続
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 2. ツール定義を取得して OpenAI 形式に変換
            tools_list = await session.list_tools()
            openai_tools = []
            for tool in tools_list.tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema 
                    }
                })

            # 3. OpenAI クライアント初期化
            client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
            model_id = "gpt-4o" # または gpt-3.5-turbo など

            messages = [] # 会話履歴

            print("=== OpenAI + MCP Chat Client Started ===")
            print("Type 'exit' to quit.\n")

            while True:
                user_input = input("You: ")
                if user_input.lower() in ["exit", "quit"]:
                    break

                # ユーザーの入力を履歴に追加
                messages.append({"role": "user", "content": user_input})

                # --- 1回目の推論 ---
                response = await client.chat.completions.create(
                    model=model_id,
                    messages=messages,
                    tools=openai_tools,
                    tool_choice="auto"
                )

                response_message = response.choices[0].message
                
                # AIの応答（思考やツール呼び出し）を履歴に追加
                messages.append(response_message)

                # ツール呼び出しがあるかチェック
                if response_message.tool_calls:
                    for tool_call in response_message.tool_calls:
                        fn_name = tool_call.function.name
                        fn_args = json.loads(tool_call.function.arguments)
                        
                        print(f"[System] Calling MCP Tool: {fn_name}({fn_args})...")

                        # --- MCP ツール実行 ---
                        try:
                            result = await session.call_tool(fn_name, arguments=fn_args)
                            tool_output = result.content[0].text
                            print(f"[System] Tool Output: {tool_output}")
                        except Exception as e:
                            tool_output = f"Error: {str(e)}"

                        # --- 結果を OpenAI に返す ---
                        # role="tool" で、tool_call_id を指定して紐付けるのが OpenAI 流です
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_output
                        })

                    # --- 2回目の推論（結果を受けての回答） ---
                    final_response = await client.chat.completions.create(
                        model=model_id,
                        messages=messages,
                        # ここではツール定義は必須ではないですが、連続呼び出しのために残してもOK
                    )
                    
                    final_text = final_response.choices[0].message.content
                    print(f"OpenAI: {final_text}")
                    messages.append({"role": "assistant", "content": final_text})

                else:
                    # ツール呼び出しがなかった場合
                    print(f"OpenAI: {response_message.content}")

if __name__ == "__main__":
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
