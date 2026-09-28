# Brandcraft: AI Brand Identity and Strategy Platform

Brandcraft helps founders create a practical brand strategy through a guided six-question interview. The default `mock` AI mode is fully offline and makes no Gemini request.

## Run on Windows PowerShell

```powershell
cd C:\Users\bhava\Downloads\brand-platform
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
py manage.py migrate
py manage.py runserver
```

Open `http://127.0.0.1:8000/`.

Keep `AI_MODE=mock` in `.env` for the college demo. It works without an API key, internet connection, billing, or Gemini quota.

## Tests

```powershell
py manage.py check
py manage.py makemigrations --check --dry-run
py manage.py test -v 2
```

## Optional live Gemini mode

Only when intentionally testing a configured free-tier key, set `AI_MODE=gemini` and `GEMINI_API_KEY` in `.env`. Do not commit `.env`. The application returns friendly errors for a missing SDK/key, quota limit, or provider failure.
