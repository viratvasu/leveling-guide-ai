# Leveling Guide AI

AI-powered tool that generates specific, actionable examples for company leveling guides. Upload your CSV framework and get 3 concrete examples per competency cell showing what employees can do to demonstrate they're operating at each level.

## Live Demo
🌐 **[http://13.201.30.246](http://13.201.30.246)**

## Features

- 📤 CSV upload with instant parsing
- 🤖 AI generates 3 examples per cell (~15-30 sec for full grid)
- 🔄 Regenerate individual cells with feedback
- 📊 Version history and rollback
- 🔐 Multi-company with permissions

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Django + Gunicorn |
| Frontend | React + Vite |
| Database | SQLite |
| AI | Anthropic Claude Sonnet |
| Hosting | EC2 + Nginx |

## Quick Start

### Backend
```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables

Create a `.env` file in the root directory:
```
DEBUG=True
DJANGO_SECRET_KEY=your-secret-key
ANTHROPIC_API_KEY=sk-ant-your-api-key
ALLOWED_HOSTS=localhost,127.0.0.1
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login/` | User login |
| POST | `/api/guides/upload/` | Upload CSV |
| POST | `/api/guides/<id>/generate/` | Generate all examples |
| POST | `/api/guides/<id>/regenerate-cell/` | Regenerate one cell |
| GET | `/api/guides/current/` | Get active guide |
| GET | `/api/health/` | Health check |

## Project Structure

```
leveling_guide_ai/
├── app/                    # Django app
│   ├── models.py          # User, Company, LevellingGuide
│   ├── views.py           # API endpoints
│   └── services.py        # AI generation logic
├── frontend/
│   ├── src/components/    # React components
│   └── src/pages/         # Page views
└── leveling_guide_ai/     # Django config
```

## License

MIT
