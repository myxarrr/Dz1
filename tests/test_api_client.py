import os
import types
import sys
import pytest

# Ensure project root is on sys.path so tests can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import extract_text_from_response, call_mentorpiece


def test_extract_from_choices_text():
    resp = {"choices": [{"text": "Перевод"}]}
    assert extract_text_from_response(resp) == "Перевод"


def test_extract_from_message_content():
    resp = {"choices": [{"message": {"content": "Содержимое"}}]}
    assert extract_text_from_response(resp) == "Содержимое"


def test_extract_from_top_level():
    resp = {"result": "Результат"}
    assert extract_text_from_response(resp) == "Результат"


def test_extract_from_outputs():
    resp = {"outputs": [{"content": "Вывод"}]}
    assert extract_text_from_response(resp) == "Вывод"


def test_call_mentorpiece_sets_headers(monkeypatch):
    # Arrange
    os.environ['MENTORPIECE_API_KEY'] = 'testkey'

    captured = {}

    class FakeResp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"result": "ok"}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured['url'] = url
        captured['headers'] = headers
        captured['json'] = json
        captured['timeout'] = timeout
        return FakeResp()

    monkeypatch.setattr('requests.post', fake_post)

    # Act
    res = call_mentorpiece('model-x', 'prompt')

    # Assert
    assert res == {"result": "ok"}
    assert captured['headers']['Authorization'] == 'Bearer testkey'
    assert captured['headers']['Content-Type'] == 'application/json'
