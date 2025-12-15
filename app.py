import os
from flask import Flask, render_template, request
from dotenv import load_dotenv
import requests

load_dotenv()

API_URL = "https://api.mentorpiece.org/v1/process-ai-request"
API_KEY = os.getenv("MENTORPIECE_API_KEY")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET', 'dev')


def call_mentorpiece(model: str, prompt: str, timeout: int = 10) -> dict:
    """Send a request to Mentorpiece API and return parsed JSON response."""
    api_key = os.getenv("MENTORPIECE_API_KEY")
    if not api_key:
        raise RuntimeError("MENTORPIECE_API_KEY is not set in environment")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    payload = {
        "model": model,
        "prompt": prompt,
    }

    resp = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def extract_text_from_response(resp_json: dict) -> str:
    """Robustly extract text from various possible response shapes."""
    # Common patterns
    if not isinstance(resp_json, dict):
        return str(resp_json)

    # choices -> text
    choices = resp_json.get("choices") or resp_json.get("output")
    if choices and isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            # message.content
            msg = first.get("message") or first.get("content")
            if isinstance(msg, dict) and msg.get("content"):
                return msg.get("content")
            if isinstance(first.get("text"), str):
                return first.get("text")
            if isinstance(first.get("content"), str):
                return first.get("content")

    # top-level keys
    for key in ("result", "translation", "text", "output", "content"):
        val = resp_json.get(key)
        if isinstance(val, str) and val.strip():
            return val

    # outputs as list of dicts
    outputs = resp_json.get("outputs")
    if isinstance(outputs, list) and outputs:
        o0 = outputs[0]
        if isinstance(o0, dict):
            for k in ("content", "text"):
                if isinstance(o0.get(k), str):
                    return o0.get(k)

    # Fallback to JSON string
    return str(resp_json)


def translate_text(text: str, target_lang: str) -> str:
    prompt = f"Переведи следующий текст на {target_lang}:\n{text}"
    resp = call_mentorpiece("Qwen/Qwen3-VL-30B-A3B-Instruct", prompt)
    return extract_text_from_response(resp)


def judge_translation(src: str, translation: str) -> str:
    prompt = f"Оцени перевод: {src} -> {translation}"
    resp = call_mentorpiece("claude-sonnet-4-5-20250929", prompt)
    return extract_text_from_response(resp)


@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    verdict = None
    src_text = ''
    target_lang = 'Английский'

    if request.method == 'POST':
        src_text = request.form.get('source_text', '').strip()
        target_lang = request.form.get('target_lang', 'Английский')
        action = request.form.get('action')

        if not src_text:
            result = ''
            verdict = 'Введите текст для перевода.'
        else:
            try:
                translation = translate_text(src_text, target_lang)
                result = translation
                if action == 'judge':
                    verdict = judge_translation(src_text, translation)
            except Exception as e:
                result = ''
                verdict = f'Ошибка: {e}'

    return render_template('index.html', source_text=src_text, translation=result, verdict=verdict, target_lang=target_lang)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
