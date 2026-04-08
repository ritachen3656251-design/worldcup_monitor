# Research: 世界杯热点监控助手

**Feature**: 001-worldcup-monitor  
**Date**: 2026-04-08  
**Purpose**: Document technology research, decisions, and rationale for implementation

## Overview

This document captures research findings and technical decisions for building the World Cup Hot Topics Monitor. All decisions align with the constitution's MVP Mindset principle and the user's explicit technology requirements.

## Technology Stack Decisions

### Backend Framework: FastAPI

**Decision**: Use FastAPI for the backend web framework

**Rationale**:
- Modern async Python framework with excellent performance
- Built-in OpenAPI documentation generation
- Native support for Pydantic models (type safety)
- Lightweight and fast, suitable for single-server deployment
- Strong ecosystem for building REST APIs

**Alternatives Considered**:
- Flask: More mature but lacks async support and modern features
- Django: Too heavyweight for MVP, includes unnecessary ORM/admin features

**Implementation Notes**:
- Use async/await for I/O-bound operations (database, API calls)
- Leverage Pydantic for request/response validation
- Enable CORS for frontend communication

### AI Provider: Aliyun Qwen API

**Decision**: Use Aliyun's Qwen API for all AI processing (relevance filtering, clustering, generation, credibility scoring)

**Rationale**:
- Excellent Chinese language understanding (critical for 虎扑/懂球帝/B站 content)
- Reliable API with good uptime and support
- Cost-effective compared to OpenAI for Chinese content
- Structured output support for JSON schema responses
- User explicitly specified this choice

**Alternatives Considered**:
- OpenAI GPT-4: Better general capabilities but weaker Chinese support, higher cost
- Local open-source models: Eliminated per clarification (Aliyun API chosen instead)

**Implementation Notes**:
- Use Qwen-Max for complex tasks (detail generation, credibility scoring)
- Use Qwen-Turbo for simple tasks (relevance filtering) to reduce costs
- Implement exponential backoff retry logic (max 3 attempts)
- Track daily API call count with hard limit enforcement

### Database: SQLite

**Decision**: Use SQLite for all data persistence

**Rationale**:
- Zero-configuration, serverless database
- Perfect for single-server deployment
- Sufficient performance for MVP scale (~100 active topics)
- ACID compliance for data integrity
- File-based storage simplifies backup/restore
- Constitution's MVP Mindset: "SQLite until scale demands otherwise"

**Alternatives Considered**:
- PostgreSQL: Overkill for MVP, adds deployment complexity
- MySQL: Similar to PostgreSQL, unnecessary for single-server setup

**Implementation Notes**:
- Use SQLAlchemy ORM for database operations
- Enable WAL mode for better concurrent read performance
- Implement connection pooling (though single-threaded writes)
- Regular vacuum operations to maintain performance

### Task Scheduling: APScheduler

**Decision**: Use APScheduler for periodic tasks (scraping, health monitoring)

**Rationale**:
- Lightweight, in-process scheduler
- No external dependencies (no Redis/RabbitMQ needed)
- Sufficient for MVP with 30-minute scraping cycles
- Easy to configure and monitor
- Constitution's MVP Mindset: "APScheduler until complexity demands otherwise"

**Alternatives Considered**:
- Celery: Too complex for MVP, requires message broker
- Cron jobs: Less flexible, harder to manage programmatically

**Implementation Notes**:
- Use BackgroundScheduler for non-blocking execution
- Configure persistent job store (SQLite) for job state
- Implement job failure handling and retry logic
- Log job execution times and outcomes

### Caching: In-Memory Dictionary

**Decision**: Use Python dict for caching generated cards and detail pages

**Rationale**:
- Simplest possible caching solution
- No external dependencies
- Sufficient for MVP with limited concurrent users
- Fast access times (O(1) lookups)
- Constitution's MVP Mindset: "In-memory dict until performance demands otherwise"

**Alternatives Considered**:
- Redis: Overkill for MVP, adds deployment complexity
- LRU cache: Could be added later if memory becomes concern

**Implementation Notes**:
- Implement TTL-based expiration (30 minutes for cards, 1 hour for details)
- Use threading.Lock for thread-safe access
- Monitor memory usage, implement size limits if needed
- Clear cache on pipeline completion to ensure freshness

### Frontend: React + TailwindCSS

**Decision**: Use React for UI framework and TailwindCSS for styling

**Rationale**:
- React: Industry-standard, component-based architecture
- TailwindCSS: Utility-first CSS, rapid prototyping, consistent design
- Strong ecosystem and community support
- Easy to achieve Perplexity-like visual design
- User explicitly specified this choice

**Alternatives Considered**:
- Vue.js: Simpler learning curve but smaller ecosystem
- Vanilla JS: Too low-level for complex UI requirements

**Implementation Notes**:
- Use Vite for fast development and build
- Implement responsive design (mobile + desktop)
- Use React Query for API state management
- Implement polling service for real-time updates (30s interval)

## Scraping Strategy

### Unified Request Function

**Decision**: Implement a single `unified_request()` function that all scrapers must use

**Requirements** (per constitution):
- Platform-specific delays: 虎扑 5s, 懂球帝 3s, B站 2s
- User-Agent rotation from a pool of 10+ realistic browser UAs
- Browser-mimicking headers (Accept, Accept-Language, Referer, etc.)
- Automatic retry with exponential backoff (max 3 attempts)
- Request/response logging for debugging

**Implementation Notes**:
```python
def unified_request(url: str, platform: str, **kwargs) -> Response:
    """
    Unified HTTP request function with delays, UA rotation, and headers.
    
    Args:
        url: Target URL
        platform: Source platform ('hupu', 'dongqiudi', 'bilibili')
        **kwargs: Additional requests.get() parameters
    
    Returns:
        Response object
    
    Raises:
        RequestException: After 3 failed retry attempts
    """
    # Implementation details in Phase 1
```

### Data Preservation

**Decision**: Store both raw and cleaned versions of scraped content

**Rationale**:
- Raw data enables debugging and reprocessing
- Cleaned data is what AI processes
- Constitution requirement: "Raw data preservation separate from cleaned data"

**Schema**:
- `source_content` table with `raw_html` and `cleaned_text` columns
- Raw: Original HTML/JSON response from source
- Cleaned: Extracted text after removing HTML tags, ads, emojis, non-Chinese chars

### Content Deduplication

**Decision**: Use content fingerprinting (title + first 100 chars of body, SHA256 hash)

**Rationale**:
- Fast duplicate detection (hash comparison)
- Handles minor variations (whitespace, formatting)
- Low collision probability with SHA256

**Implementation Notes**:
- Create fingerprint before storing in database
- Check fingerprint against existing records
- Skip if duplicate found (log skip event)

## AI Processing Pipeline

### Relevance Filtering

**Decision**: Use Qwen-Turbo with 1-10 scoring prompt

**Prompt Strategy**:
- Few-shot examples (3 positive, 3 negative examples)
- Clear scoring rubric (7+ relevant, 4-6 borderline, ≤3 irrelevant)
- Structured JSON output: `{"score": 8, "reason": "..."}`

**Thresholds** (configurable):
- ≥7: Enter aggregation pool
- 4-6: Low priority queue
- ≤3: Discard

### Topic Clustering

**Decision**: Two-stage clustering (embedding + LLM refinement)

**Stage 1 - Embedding Clustering**:
- Use sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
- Compute embeddings for cleaned text
- Cosine similarity > 0.8 → candidate cluster
- Fast, catches obvious duplicates

**Stage 2 - LLM Refinement**:
- Use Qwen-Turbo to judge if candidates are truly same topic
- Prompt: "Are these two articles about the same event? Yes/No + reason"
- Handles nuanced cases (similar but different events)

**Time Window**: Only cluster content within 24 hours (older content archived)

### Card Generation

**Decision**: Use Qwen-Max for high-quality summaries

**Output Format**:
```json
{
  "title": "15字以内标题",
  "summary": "50字以内一句话摘要",
  "category": "转会传闻|球队动态|赛程赛制|球迷讨论",
  "sources": ["虎扑", "懂球帝"],
  "credibility": "可信|待确认|传闻"
}
```

**Prompt Strategy**:
- Emphasize brevity (title ≤15 chars, summary ≤50 chars)
- Require factual accuracy (no hallucinations)
- Include source attribution in prompt context

### Detail Generation

**Decision**: Use Qwen-Max for structured long-form content

**Output Format**:
```json
{
  "overview": "事件概述，100-200字",
  "viewpoints": [
    {"source": "虎扑用户", "view": "观点内容", "citation": "[1]"}
  ],
  "timeline": [
    {"time": "2026-04-08 10:00", "event": "事件描述", "citation": "[2]"}
  ],
  "sources": [
    {"id": 1, "platform": "虎扑", "title": "...", "url": "...", "time": "..."}
  ]
}
```

**Prompt Strategy**:
- Require inline citations for every factual claim
- Handle contradictions explicitly ("不同来源对此事件的描述存在差异")
- Maintain neutral tone, present multiple viewpoints

### Credibility Scoring

**Decision**: Multi-factor scoring algorithm

**Factors**:
1. Source authority (虎扑/懂球帝 > B站 > Bing)
2. Multi-source verification (2+ sources = higher credibility)
3. Content type (official announcement > user discussion)

**Scoring Logic**:
```python
def calculate_credibility(cluster: TopicCluster) -> str:
    authority_score = sum(SOURCE_WEIGHTS[s.platform] for s in cluster.sources)
    multi_source_bonus = 1.5 if len(cluster.sources) >= 2 else 1.0
    content_type_score = detect_content_type(cluster)
    
    total = authority_score * multi_source_bonus * content_type_score
    
    if total >= 8: return "可信"
    elif total >= 5: return "待确认"
    else: return "传闻"
```

## Source Health Monitoring

### Probe Strategy

**Decision**: HTTP HEAD requests every 5 minutes to check source availability

**Failure Handling**:
- 3 consecutive failures → Email alert to admin
- 5 consecutive failures → Auto-degrade to Bing Search API
- Recovery: Auto-restore when probe succeeds

**Email Configuration**:
- Use Python's smtplib for email sending
- Configure SMTP server, port, credentials in config.yaml
- Email template includes: source name, failure count, timestamp, recovery instructions

### Bing Search API Fallback

**Decision**: Use Bing Web Search API as backup source

**Implementation**:
- Trigger when primary sources unavailable
- Search with same keyword library
- Parse search results (title, snippet, URL)
- Mark all Bing-sourced content as "待确认" credibility
- Label as "搜索引擎聚合" in source attribution

## Real-Time Push Strategy

### Development Phase: Polling

**Decision**: Use client-side polling (30-second interval)

**Rationale**:
- Simplest implementation for MVP
- No WebSocket infrastructure needed
- Sufficient for 30-minute scraping cycle
- Easy to debug and monitor

**Implementation**:
- Frontend polls `/api/cards/new?since=<timestamp>` every 30s
- Backend returns new cards since last check
- Display notification bar if new cards found

### Future: WebSocket Upgrade

**Decision**: Upgrade to WebSocket after MVP validation

**Rationale**:
- More efficient for real-time updates
- Better user experience (instant notifications)
- Only add complexity after proving product value

## Configuration Management

### Configuration File: config.yaml

**Decision**: Use YAML for all tunable parameters

**Structure**:
```yaml
scraping:
  interval_minutes: 30
  keywords:
    - "2026世界杯"
    - "美加墨世界杯"
    # ... 30-50 keywords
  delays:
    hupu: 5
    dongqiudi: 3
    bilibili: 2

ai:
  provider: "aliyun"
  api_key: "${ALIYUN_API_KEY}"  # From environment variable
  daily_limit: 10000
  input_max_chars: 1500
  models:
    relevance: "qwen-turbo"
    clustering: "qwen-turbo"
    generation: "qwen-max"
    credibility: "qwen-max"

clustering:
  embedding_similarity_threshold: 0.8
  time_window_hours: 24

content:
  archive_after_hours: 72
  retention_days: 30
  hotness_threshold: 10

monitoring:
  probe_interval_minutes: 5
  failure_alert_threshold: 3
  degradation_threshold: 5
  admin_email: "${ADMIN_EMAIL}"

push:
  polling_interval_seconds: 30

dry_run:
  enabled: false  # Global dry-run toggle
```

**Environment Variables** (sensitive data):
- `ALIYUN_API_KEY`: Aliyun API key
- `ADMIN_EMAIL`: Admin email for alerts
- `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`: Email config

## Defensive Engineering Patterns

### LLM Output Parsing

**Pattern**: Always wrap JSON parsing in try-except

```python
def parse_llm_response(response: str, schema: Type[BaseModel]) -> Optional[BaseModel]:
    """
    Safely parse LLM JSON response with error handling.
    
    Args:
        response: Raw LLM response string
        schema: Pydantic model for validation
    
    Returns:
        Parsed model instance or None if parsing fails
    """
    try:
        data = json.loads(response)
        return schema(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        logger.error(f"LLM parse failed: {e}", extra={
            "response_sample": response[:200],
            "schema": schema.__name__
        })
        return None
```

### Input Truncation

**Pattern**: Truncate all LLM inputs to 1500 characters

```python
def truncate_input(text: str, max_chars: int = 1500) -> str:
    """Truncate text to max_chars, preserving word boundaries."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(' ', 1)[0] + "..."
```

### API Call Limiting

**Pattern**: Track daily API calls with hard limit

```python
class APICallLimiter:
    def __init__(self, daily_limit: int):
        self.daily_limit = daily_limit
        self.calls_today = 0
        self.reset_date = date.today()
    
    def check_and_increment(self) -> bool:
        """Returns True if call allowed, False if limit exceeded."""
        if date.today() > self.reset_date:
            self.calls_today = 0
            self.reset_date = date.today()
        
        if self.calls_today >= self.daily_limit:
            logger.error("Daily API limit exceeded", extra={
                "limit": self.daily_limit,
                "calls": self.calls_today
            })
            return False
        
        self.calls_today += 1
        return True
```

### Pipeline Logging

**Pattern**: Log input/output counts at each stage

```python
@log_pipeline_stage("scraping")
def scrape_sources() -> List[SourceContent]:
    """Scrape all sources and return raw content."""
    # Implementation
    pass

def log_pipeline_stage(stage_name: str):
    """Decorator to log pipeline stage execution."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.info(f"{stage_name} started")
            result = func(*args, **kwargs)
            logger.info(f"{stage_name} completed", extra={
                "stage": stage_name,
                "input_count": len(args[0]) if args else 0,
                "output_count": len(result) if result else 0
            })
            return result
        return wrapper
    return decorator
```

## Dry-Run Mode Implementation

### Global Toggle

**Decision**: Single boolean flag in config.yaml controls dry-run mode

**Behavior When Enabled**:
- Scraping layer: Returns mock scraped content (pre-defined test data)
- AI layer: Returns mock AI responses (pre-defined summaries, clusters)
- Database: Writes to separate `worldcup_dryrun.db` file
- API calls: No actual Aliyun API calls made
- Logging: All logs prefixed with `[DRY-RUN]`

**Mock Data**:
- 10 pre-defined source content items (varied topics, sources)
- 3 pre-defined topic clusters
- 5 pre-defined hot cards
- 2 pre-defined detail pages

**Use Cases**:
- Development without API costs
- Integration testing without external dependencies
- Demo/presentation mode

## Testing Strategy

### Unit Tests

**Coverage**:
- Text processing utilities (truncation, fingerprinting)
- Configuration loading
- Credibility scoring logic
- Mock data generation

**Framework**: pytest with fixtures

### Integration Tests

**Coverage**:
- End-to-end pipeline (scraping → AI → storage → API)
- Source health monitoring and degradation
- API endpoints (cards, details, health)

**Approach**: Use dry-run mode for deterministic testing

### Manual Testing

**Round 1 Validation**:
- After each of 6 specs, manually verify deliverable
- Collect bad cases during 2-3 day self-testing period

**Round 2 Refinement**:
- Test with real sources and API
- Validate AI output quality
- Check edge cases from bad case list

## Deployment Considerations

### Single Server Setup

**Requirements**:
- Linux VPS (Ubuntu 22.04 recommended)
- 4GB RAM minimum (for in-memory caching + AI processing)
- 20GB disk space (database + logs)
- Python 3.11+ installed
- Nginx for reverse proxy (frontend static files + backend API)

**Process Management**:
- Use systemd for backend service
- Nginx serves frontend build + proxies API requests
- APScheduler runs within backend process (no separate daemon)

### Environment Setup

**Steps**:
1. Clone repository
2. Create virtual environment: `python -m venv venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Configure environment variables in `.env`
5. Initialize database: `python -m src.core.database init`
6. Start backend: `uvicorn src.main:app --host 0.0.0.0 --port 8000`
7. Build frontend: `npm run build`
8. Configure Nginx to serve frontend + proxy backend

## Next Steps

Phase 1 will produce:
1. **data-model.md**: Detailed database schema for all entities
2. **contracts/**: API endpoint specifications and data schemas
3. **quickstart.md**: Step-by-step development setup guide

These artifacts will provide the foundation for Phase 2 task breakdown.
