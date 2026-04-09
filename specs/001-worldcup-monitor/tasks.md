# Tasks: 世界杯热点监控助手

**Input**: Design documents from `/specs/001-worldcup-monitor/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL - not included in this task breakdown as they were not explicitly requested in the feature specification.

**Organization**: Tasks are organized by the 6-spec incremental development strategy (vertical slices), where each spec builds one complete capability end-to-end.

## Format: `[ID] [P?] [Spec] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Spec]**: Which spec this task belongs to (Spec1-6)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`
- **Config**: `backend/config.yaml`, `backend/.env`, `backend/prompts/`

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Initialize project structure and basic configuration

- [X] T001 Create backend directory structure (src/, tests/, prompts/, data/)
- [X] T002 Create frontend directory structure (src/, public/)
- [X] T003 [P] Initialize Python project with requirements.txt (FastAPI, SQLAlchemy, APScheduler, aliyun-python-sdk, beautifulsoup4, sentence-transformers, pytest)
- [X] T004 [P] Initialize React project with package.json (React, TailwindCSS, axios, react-router-dom)
- [X] T005 [P] Create backend/.env.example with environment variable templates
- [X] T006 [P] Create backend/config.yaml with default configuration values
- [X] T006a [P] Populate backend/config.yaml with 30-50 World Cup keywords (2026世界杯, 美加墨世界杯, 世界杯预选赛, 国际足联, 世界杯扩军, 世界杯分组, etc.)
- [X] T007 [P] Create backend/README.md with project overview
- [X] T008 [P] Create frontend/README.md with setup instructions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY spec can be implemented

**⚠️ CRITICAL**: No spec work can begin until this phase is complete

### Constitution-Driven Infrastructure

- [X] T009 [P] Create backend/src/core/config.py to load config.yaml and environment variables
- [X] T010 [P] Create backend/src/core/logging.py with structured logging (ISO 8601 timestamps, JSON context)
- [X] T011 [P] Create backend/src/core/database.py with SQLAlchemy engine and session management (WAL mode enabled)
- [X] T012 [P] Create backend/src/utils/text.py with truncate_input() function (1500 char limit)
- [X] T013 [P] Create backend/src/utils/hash.py with content fingerprinting (SHA256)
- [X] T014 [P] Create backend/src/utils/mock.py with dry-run mock data generator
- [X] T015 Create backend/src/scrapers/base.py with unified_request() function (delays, UA rotation, headers)
- [X] T016 Create backend/src/ai/client.py with Aliyun Qwen API client wrapper (try-except parsing, exponential backoff)
- [X] T017 Create backend/src/core/scheduler.py with APScheduler setup (BackgroundScheduler, SQLite job store)
- [X] T018 [P] Create all 5 prompt templates in backend/prompts/ (relevance_filter.txt, topic_clustering.txt, card_generation.txt, detail_generation.txt, credibility_scoring.txt)

### Database Models (All Entities)

- [X] T019 [P] Create backend/src/models/source_content.py with SourceContent model
- [X] T020 [P] Create backend/src/models/topic_cluster.py with TopicCluster model
- [X] T021 [P] Create backend/src/models/hot_card.py with HotCard model
- [X] T022 [P] Create backend/src/models/detail_page.py with DetailPage model
- [X] T023 [P] Create backend/src/models/health_status.py with SourceHealth model
- [X] T024 [P] Create backend/src/models/api_call_log.py with APICallLog model
- [X] T025 Create backend/src/core/database.py init_db() function to create all tables and indexes

**Checkpoint**: Foundation ready - spec implementation can now begin

---

## Phase 3: Spec 1 - Minimal Pipeline (虎扑单源 + 原始列表)

**Goal**: Verify scraping → storage → display works end-to-end

**Independent Test**: Can see raw 虎扑 posts in a simple list on frontend

### Backend - Scraping & Storage

- [X] T026 [Spec1] Implement backend/src/scrapers/hupu.py to scrape 虎扑 hot posts (top 20, single keyword "2026世界杯")
- [X] T027 [Spec1] Implement backend/src/services/pipeline.py with scrape_and_store() function (scrape → clean → fingerprint → store)
- [X] T028 [Spec1] Add text cleaning logic in backend/src/utils/text.py (remove HTML, ads, emojis, non-Chinese)

### Backend - API

- [X] T029 [P] [Spec1] Create backend/src/api/cards.py with GET /api/cards endpoint (return raw SourceContent as simple list)
- [X] T030 [P] [Spec1] Create backend/src/api/health.py with GET /api/health endpoint
- [X] T031 [Spec1] Create backend/src/main.py FastAPI application with CORS configuration

### Frontend - Basic Display

- [X] T032 [P] [Spec1] Create frontend/src/services/api.ts with API client (axios)
- [X] T033 [P] [Spec1] Create frontend/src/components/RawList.tsx to display raw content list
- [X] T034 [Spec1] Create frontend/src/pages/Discover.tsx with basic layout
- [X] T035 [Spec1] Create frontend/src/App.tsx with routing setup

### Integration

- [X] T036 [Spec1] Configure APScheduler in backend/src/main.py to run scraping every 30 minutes
- [X] T037 [Spec1] Test end-to-end: Run scraper → verify data in SQLite → verify frontend displays list

**Checkpoint**: Spec 1 complete - can see raw 虎扑 posts in browser

---

## Phase 4: Spec 2 - AI Integration (相关性过滤 + 卡片生成)

**Goal**: AI processing replaces raw content with curated cards

**Independent Test**: Discovery feed shows AI-generated card summaries instead of raw posts

### Backend - AI Processing

- [X] T038 [Spec2] Implement backend/src/ai/relevance.py with filter_relevance() function (calls Qwen-Turbo, parses score)
- [X] T039 [Spec2] Implement backend/src/ai/generation.py with generate_card() function (calls Qwen-Max, generates title/summary/category)
- [X] T040 [Spec2] Implement backend/src/ai/credibility.py with calculate_credibility() function (multi-factor scoring)
- [X] T041 [Spec2] Update backend/src/services/pipeline.py to add AI filtering and card generation steps
- [X] T042 [Spec2] Implement API call limiter in backend/src/ai/client.py (daily counter, hard limit check)

### Backend - API Updates

- [X] T043 [Spec2] Update backend/src/api/cards.py GET /api/cards to return HotCard objects instead of raw content
- [X] T044 [Spec2] Add GET /api/categories endpoint in backend/src/api/cards.py

### Frontend - Card Display

- [X] T045 [P] [Spec2] Create frontend/src/components/HotCard.tsx component (title, summary, sources, credibility badge)
- [X] T046 [P] [Spec2] Create frontend/src/components/CardFeed.tsx component (grid layout for cards)
- [X] T047 [Spec2] Update frontend/src/pages/Discover.tsx to use CardFeed instead of RawList
- [X] T048 [Spec2] Add TailwindCSS styling for cards (responsive design)

### Integration

- [X] T049 [Spec2] Test AI pipeline: Scrape → Filter (score ≥7) → Generate cards → Display in feed
- [X] T050 [Spec2] Verify API call counter increments and respects daily limit

**Checkpoint**: Spec 2 complete - discovery feed shows AI-generated cards

---

## Phase 5: Spec 3 - Clustering (话题合并)

**Goal**: Multiple posts about same topic merge into one card

**Independent Test**: Cards represent topics (multiple sources), not individual posts

### Backend - Clustering

- [X] T051 [Spec3] Implement backend/src/ai/clustering.py with compute_embeddings() function (sentence-transformers)
- [X] T052 [Spec3] Implement backend/src/ai/clustering.py with cluster_by_similarity() function (cosine similarity > 0.8)
- [X] T053 [Spec3] Implement backend/src/ai/clustering.py with refine_with_llm() function (Qwen-Turbo judges same topic)
- [X] T054 [Spec3] Update backend/src/services/pipeline.py to add clustering step (create TopicCluster, link SourceContent)
- [X] T055 [Spec3] Update backend/src/ai/generation.py generate_card() to accept multiple sources (cluster)

### Frontend - Multi-Source Display

- [X] T056 [Spec3] Update frontend/src/components/HotCard.tsx to display multiple source labels
- [X] T057 [Spec3] Add source count badge to cards

### Integration

- [X] T058 [Spec3] Test clustering: Scrape similar posts → Cluster → Generate single card with multiple sources
- [X] T059 [Spec3] Verify single-source topics marked as "待确认" credibility

**Checkpoint**: Spec 3 complete - cards aggregate multiple sources

---

## Phase 6: Spec 4 - Detail Pages (结构化详情 + 引用)

**Goal**: Click card → see detailed AI content with inline citations

**Independent Test**: Detail page shows structured content (overview + viewpoints + timeline) with clickable citations

### Backend - Detail Generation

- [X] T060 [Spec4] Implement backend/src/ai/generation.py with generate_detail() function (structured JSON: overview, viewpoints, timeline)
- [X] T061 [Spec4] Add detail page caching logic in backend/src/services/pipeline.py (1 hour TTL)
- [X] T062 [Spec4] Create backend/src/api/details.py with GET /api/cards/{id}/detail endpoint

### Frontend - Detail Page

- [X] T063 [P] [Spec4] Create frontend/src/components/DetailPage.tsx component (overview, viewpoints, timeline sections)
- [X] T064 [P] [Spec4] Create frontend/src/components/SourceCard.tsx component (horizontal source list at bottom)
- [X] T065 [P] [Spec4] Create frontend/src/components/Citation.tsx component (clickable inline citation tags)
- [X] T066 [Spec4] Create frontend/src/pages/Detail.tsx route
- [X] T067 [Spec4] Update frontend/src/components/HotCard.tsx to link to detail page on click
- [X] T068 [Spec4] Implement citation click handler (scroll to source or show tooltip)

### Integration

- [X] T069 [Spec4] Test detail generation: Click card → Generate detail (if not cached) → Display structured content
- [X] T070 [Spec4] Verify all citations link to correct sources
- [X] T071 [Spec4] Verify contradictions are explicitly noted in generated content

**Checkpoint**: Spec 4 complete - full detail pages with source attribution

---

## Phase 7: Spec 5 - Multi-Source + Fallback (懂球帝 + B站 + 降级)

**Goal**: Multiple sources enrich content, system survives source failures

**Independent Test**: System continues working when one source fails, automatically uses Bing fallback

### Backend - Additional Scrapers

- [X] T072 [P] [Spec5] Implement backend/src/scrapers/dongqiudi.py (scrape articles and posts, top 20)
- [X] T073 [P] [Spec5] Implement backend/src/scrapers/bilibili.py (search videos/dynamics, top 10)
- [X] T074 [P] [Spec5] Implement backend/src/scrapers/bing_fallback.py (Bing Search API integration)
- [X] T075 [Spec5] Update backend/src/services/pipeline.py to scrape all sources in parallel

### Backend - Health Monitoring

- [X] T076 [Spec5] Implement backend/src/services/monitoring.py with probe_source_health() function (HTTP HEAD requests)
- [X] T077 [Spec5] Implement backend/src/services/monitoring.py with send_alert_email() function (SMTP)
- [X] T078 [Spec5] Implement backend/src/services/monitoring.py with handle_degradation() function (switch to Bing after 5 failures)
- [X] T079 [Spec5] Add health monitoring scheduler job in backend/src/main.py (every 5 minutes)
- [X] T080 [Spec5] Create backend/src/api/health.py GET /api/sources/health endpoint

### Frontend - Health Status

- [X] T081 [Spec5] Create frontend/src/components/SourceStatus.tsx component (optional admin view)

### Integration

- [X] T082 [Spec5] Test multi-source scraping: All 3 sources → Cluster across sources → Richer cards
- [X] T083 [Spec5] Test degradation: Simulate 虎扑 failure → Alert sent → Bing fallback activated
- [X] T084 [Spec5] Verify Bing-sourced content marked "待确认" and labeled "搜索引擎聚合"

**Checkpoint**: Spec 5 complete - robust multi-source pipeline with automatic fallback

---

## Phase 8: Spec 6 - Polish + Push (推送 + 图片 + 视觉)

**Goal**: Real-time updates, visual polish, channel filtering - production-ready MVP

**Independent Test**: New cards appear via notification, images load, channel filters work, UI matches Perplexity style

### Backend - Real-Time Push

- [X] T085 [Spec6] Implement backend/src/services/notification.py with get_new_cards() function (since timestamp)
- [X] T086 [Spec6] Add GET /api/cards/new endpoint in backend/src/api/cards.py

### Backend - Image Handling

- [X] T087 [P] [Spec6] Implement backend/src/utils/images.py with proxy_image() function (cache original images)
- [X] T088 [P] [Spec6] Implement backend/src/utils/images.py with match_theme_image() function (theme library lookup)
- [X] T089 [Spec6] Update backend/src/ai/generation.py generate_card() to select image (original > theme > null)

### Frontend - Polling & Notifications

- [X] T090 [Spec6] Create frontend/src/services/polling.ts with polling service (30-second interval)
- [X] T091 [Spec6] Create frontend/src/components/Notification.tsx component (notification bar at top)
- [X] T092 [Spec6] Update frontend/src/pages/Discover.tsx to integrate polling and notifications

### Frontend - Visual Polish

- [X] T093 [P] [Spec6] Create frontend/src/components/ChannelTabs.tsx component (全部/热门/转会传闻/球队动态/赛程赛制/球迷讨论)
- [X] T094 [P] [Spec6] Update frontend/src/components/CardFeed.tsx to support mixed layout (3 large cards + small cards grid)
- [X] T095 [P] [Spec6] Add image loading states and error handling in frontend/src/components/HotCard.tsx
- [X] T096 [P] [Spec6] Implement responsive design (mobile + desktop) across all components
- [X] T097 [Spec6] Add TailwindCSS styling to match Perplexity Discover aesthetic (clean, modern, card shadows)
- [X] T098 [Spec6] Implement infinite scroll in frontend/src/pages/Discover.tsx

### Integration

- [X] T099 [Spec6] Test polling: Generate new card → Frontend polls → Notification appears → Click loads new cards
- [X] T100 [Spec6] Test channel filtering: Click "转会传闻" → Only transfer rumor cards displayed
- [X] T101 [Spec6] Test image strategy: Cards with images display properly, fallback to theme images or no-image layout
- [X] T102 [Spec6] Test responsive design: Verify mobile and desktop layouts
- [X] T103 [Spec6] Performance test: Verify 3s page load for 10+ cards (SC-001), 1s detail page load (SC-004)

**Checkpoint**: Spec 6 complete - production-ready MVP with all features

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements and documentation

- [X] T104 [P] Add comprehensive error handling across all API endpoints
- [X] T105 [P] Add loading states and error messages in frontend
- [X] T106 [P] Implement frontend/src/components/ErrorBoundary.tsx
- [X] T107 [P] Add backend/data/logs/ directory and configure log rotation
- [X] T108 [P] Create deployment documentation in backend/README.md
- [X] T109 [P] Add API documentation comments (FastAPI auto-generates /docs)
- [X] T110 Run quickstart.md validation (setup from scratch, verify all steps work)
- [X] T111 Create demo data for screenshots and presentations
- [X] T112 Final code review against constitution checklist
- [X] T113 Implement scheduled cleanup job in backend/src/services/cleanup.py (archive content after 72h, delete after 30 days per FR-004)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all specs
- **Spec 1-6 (Phase 3-8)**: All depend on Foundational phase completion
  - Specs must be completed sequentially (each builds on previous)
  - Spec 1 → Spec 2 → Spec 3 → Spec 4 → Spec 5 → Spec 6
- **Polish (Phase 9)**: Depends on Spec 6 completion

### Spec Dependencies

- **Spec 1**: Can start after Foundational (Phase 2) - No dependencies on other specs
- **Spec 2**: Depends on Spec 1 (needs scraping pipeline and database)
- **Spec 3**: Depends on Spec 2 (needs AI filtering and card generation)
- **Spec 4**: Depends on Spec 3 (needs clustering and cards)
- **Spec 5**: Depends on Spec 4 (needs complete pipeline to add sources)
- **Spec 6**: Depends on Spec 5 (needs all features to polish)

### Within Each Spec

- Backend tasks before frontend tasks (API must exist before UI consumes it)
- Models before services (services use models)
- Services before API endpoints (endpoints call services)
- API endpoints before frontend components (frontend calls API)
- Integration tasks last (verify everything works together)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Within each spec, tasks marked [P] can run in parallel if they don't depend on each other
- Frontend and backend tasks can run in parallel if API contract is defined

---

## Parallel Example: Spec 2

```bash
# These can run in parallel (different files, no dependencies):
T038: Implement backend/src/ai/relevance.py
T039: Implement backend/src/ai/generation.py
T040: Implement backend/src/ai/credibility.py

# Then sequentially:
T041: Update pipeline.py (depends on T038-T040)
T042: Implement API call limiter

# These can run in parallel (frontend, independent of backend progress):
T045: Create HotCard.tsx component
T046: Create CardFeed.tsx component

# Then sequentially:
T047: Update Discover.tsx (depends on T045-T046)
T048: Add styling
```

---

## Implementation Strategy

### MVP First (Spec 1-4)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all specs)
3. Complete Phase 3: Spec 1 (minimal pipeline)
4. Complete Phase 4: Spec 2 (AI integration)
5. Complete Phase 5: Spec 3 (clustering)
6. Complete Phase 6: Spec 4 (detail pages)
7. **STOP and VALIDATE**: Self-test for 2-3 days, collect bad cases

### Full MVP (Spec 5-6)

8. Complete Phase 7: Spec 5 (multi-source + fallback)
9. Complete Phase 8: Spec 6 (polish + push)
10. **STOP and VALIDATE**: Self-test for 2-3 days, collect more bad cases

### Quality Refinement (Round 2)

11. Prioritize bad cases: AI quality → Filtering accuracy → Source richness → Visual polish
12. Iteratively fix issues based on real usage data
13. Complete Phase 9: Final polish

---

## Notes

- [P] tasks = different files, no dependencies
- [Spec] label maps task to specific spec for traceability
- Each spec should be independently completable and testable
- Commit after completing each spec (atomic commits)
- Stop at any checkpoint to validate spec independently
- Avoid: vague tasks, same file conflicts, cross-spec dependencies that break independence
- Constitution compliance: All tasks follow defensive engineering, config externalization, prompt separation principles
