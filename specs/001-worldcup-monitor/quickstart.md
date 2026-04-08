# Quickstart Guide: 世界杯热点监控助手

**Feature**: 001-worldcup-monitor  
**Date**: 2026-04-08  
**Target Audience**: Developers setting up local development environment

## Overview

This guide walks you through setting up the World Cup Hot Topics Monitor development environment from scratch. Follow these steps to get the backend and frontend running locally.

## Prerequisites

### Required Software

- **Python 3.11+**: Backend runtime
- **Node.js 18+**: Frontend build tools
- **Git**: Version control
- **Code Editor**: VS Code recommended

### System Requirements

- **OS**: Linux, macOS, or Windows (with WSL2)
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: 2GB free space

### External Services

- **Aliyun Account**: For Qwen API access
  - Sign up at https://www.aliyun.com/
  - Enable DashScope API
  - Generate API key

- **Email Account**: For admin alerts (SMTP)
  - Gmail, Outlook, or any SMTP server
  - Enable "less secure apps" or app-specific password

## Quick Start (5 Minutes)

### 1. Clone Repository

```bash
git clone <repository-url>
cd worldcup-monitor
git checkout 001-worldcup-monitor
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env with your API keys (see Configuration section)

# Initialize database
python -m src.core.database init

# Start backend server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Backend should now be running at http://localhost:8000

### 3. Frontend Setup

```bash
# Open new terminal
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend should now be running at http://localhost:5173

### 4. Verify Setup

Open http://localhost:5173 in your browser. You should see the discovery page (empty initially).

## Detailed Setup

### Backend Configuration

#### Environment Variables (.env)

Create `backend/.env` file with the following:

```bash
# Aliyun API Configuration
ALIYUN_API_KEY=your_aliyun_api_key_here
ALIYUN_API_ENDPOINT=https://dashscope.aliyuncs.com/api/v1

# Email Configuration (for admin alerts)
ADMIN_EMAIL=your_email@example.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_specific_password

# Application Configuration
DEBUG=true
DRY_RUN=false  # Set to true for development without API calls
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite:///data/worldcup.db
```

#### Configuration File (config.yaml)

The `backend/config.yaml` file contains all tunable parameters. Default values are provided, but you can customize:

```yaml
scraping:
  interval_minutes: 30  # How often to scrape sources
  keywords:
    - "2026世界杯"
    - "美加墨世界杯"
    - "世界杯预选赛"
    # Add more keywords as needed (30-50 total)
  delays:
    hupu: 5      # Seconds between requests to 虎扑
    dongqiudi: 3 # Seconds between requests to 懂球帝
    bilibili: 2  # Seconds between requests to B站

ai:
  provider: "aliyun"
  daily_limit: 10000  # Max API calls per day
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

push:
  polling_interval_seconds: 30

dry_run:
  enabled: false  # Set to true to use mock data
```

### Database Initialization

The database is automatically created on first run, but you can manually initialize:

```bash
cd backend
python -m src.core.database init
```

This creates:
- `data/worldcup.db` - SQLite database file
- All tables defined in data-model.md
- Initial source health records

To reset database (WARNING: deletes all data):

```bash
python -m src.core.database reset
```

### Prompt Templates

Create prompt template files in `backend/prompts/`:

**prompts/relevance_filter.txt**:
```
你是一个内容相关性评分专家。请评估以下内容与"2026世界杯"的相关性。

评分标准：
- 10分：直接讨论2026世界杯赛事、球队、球员
- 7-9分：与2026世界杯相关的预选赛、备战、转会
- 4-6分：足球相关但不特定于2026世界杯
- 1-3分：与足球或世界杯无关

内容：
{content}

请以JSON格式返回：
{
  "score": <1-10的整数>,
  "reason": "<评分理由，10-50字>"
}
```

**prompts/topic_clustering.txt**:
```
你是一个话题聚类专家。请判断以下两篇文章是否讨论同一个话题/事件。

文章1：
{content1}

文章2：
{content2}

请以JSON格式返回：
{
  "same_topic": <true或false>,
  "reason": "<判断理由，10-50字>"
}
```

**prompts/card_generation.txt**:
```
你是一个新闻编辑。请为以下话题生成一张热点卡片。

要求：
- 标题：15个汉字以内，简洁有力
- 摘要：50个汉字以内，一句话概括核心信息
- 分类：从"转会传闻"、"球队动态"、"赛程赛制"、"球迷讨论"中选择最合适的

来源内容：
{sources}

请以JSON格式返回：
{
  "title": "<标题>",
  "summary": "<摘要>",
  "category": "<分类>"
}
```

**prompts/detail_generation.txt**:
```
你是一个深度报道编辑。请为以下话题生成详细内容。

要求：
- 事件概述：100-200字，客观描述事件全貌
- 各方观点：列出不同来源的观点，每个观点标注引用[1][2]等
- 时间线：按时间顺序列出关键事件，标注引用
- 严格基于提供的来源，不添加未提及的事实
- 如有矛盾，明确指出"不同来源对此事件的描述存在差异"

来源内容：
{sources}

请以JSON格式返回：
{
  "overview": "<事件概述>",
  "viewpoints": [
    {"source": "<来源>", "view": "<观点>", "citation": "[1]"}
  ],
  "timeline": [
    {"time": "YYYY-MM-DD HH:MM", "event": "<事件>", "citation": "[1]"}
  ]
}
```

**prompts/credibility_scoring.txt**:
```
你是一个信息可信度评估专家。请评估以下话题的可信度。

评估因素：
- 信源权威性（官方 > 媒体 > 用户讨论）
- 多源验证（多个独立来源 > 单一来源）
- 内容类型（官方公告 > 新闻报道 > 传闻讨论）

可信度等级：
- "可信"：多个权威来源交叉验证，或官方声明
- "待确认"：单一来源，或来源权威性一般
- "传闻"：仅用户讨论，无权威来源支持

话题信息：
来源数量：{source_count}
来源平台：{platforms}
内容摘要：{summary}

请以JSON格式返回：
{
  "credibility": "<可信|待确认|传闻>",
  "reason": "<评估理由，10-50字>"
}
```

### Running the Pipeline

The scraping pipeline runs automatically every 30 minutes (configurable). To manually trigger:

```bash
cd backend
python -m src.services.pipeline run
```

To run in dry-run mode (uses mock data, no API calls):

```bash
# Set DRY_RUN=true in .env, then:
python -m src.services.pipeline run
```

### Frontend Configuration

The frontend automatically connects to `http://localhost:8000` in development. To change the API endpoint, edit `frontend/src/services/api.ts`:

```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

## Development Workflow

### Two-Round Development Strategy

**Round 1: Build End-to-End Pipeline (6 Specs)**

Each spec is a vertical slice that adds one capability:

1. **Spec 1 - Minimal Pipeline**: 虎扑单源 + 原始列表
   - Implement: Scraper, database, basic API, simple list UI
   - Verify: Can see raw 虎扑 posts

2. **Spec 2 - AI Integration**: 相关性过滤 + 卡片生成
   - Implement: AI client, relevance filtering, card generation
   - Verify: Discovery feed shows AI-generated cards

3. **Spec 3 - Clustering**: 话题合并
   - Implement: Embedding clustering, LLM refinement
   - Verify: Multiple posts merge into one card

4. **Spec 4 - Detail Pages**: 结构化详情
   - Implement: Detail generation, inline citations
   - Verify: Click card → see detailed content

5. **Spec 5 - Multi-Source**: 懂球帝 + B站 + 降级
   - Implement: Additional scrapers, health monitoring
   - Verify: Multiple sources, automatic fallback

6. **Spec 6 - Polish**: 推送 + 视觉
   - Implement: Polling, images, channel filters
   - Verify: Real-time updates, polished UI

**After Spec 6**: Self-test for 2-3 days, collect bad cases

**Round 2: Quality Refinement**

Fix bad cases by priority:
1. AI generation quality (prompt tuning)
2. Filtering/clustering accuracy (threshold tuning)
3. Source richness (more keywords)
4. Visual polish (UI improvements)

### Git Workflow

```bash
# After completing each spec
git add .
git commit -m "feat: implement spec N - <description>

- <what was accomplished>
- <key changes>
- <verification results>"

# Push to remote
git push origin 001-worldcup-monitor
```

### Testing

**Unit Tests**:
```bash
cd backend
pytest tests/unit/
```

**Integration Tests**:
```bash
pytest tests/integration/
```

**Manual Testing Checklist**:
- [ ] Backend health check: http://localhost:8000/api/health
- [ ] Get cards: http://localhost:8000/api/cards
- [ ] Frontend loads: http://localhost:5173
- [ ] Cards display in feed
- [ ] Click card → detail page loads
- [ ] Channel filters work
- [ ] New card notifications appear

## Troubleshooting

### Backend Issues

**Problem**: `ModuleNotFoundError: No module named 'src'`
**Solution**: Ensure you're in the `backend/` directory and virtual environment is activated

**Problem**: `sqlite3.OperationalError: unable to open database file`
**Solution**: Create `data/` directory: `mkdir -p data`

**Problem**: `AliyunAPIError: Invalid API key`
**Solution**: Check `ALIYUN_API_KEY` in `.env` file

**Problem**: Pipeline not running automatically
**Solution**: Check APScheduler logs, ensure `uvicorn` is running with `--reload` flag

### Frontend Issues

**Problem**: `CORS error` when calling API
**Solution**: Ensure backend CORS is configured for `http://localhost:5173`

**Problem**: Cards not loading
**Solution**: Check browser console for errors, verify backend is running

**Problem**: Images not displaying
**Solution**: Check image URLs in database, verify proxy/CORS settings

### Common Errors

**Error**: `Daily API limit exceeded`
**Solution**: Check `api_call_log` table, increase limit in config.yaml, or wait until next day

**Error**: `Source health degraded`
**Solution**: Check `source_health` table, verify source websites are accessible

**Error**: `LLM parse failed`
**Solution**: Check logs for parse errors, review prompt templates, verify AI response format

## Development Tools

### Recommended VS Code Extensions

- Python (Microsoft)
- Pylance (Microsoft)
- ESLint (Microsoft)
- Prettier (Prettier)
- SQLite Viewer (alexcvzz)
- REST Client (Huachao Mao)

### Useful Commands

**View database**:
```bash
sqlite3 data/worldcup.db
.tables
.schema source_content
SELECT * FROM hot_card LIMIT 5;
```

**Check API usage**:
```bash
curl http://localhost:8000/api/health | jq '.data.api_usage'
```

**Monitor logs**:
```bash
tail -f data/logs/app.log
```

**Clear cache**:
```bash
# Restart backend to clear in-memory cache
# Or implement cache clear endpoint
```

## Next Steps

1. Complete Round 1 (6 specs) following the development strategy
2. Self-test for 2-3 days, document bad cases
3. Prioritize and fix bad cases in Round 2
4. Deploy to production server (see deployment guide)

## Additional Resources

- **API Documentation**: http://localhost:8000/docs (FastAPI auto-generated)
- **Data Model**: See `data-model.md`
- **API Contracts**: See `contracts/api-endpoints.md`
- **Constitution**: See `.specify/memory/constitution.md`

## Getting Help

If you encounter issues not covered in this guide:

1. Check logs in `data/logs/`
2. Review error messages carefully
3. Consult the research.md document for technical decisions
4. Check the constitution for architectural constraints

Happy coding! 🚀⚽
