import os
from datetime import datetime
from typing import Literal, Union

import instructor
import openai
from pydantic import BaseModel, Field, field_validator


# --- 1. ベースとなる抽象クラス的な役割 ---
class ToolBase(BaseModel):
    def execute(self) -> str:
        """各ツールが実行ロジックを実装する"""
        raise NotImplementedError("Subclasses must implement execute()")


# --- 2. 各ツールの定義 ---


class GetTimestamp(ToolBase):
    """現在の時刻を取得します。"""

    action: Literal["get_timestamp"] = "get_timestamp"

    def execute(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class GetOSName(ToolBase):
    """実行環境のOS名を取得します。"""

    action: Literal["get_os_name"] = "get_os_name"

    def execute(self) -> str:
        return f"OS Name: {os.name}"


class GetEnvVar(ToolBase):
    """指定された環境変数（PATH, SHELL, USERなど）の値を取得します。"""

    action: Literal["get_env_var"] = "get_env_var"
    # 引数が必要なアクション
    env_name: str = Field(..., description="取得したい環境変数名")

    @field_validator("env_name")
    @classmethod
    def validate_env_name(cls, v):
        # バリデーション例: 許可されていない変数や空文字をチェック
        forbidden = ["PASSWORD", "SECRET_KEY"]
        if v.upper() in forbidden:
            raise ValueError(f"セキュリティ上の理由で {v} は取得できません。")
        if not v:
            raise ValueError("環境変数名が空です。")
        return v.upper()

    def execute(self) -> str:
        value = os.environ.get(self.env_name, "見つかりませんでした")
        return f"Environment Variable '{self.env_name}': {value}"


class FinalResponse(BaseModel):
    """ユーザーへの最終回答。これ以上ツールが必要ない時に使用します。"""

    action: Literal["final_answer"] = "final_answer"
    answer: str = Field(..., description="ユーザーへの最終的な返答内容")

    def execute(self) -> str:
        return self.answer


# ツール群の定義
Tools = Union[GetTimestamp, GetOSName, GetEnvVar, FinalResponse]

# --- 3. エージェントのコアロジック ---

client = instructor.from_openai(openai.OpenAI())


def ask_ai_loop():
    messages = [
        {
            "role": "system",
            "content": "あなたはシステム管理アシスタントです。ツールを駆使して回答してください。",
        }
    ]

    while True:
        user_input = input("\nユーザー: ")
        if user_input.lower() in ["exit", "quit", "終了"]:
            break

        messages.append({"role": "user", "content": user_input})

        while True:
            try:
                # max_retries を設定することで、Pydanticのバリデーションエラー時に
                # instructor が LLM にエラーメッセージを添えて再生成を依頼する
                response = client.chat.completions.create(
                    model=os.environ.get("OPENAI_MODEL"),
                    response_model=Tools,
                    messages=messages,
                    max_retries=3,  # バリデーション失敗時の自動リトライ回数
                )
            except Exception as e:
                print(f" (Error: リトライ上限に達しました - {e})")
                break

            # 多態性（ポリモーフィズム）を利用した実行
            # クラスが何であるかを確認せず、共通のインターフェースを叩く
            result = response.execute()

            if response.action == "final_answer":
                print(f"\nAI: {result}")
                messages.append({"role": "assistant", "content": result})
                break

            # ログ出力と履歴追加
            print(f" (System Log: {response.action} を実行中...)")
            messages.append(
                {
                    "role": "assistant",
                    "content": f"Performed {response.action}",
                }
            )
            messages.append({"role": "system", "content": f"Result: {result}"})


if __name__ == "__main__":
    ask_ai_loop()
