# server.py
from mcp.server.fastmcp import FastMCP

# サーバーの名前を定義
mcp = FastMCP("simple-math-server")

# ツール（関数）を定義。型ヒントとdocstringは必須です（AIがここを読みます）
@mcp.tool()
def add(a: int, b: int) -> int:
    """2つの数値を足し算します。"""
    return a + b

if __name__ == "__main__":
    mcp.run()
