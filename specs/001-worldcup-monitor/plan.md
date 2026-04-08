# Implementation Plan: 世界杯热点监控助手

**Branch**: `001-worldcup-monitor` | **Date**: 2026-04-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-worldcup-monitor/spec.md`

**Note**: This plan follows a two-round development strategy: Round 1 builds a working end-to-end pipeline through 6 incremental specs (vertical slices), Round 2 refines quality based on real usage feedback.

## Summary

Build an AI-powered editorial platform that monitors Chinese football communities (虎扑, 懂球帝, B站) for 2026 World Cup pre-tournament news. The system automatically scrapes content every 30 minutes, uses AI to filter/cluster/summarize into curated "hot topic cards" with credibility labels and source attribution. Users browse a discovery feed (inspired by Perplexity Discover) with mixed card layouts, click for detailed AI-generated content with inline citations, and receive real-time notifications for new topics.

**Technical Approach**: Python/FastAPI backend with React/TailwindCSS frontend, SQLite database, APScheduler for scheduling, Aliyun Qwen API for AI processing. Four-layer architecture: Data Scraping → AI Processing → Content Display → Real-time Push. All constitution principles enforced (prompt separation, defensive parsing, configuration externalization, dry-run mode).

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI (web framework), APScheduler (task scheduling), Aliyun SDK (Qwen API), BeautifulSoup4/lxml (scraping), sentence-transformers (embeddings for clustering)  
**Storage**: SQLite (MVP database), in-memory dict (caching)  
**Testing**: pytest (unit/integration tests), mock data for dry-run mode  
**Target Platform**: Linux server (single VPS deployment)  
**Project Type**: Web service (backend API + frontend SPA)  
**Performance Goals**: 3s page load for 10+ cards, 1s detail page load, 30s notification latency, 30min scraping cycle  
**Constraints**: Single server deployment, local LLM inference not used (Aliyun API instead), 1500 char LLM input limit, daily API call hard limit  
**Scale/Scope**: MVP for personal/small group use, ~100 hot topics active at any time, 3 primary sources + 1 backup

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Principle I - Product Positioning**: Does this feature maintain AI editorial curation (not raw content forwarding)?
- [x] Verified: Feature processes/curates content through AI filtering, clustering, and summarization - never displays raw scraped content

**Principle II - Data Honesty**: Does this feature require source attribution and credibility classification?
- [x] Verified: All factual claims traceable to sources via inline citations in detail pages
- [x] Verified: Credibility labels (可信/待确认/传闻) implemented for all cards based on multi-source verification

**Principle III - Defensive Engineering**: Are protective measures in place?
- [x] Verified: All LLM parsing wrapped in try-except (see architecture constraints)
- [x] Verified: Input truncation implemented (1500 char limit specified)
- [x] Verified: API call counter with hard limits implemented (daily quota tracking)
- [x] Verified: Pipeline stage logging added (input/output counts at each layer)

**Principle IV - Configuration Externalization**: Are parameters externalized?
- [x] Verified: No hardcoded thresholds, intervals, or limits (config.yaml for all tunable params)
- [x] Verified: All tunable values in config files (scraping intervals, thresholds, API limits, similarity scores)

**Principle V - Prompt-Code Separation**: Are prompts externalized?
- [x] Verified: All prompts in `prompts/` directory (5 prompt templates specified)
- [x] Verified: No hardcoded prompts in code (runtime file loading required)

**Principle VI - Crawler Standards**: Does scraping follow standards?
- [x] Verified: Unified request function used (封装统一请求函数 specified)
- [x] Verified: Platform-specific delays implemented (虎扑5秒、懂球帝3秒、B站2秒)
- [x] Verified: UA rotation and browser headers configured (UA轮换、Headers伪装)
- [x] Verified: Raw data preservation separate from cleaned data (raw + cleaned 两份存储)

**Principle VII - Testability**: Is dry-run mode supported?
- [x] Verified: Dry-run toggle implemented (全局开关 specified)
- [x] Verified: Mock data available for AI processing layers (AI层用mock数据)

**Principle VIII - MVP Mindset**: Are technology choices justified?
- [x] Verified: SQLite used (explicitly specified, no PostgreSQL)
- [x] Verified: APScheduler used (explicitly specified, no Celery)
- [x] Verified: Simple caching used (in-memory dict, no Redis)
- [x] Verified: Complexity justified (Aliyun API chosen over local LLM for reliability)

**Principle IX - Git Discipline**: Is commit strategy clear?
- [x] Verified: Atomic commit plan defined (6-spec incremental development with commits per spec)
- [x] Verified: Commit message format established (follows constitution guidelines)

**Constitution Check Result**: ✅ PASSED - All principles verified

## Project Structure

### Documentation (this feature)

```text
specs/001-worldcup-monitor/
├── plan.md              # This file
├── research.md          # Phase 0: Technology research and decisions
├── data-model.md        # Phase 1: Database schema and entities
├── quickstart.md        # Phase 1: Development setup guide
├── contracts/           # Phase 1: API contracts
│   ├── api-endpoints.md # REST API specification
│   └── data-schemas.md  # Request/response schemas
└── tasks.md             # Phase 2: Task breakdown (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/                    # FastAPI routes
│   │   ├── __init__.py
│   │   ├── cards.py           # Hot topic cards endpoints
│   │   ├── details.py         # Detail page endpoints
│   │   └── health.py          # Health check endpoints
│   ├── scrapers/              # Data scraping layer
│   │   ├── __init__.py
│   │   ├── base.py            # Unified request function
│   │   ├── hupu.py            # 虎扑 scraper
│   │   ├── dongqiudi.py       # 懂球帝 scraper
│   │   ├── bilibili.py        # B站 scraper
│   │   └── bing_fallback.py   # Bing Search API fallback
│   ├── ai/                    # AI processing layer
│   │   ├── __init__.py
│   │   ├── client.py          # Aliyun Qwen API client
│   │   ├── relevance.py       # Relevance filtering
│   │   ├── clustering.py      # Topic clustering
│   │   ├── generation.py      # Card/detail generation
│   │   └── credibility.py     # Credibility scoring
│   ├── models/                # Database models
│   │   ├── __init__.py
│   │   ├── source_content.py  # Raw/cleaned content
│   │   ├── topic_cluster.py   # Topic clusters
│   │   ├── hot_card.py        # Hot topic cards
│   │   └── health_status.py   # Source health monitoring
│   ├── services/              # Business logic
│   │   ├── __init__.py
│   │   ├── pipeline.py        # Main pipeline orchestration
│   │   ├── monitoring.py      # Source health monitoring
│   │   └── notification.py    # Push notification service
│   ├── core/                  # Core utilities
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration loader
│   │   ├── database.py        # SQLite connection
│   │   ├── logging.py         # Structured logging
│   │   └── scheduler.py       # APScheduler setup
│   ├── utils/                 # Helper utilities
│   │   ├── __init__.py
│   │   ├── text.py            # Text processing
│   │   ├── hash.py            # Content fingerprinting
│   │   └── mock.py            # Dry-run mock data
│   └── main.py                # FastAPI application entry
├── tests/
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── fixtures/              # Test fixtures
├── prompts/                   # Prompt templates (constitution requirement)
│   ├── relevance_filter.txt
│   ├── topic_clustering.txt
│   ├── card_generation.txt
│   ├── detail_generation.txt
│   └── credibility_scoring.txt
├── config.yaml                # Configuration file
├── requirements.txt           # Python dependencies
└── README.md                  # Backend documentation

frontend/
├── src/
│   ├── components/            # React components
│   │   ├── CardFeed.tsx      # Card feed display
│   │   ├── HotCard.tsx       # Individual card component
│   │   ├── DetailPage.tsx    # Detail page
│   │   ├── ChannelTabs.tsx   # Channel filter tabs
│   │   └── Notification.tsx  # New topics notification bar
│   ├── pages/                 # Page components
│   │   ├── Discover.tsx      # Main discovery page
│   │   └── Detail.tsx        # Detail page route
│   ├── services/              # API clients
│   │   ├── api.ts            # API client
│   │   └── polling.ts        # Polling service
│   ├── types/                 # TypeScript types
│   │   └── index.ts          # Type definitions
│   ├── App.tsx               # Root component
│   └── main.tsx              # Entry point
├── public/                    # Static assets
│   └── theme-images/         # Theme image library
├── package.json
└── README.md

data/                          # SQLite database and logs
├── worldcup.db               # SQLite database file
└── logs/                     # Application logs
```

**Structure Decision**: Web application structure (Option 2) selected. Backend and frontend are separate projects to enable independent development and deployment. Backend uses layered architecture (API → Services → Models) aligned with the four-layer pipeline (Scraping → AI → Display → Push). Prompts directory at backend root per constitution requirement.

## Complexity Tracking

No constitution violations - all complexity justified and aligned with MVP principles.

## Development Strategy: Two-Round Approach

### Round 1: End-to-End Pipeline (6 Vertical Specs)

Goal: Build working pipeline quickly, validate each layer incrementally. Each spec is a vertical slice that adds one capability to the full stack.

**Spec 1 - Minimal Pipeline**: 虎扑单源 + 单关键词 + 原始列表展示
- Verify: Scraping → Storage → Display works end-to-end
- Deliverable: Can see raw 虎扑 posts in a simple list

**Spec 2 - AI Integration**: 相关性过滤 + 摘要生成 + 卡片流
- Verify: AI processing replaces raw content with curated cards
- Deliverable: Discovery feed shows AI-generated card summaries

**Spec 3 - Clustering**: 话题合并 + 聚合卡片
- Verify: Multiple posts about same topic merge into one card
- Deliverable: Cards represent topics, not individual posts

**Spec 4 - Detail Pages**: 结构化长文 + 内联引用 + 可信度
- Verify: Click card → see detailed AI content with sources
- Deliverable: Full detail page with citations and credibility labels

**Spec 5 - Multi-Source + Fallback**: 懂球帝 + B站 + 健康监控 + Bing兜底
- Verify: Multiple sources enrich content, system survives source failures
- Deliverable: Robust multi-source pipeline with automatic degradation

**Spec 6 - Polish + Push**: 轮询推送 + 图片策略 + 大小卡片 + 频道筛选 + 视觉对标Perplexity
- Verify: Real-time updates, visual polish, channel filtering
- Deliverable: Production-ready MVP matching design vision

**Timeline**: 2-3 days self-testing after Spec 6 to collect bad cases

### Round 2: Quality Refinement (Priority-Driven)

Goal: Fix bad cases discovered during self-testing, prioritized by impact.

**Priority Order**:
1. AI生成质量 (prompt tuning, few-shot examples)
2. 过滤聚类准确性 (threshold tuning, edge case handling)
3. 信源丰富度 (add more keywords, improve scraping robustness)
4. 视觉交互 (UI polish, responsive design, loading states)

**Approach**: Iterative refinement based on actual usage data, not speculation.
