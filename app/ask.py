"""第1回: 会話履歴を保ちながら素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

ツールは使わず、同じプロセス内の質問履歴を保つ「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"

_client = None
_chat = None


def ask(question: str) -> str:
    global _client, _chat
    if _chat is None:
        _client = genai.Client(api_key=get_api_key())
        _chat = _client.chats.create(model=MODEL)

    response = _chat.send_message(question)

    usage = response.usage_metadata
    print(f"[tokens] 入力: {usage.prompt_token_count}, 出力: {usage.candidates_token_count}")

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    question = args.question
    while question:
        print(f"[質問] {question}\n")
        try:
            print(ask(question))
        except errors.APIError as e:
            print(api_error_message(e.code, e.message))
            raise SystemExit(1)

        try:
            question = input("\n続けて質問してください（終了するには空行）: ").strip()
        except EOFError:
            break


if __name__ == "__main__":
    main()
