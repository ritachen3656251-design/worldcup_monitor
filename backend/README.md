# World Cup Hot Topics Monitor - Backend

AI-powered editorial platform that monitors Chinese football communities for 2026 World Cup news.

## Tech Stack

- **Framework**: FastAPI (async Python web framework)
- **Database**: SQLite with SQLAlchemy ORM
- **Scheduling**: APScheduler (background tasks)
- **AI**: Aliyun Qwen API (relevance filtering, clustering, generation)
- **Scraping**: BeautifulSoup4 + requests
- **ML**: sentence-transformers (embeddings for clustering)

## Project Structure

```
backend/
├── src/
│   ├── api/          # FastAPI routes
│   ├── scrapers/     # Data scraping layer
│   ├── ai/           # AI processing layer
│   ├── models/       # Database models
│   ├── services/     # Business logic
│   ├── core/         # Core utilities (config, database, logging)
│   ├── utils/        # Helper utilities
│   └── main.py       # Application entry point
├── tests/            # Unit and integration tests
├── prompts/          # AI prompt templates
├── data/             # SQLite database and logs
├── config.yaml       # Configuration file
├── .env              # Environment variables (create from .env.example)
└── requirements.txt  # Python dependencies
```

## Setup

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and credentials
   ```

4. **Initialize database**:
   ```bash
   python -c "from src.core.database import init_db; init_db()"
   ```

5. **Run development server**:
   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Configuration

Edit `config.yaml` to customize:
- Scraping intervals and keywords
- AI model selection and limits
- Clustering thresholds
- Content retention policies
- Monitoring settings

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_text.py
```

## Dry-Run Mode

For development without API costs, enable dry-run mode in `config.yaml`:

```yaml
dry_run:
  enabled: true
```

This uses mock data for all AI processing and scraping.

## Constitution Compliance

This project follows strict engineering principles:
- ✅ Prompt-code separation (all prompts in `prompts/`)
- ✅ Configuration externalization (no hardcoded values)
- ✅ Defensive engineering (try-except, input truncation, rate limiting)
- ✅ Raw data preservation (separate from cleaned data)
- ✅ Unified request function (delays, UA rotation, headers)
- ✅ Dry-run mode support

## License

MIT
