# AI Translator & Critic (Flask Edition)

Проект реализует веб-приложение на Flask, которое переводит текст и оценивает качество перевода через API Mentorpiece.

Локальный запуск

1. Создайте виртуальное окружение и установите зависимости:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Скопируйте `.env.example` в `.env` и укажите `MENTORPIECE_API_KEY`.

3. Запустите приложение:

```bash
export FLASK_APP=app.py
flask run
```

4. Откройте http://127.0.0.1:5000

Примечания

- Используется `requests` для отправки HTTP-запросов к `https://api.mentorpiece.org/v1/process-ai-request`.
- Ключ для API берется из переменной окружения `MENTORPIECE_API_KEY`.

