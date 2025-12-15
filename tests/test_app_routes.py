import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app


def test_index_get():
    client = app.test_client()
    resp = client.get('/')
    assert resp.status_code == 200
    assert b'AI Translator & Critic' in resp.data
