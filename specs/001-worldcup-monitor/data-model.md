# Data Model: 世界杯热点监控助手

**Feature**: 001-worldcup-monitor  
**Date**: 2026-04-08  
**Database**: SQLite  
**ORM**: SQLAlchemy

## Overview

This document defines the database schema for the World Cup Hot Topics Monitor. The data model supports the four-layer pipeline: Data Scraping → AI Processing → Content Display → Real-time Push.

## Entity Relationship Diagram

```
┌─────────────────┐
│ SourceContent   │ (Raw scraped data)
│ - id            │
│ - platform      │
│ - raw_html      │
│ - cleaned_text  │
│ - fingerprint   │
│ - scraped_at    │
└────────┬────────┘
         │ 1:N
         ↓
┌─────────────────┐
│ TopicCluster    │ (Grouped related content)
│ - id            │
│ - cluster_key   │
│ - clustered_at  │
└────────┬────────┘
         │ 1:1
         ↓
┌─────────────────┐
│ HotCard         │ (AI-generated card)
│ - id            │
│ - cluster_id    │
│ - title         │
│ - summary       │
│ - category      │
│ - credibility   │
│ - hotness_score │
│ - generated_at  │
└─────────────────┘

┌─────────────────┐
│ DetailPage      │ (AI-generated detail)
│ - id            │
│ - cluster_id    │
│ - overview      │
│ - viewpoints    │
│ - timeline      │
│ - generated_at  │
└─────────────────┘

┌─────────────────┐
│ SourceHealth    │ (Health monitoring)
│ - id            │
│ - platform      │
│ - status        │
│ - failure_count │
│ - last_check    │
└─────────────────┘

┌─────────────────┐
│ APICallLog      │ (API usage tracking)
│ - id            │
│ - date          │
│ - call_count    │
└─────────────────┘
```

## Entities

### 1. SourceContent (原始内容)

Stores raw and cleaned scraped content from all sources.

**Table**: `source_content`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique identifier |
| platform | VARCHAR(50) | NOT NULL | Source platform: 'hupu', 'dongqiudi', 'bilibili', 'bing' |
| url | TEXT | NOT NULL | Original content URL |
| title | TEXT | NOT NULL | Content title |
| raw_html | TEXT | NULL | Raw HTML/JSON response (for debugging) |
| cleaned_text | TEXT | NOT NULL | Cleaned text after processing |
| author | VARCHAR(200) | NULL | Content author/poster |
| published_at | DATETIME | NOT NULL | Original publish time |
| interaction_count | INTEGER | DEFAULT 0 | Total interactions (likes + comments + views) |
| image_urls | TEXT | NULL | JSON array of image URLs |
| fingerprint | VARCHAR(64) | NOT NULL UNIQUE | SHA256 hash for deduplication |
| scraped_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | When scraped |
| relevance_score | INTEGER | NULL | AI relevance score (1-10), NULL if not yet scored |
| cluster_id | INTEGER | NULL | Foreign key to topic_cluster |
| archived | BOOLEAN | DEFAULT FALSE | True if archived (>72h old + low hotness) |

**Indexes**:
- `idx_fingerprint` on `fingerprint` (for fast duplicate detection)
- `idx_platform_scraped` on `(platform, scraped_at)` (for source queries)
- `idx_cluster_id` on `cluster_id` (for cluster lookups)
- `idx_archived` on `archived` (for filtering active content)

**Validation Rules**:
- `platform` must be one of: 'hupu', 'dongqiudi', 'bilibili', 'bing'
- `relevance_score` must be between 1 and 10 if not NULL
- `fingerprint` is computed as SHA256(title + cleaned_text[:100])
- `image_urls` is JSON array string: `["url1", "url2"]`

**Lifecycle**:
1. Created during scraping with `raw_html` and `cleaned_text`
2. Updated with `relevance_score` after AI filtering
3. Updated with `cluster_id` after clustering
4. Marked `archived=TRUE` after 72 hours if low hotness
5. Deleted after 30 days (retention policy)

### 2. TopicCluster (话题簇)

Groups related source content into topics.

**Table**: `topic_cluster`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique identifier |
| cluster_key | VARCHAR(100) | NOT NULL UNIQUE | Unique key for cluster (e.g., "transfer-messi-2026-04-08") |
| embedding_vector | BLOB | NULL | Serialized embedding vector for similarity search |
| clustered_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | When cluster created |
| last_updated | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | When cluster last updated |
| source_count | INTEGER | DEFAULT 0 | Number of sources in cluster |
| archived | BOOLEAN | DEFAULT FALSE | True if all sources archived |

**Indexes**:
- `idx_cluster_key` on `cluster_key` (for fast lookups)
- `idx_clustered_at` on `clustered_at` (for time-based queries)
- `idx_archived` on `archived` (for filtering active clusters)

**Validation Rules**:
- `cluster_key` format: `{category}-{keywords}-{date}` (e.g., "transfer-messi-2026-04-08")
- `source_count` must match actual count of linked SourceContent records
- `embedding_vector` is pickled numpy array (for cosine similarity)

**Lifecycle**:
1. Created during clustering when similar content found
2. Updated with new sources as they're clustered
3. `last_updated` timestamp refreshed on each update
4. Marked `archived=TRUE` when all linked sources archived
5. Deleted after 30 days if archived

### 3. HotCard (热点卡片)

AI-generated card summaries for display in discovery feed.

**Table**: `hot_card`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique identifier |
| cluster_id | INTEGER | NOT NULL UNIQUE | Foreign key to topic_cluster (1:1) |
| title | VARCHAR(50) | NOT NULL | Card title (≤15 Chinese chars) |
| summary | VARCHAR(200) | NOT NULL | One-sentence summary (≤50 Chinese chars) |
| category | VARCHAR(50) | NOT NULL | Channel category |
| credibility | VARCHAR(20) | NOT NULL | Credibility label |
| source_labels | TEXT | NOT NULL | JSON array of source names |
| image_url | TEXT | NULL | Card image URL (from sources or theme library) |
| hotness_score | FLOAT | NOT NULL | Calculated hotness score |
| generated_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | When card generated |
| cached_until | DATETIME | NOT NULL | Cache expiration time (30 min TTL) |

**Indexes**:
- `idx_cluster_id` on `cluster_id` (for cluster lookups)
- `idx_category` on `category` (for channel filtering)
- `idx_hotness` on `hotness_score DESC` (for sorting)
- `idx_cached_until` on `cached_until` (for cache invalidation)

**Validation Rules**:
- `title` length ≤ 15 Chinese characters (≤45 bytes UTF-8)
- `summary` length ≤ 50 Chinese characters (≤150 bytes UTF-8)
- `category` must be one of: '全部', '热门', '转会传闻', '球队动态', '赛程赛制', '球迷讨论'
- `credibility` must be one of: '可信', '待确认', '传闻'
- `source_labels` is JSON array: `["虎扑", "懂球帝"]`
- `hotness_score` = interaction_sum × (1 / (1 + hours × 0.1)) × (1.1 if has_image else 1.0)

**Lifecycle**:
1. Created after clustering with AI-generated content
2. Cached for 30 minutes (`cached_until` timestamp)
3. Regenerated if cache expired and cluster updated
4. Deleted when cluster archived

### 4. DetailPage (详情页)

AI-generated detailed content for individual topics.

**Table**: `detail_page`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique identifier |
| cluster_id | INTEGER | NOT NULL UNIQUE | Foreign key to topic_cluster (1:1) |
| overview | TEXT | NOT NULL | Event overview (100-200 chars) |
| viewpoints | TEXT | NOT NULL | JSON array of viewpoints with citations |
| timeline | TEXT | NOT NULL | JSON array of timeline events with citations |
| sources | TEXT | NOT NULL | JSON array of source details |
| generated_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | When detail generated |
| cached_until | DATETIME | NOT NULL | Cache expiration time (1 hour TTL) |

**Indexes**:
- `idx_cluster_id` on `cluster_id` (for cluster lookups)
- `idx_cached_until` on `cached_until` (for cache invalidation)

**Validation Rules**:
- `overview` length 100-200 Chinese characters
- `viewpoints` JSON schema:
  ```json
  [
    {
      "source": "虎扑用户",
      "view": "观点内容",
      "citation": "[1]"
    }
  ]
  ```
- `timeline` JSON schema:
  ```json
  [
    {
      "time": "2026-04-08 10:00",
      "event": "事件描述",
      "citation": "[2]"
    }
  ]
  ```
- `sources` JSON schema:
  ```json
  [
    {
      "id": 1,
      "platform": "虎扑",
      "title": "原始标题",
      "url": "https://...",
      "author": "作者",
      "published_at": "2026-04-08 09:30"
    }
  ]
  ```

**Lifecycle**:
1. Created on-demand when user clicks card (lazy generation)
2. Cached for 1 hour (`cached_until` timestamp)
3. Regenerated if cache expired and cluster updated
4. Deleted when cluster archived

### 5. SourceHealth (信源健康)

Tracks health status of scraping sources for monitoring and degradation.

**Table**: `source_health`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique identifier |
| platform | VARCHAR(50) | NOT NULL UNIQUE | Source platform identifier |
| status | VARCHAR(20) | NOT NULL | Current status |
| failure_count | INTEGER | DEFAULT 0 | Consecutive failure count |
| last_check | DATETIME | NOT NULL | Last probe check time |
| last_success | DATETIME | NULL | Last successful probe time |
| degraded_at | DATETIME | NULL | When degraded to backup source |
| alert_sent | BOOLEAN | DEFAULT FALSE | True if alert email sent |

**Indexes**:
- `idx_platform` on `platform` (for fast lookups)
- `idx_status` on `status` (for filtering by status)

**Validation Rules**:
- `platform` must be one of: 'hupu', 'dongqiudi', 'bilibili'
- `status` must be one of: 'healthy', 'degraded', 'failed'
- `failure_count` resets to 0 on successful probe
- `alert_sent` resets to FALSE when status returns to 'healthy'

**State Transitions**:
1. `healthy` → `degraded`: After 5 consecutive failures
2. `degraded` → `healthy`: After 1 successful probe
3. `healthy` → `failed`: After 3 consecutive failures (triggers alert)
4. `failed` → `healthy`: After 1 successful probe

**Lifecycle**:
1. Initialized with all platforms in 'healthy' status
2. Updated every 5 minutes by probe scheduler
3. Triggers email alert when `failure_count` reaches 3
4. Triggers degradation when `failure_count` reaches 5

### 6. APICallLog (API调用日志)

Tracks daily API call counts for rate limiting.

**Table**: `api_call_log`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique identifier |
| date | DATE | NOT NULL UNIQUE | Date of API calls |
| call_count | INTEGER | DEFAULT 0 | Total API calls for this date |
| limit | INTEGER | NOT NULL | Daily limit (from config) |
| last_updated | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | Last increment time |

**Indexes**:
- `idx_date` on `date` (for fast date lookups)

**Validation Rules**:
- `call_count` must be ≤ `limit`
- `date` is unique (one record per day)
- Auto-creates new record for new day

**Lifecycle**:
1. Created automatically on first API call of the day
2. Incremented on each API call
3. Checked before each API call (reject if limit exceeded)
4. Retained for 30 days for analytics

## Relationships

### SourceContent → TopicCluster (Many-to-One)
- Multiple source content items can belong to one topic cluster
- Foreign key: `source_content.cluster_id` → `topic_cluster.id`
- Cascade: When cluster deleted, set `cluster_id` to NULL in sources

### TopicCluster → HotCard (One-to-One)
- Each cluster has exactly one hot card
- Foreign key: `hot_card.cluster_id` → `topic_cluster.id`
- Cascade: When cluster deleted, delete hot card

### TopicCluster → DetailPage (One-to-One)
- Each cluster has exactly one detail page
- Foreign key: `detail_page.cluster_id` → `topic_cluster.id`
- Cascade: When cluster deleted, delete detail page

## Database Configuration

### SQLite Settings

```python
# Connection string
DATABASE_URL = "sqlite:///data/worldcup.db"

# SQLAlchemy engine configuration
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,  # Allow multi-threaded access
        "timeout": 30  # 30-second lock timeout
    },
    pool_pre_ping=True,  # Verify connections before use
    echo=False  # Disable SQL logging in production
)

# Enable WAL mode for better concurrency
with engine.connect() as conn:
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
```

### Migrations

**Strategy**: Use Alembic for schema migrations

**Initial Migration**:
```bash
alembic init alembic
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

**Migration Files Location**: `backend/alembic/versions/`

## Data Retention Policy

| Entity | Retention Period | Deletion Trigger |
|--------|------------------|------------------|
| SourceContent (active) | Until archived | 72 hours + low hotness |
| SourceContent (archived) | 30 days | Scheduled cleanup job |
| TopicCluster (active) | Until all sources archived | All sources archived |
| TopicCluster (archived) | 30 days | Scheduled cleanup job |
| HotCard | Tied to cluster | Cluster deleted |
| DetailPage | Tied to cluster | Cluster deleted |
| SourceHealth | Indefinite | Never deleted |
| APICallLog | 30 days | Scheduled cleanup job |

**Cleanup Job**: Runs daily at 2 AM, deletes records exceeding retention period

## Sample Queries

### Get Active Hot Cards for Discovery Feed
```sql
SELECT hc.*, tc.source_count
FROM hot_card hc
JOIN topic_cluster tc ON hc.cluster_id = tc.id
WHERE tc.archived = FALSE
  AND hc.cached_until > CURRENT_TIMESTAMP
ORDER BY hc.hotness_score DESC
LIMIT 20;
```

### Get Detail Page with Sources
```sql
SELECT dp.*, 
       GROUP_CONCAT(sc.title) as source_titles
FROM detail_page dp
JOIN topic_cluster tc ON dp.cluster_id = tc.id
JOIN source_content sc ON sc.cluster_id = tc.id
WHERE dp.cluster_id = ?
  AND dp.cached_until > CURRENT_TIMESTAMP
GROUP BY dp.id;
```

### Check Source Health Status
```sql
SELECT platform, status, failure_count, last_check
FROM source_health
WHERE status != 'healthy'
ORDER BY failure_count DESC;
```

### Check Daily API Usage
```sql
SELECT call_count, limit, 
       (call_count * 100.0 / limit) as usage_percent
FROM api_call_log
WHERE date = CURRENT_DATE;
```

## Next Steps

Phase 1 will continue with:
1. **contracts/**: API endpoint specifications
2. **quickstart.md**: Development setup guide
