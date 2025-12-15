import os
import json
import time
import threading
import requests
import pytest

from pathlib import Path

# Ensure project root on path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import app after adjusting sys.path
from app import app


def _run_app(port=5001):
    app.run(port=port, debug=False, use_reloader=False)


def wait_for_server(url, timeout=5.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            requests.get(url, timeout=0.5)
            return True
        except Exception:
            time.sleep(0.1)
    return False


def load_fixture(name):
    p = Path(__file__).parents[1] / 'fixtures' / name
    return json.loads(p.read_text())


def test_e2e_translate_and_judge():
    # Ensure Playwright is installed and provides sync API
    pytest.importorskip('playwright', reason='Playwright not installed')
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        pytest.skip('Playwright sync API not available in this environment')

    port = 5001
    url = f'http://127.0.0.1:{port}/'

    server_thread = threading.Thread(target=_run_app, kwargs={'port': port}, daemon=True)
    server_thread.start()
    assert wait_for_server(url), 'Server did not start in time'

    translate_fixture = load_fixture('translate_response.json')
    judge_fixture = load_fixture('judge_response.json')

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except Exception as e:
            pytest.skip(f'Unable to launch Playwright browser: {e}')

        context = browser.new_context()
        page = context.new_page()

        # intercept API calls and return fixtures
        def handle_route(route, request):
            body = request.post_data or '{}'
            req_json = json.loads(body) if body else {}
            model = req_json.get('model', '')
            if 'Qwen' in model:
                route.fulfill(status=200, body=json.dumps(translate_fixture), headers={'Content-Type': 'application/json'})
            else:
                route.fulfill(status=200, body=json.dumps(judge_fixture), headers={'Content-Type': 'application/json'})

        page.route('https://api.mentorpiece.org/v1/process-ai-request', handle_route)

        page.goto(url)
        page.fill('#source_text', 'Hello world')
        page.select_option('#target_lang', 'Французский')
        page.click('button[name="action"][value="translate"]')
        # wait for translation to appear
        page.wait_for_selector('pre', timeout=2000)
        content = page.locator('h5:has-text("Перевод") + .card .card-body pre').inner_text()
        assert 'Bonjour le monde' in content

        # Now click judge — the route returns judge_fixture
        page.click('button[name="action"][value="judge"]')
        page.wait_for_timeout(300)  # give JS a moment
        verdict = page.locator('h5:has-text("Вердикт судьи") + .card .card-body pre').inner_text()
        assert 'Оценка' in verdict

        browser.close()
