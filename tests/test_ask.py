import sys
from types import SimpleNamespace
from unittest.mock import call, Mock

from app import ask as ask_module


def test_ask_reuses_chat_history_and_prints_token_counts(monkeypatch, capsys):
    responses = [
        SimpleNamespace(
            usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=34),
            text="最初の回答",
        ),
        SimpleNamespace(
            usage_metadata=SimpleNamespace(prompt_token_count=20, candidates_token_count=15),
            text="続きの回答",
        ),
    ]
    chat = SimpleNamespace(send_message=Mock(side_effect=responses))
    create_chat = Mock(return_value=chat)
    client = SimpleNamespace(chats=SimpleNamespace(create=create_chat))
    monkeypatch.setattr(ask_module, "_client", None)
    monkeypatch.setattr(ask_module, "_chat", None)
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    assert ask_module.ask("最初の質問") == "最初の回答"
    assert ask_module.ask("続きの質問") == "続きの回答"

    assert ask_module._client is client
    create_chat.assert_called_once_with(model=ask_module.MODEL)
    assert chat.send_message.call_args_list == [call("最初の質問"), call("続きの質問")]
    assert capsys.readouterr().out.splitlines() == [
        "[tokens] 入力: 12, 出力: 34",
        "[tokens] 入力: 20, 出力: 15",
    ]


def test_main_prompts_for_follow_up_questions(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["ask", "最初の質問"])
    questions = iter(["続きの質問", ""])
    monkeypatch.setattr("builtins.input", lambda prompt: next(questions))
    ask_mock = Mock(side_effect=lambda question: f"回答: {question}")
    monkeypatch.setattr(ask_module, "ask", ask_mock)

    ask_module.main()

    assert ask_mock.call_args_list == [call("最初の質問"), call("続きの質問")]