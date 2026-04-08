# Data Schemas: 世界杯热点监控助手

**Feature**: 001-worldcup-monitor  
**Date**: 2026-04-08  
**Format**: JSON  
**Validation**: Pydantic models

## Overview

This document defines all data schemas used in API requests and responses. All schemas are implemented as Pydantic models for runtime validation.

## Response Schemas

### HotCardSchema

Represents a hot topic card in the discovery feed.

```json
{
  "id": 123,
  "title": "梅西确认参加2026世界杯",
  "summary": "阿根廷球星梅西在接受采访时表示将参加2026年世界杯，这将是他的第六次世界杯之旅",
  "category": "球队动态",
  "credibility": "可信",
  "sources": ["虎扑", "懂球帝"],
  "image_url": "https://cdn.example.com/images/messi.jpg",
  "hotness_score": 95.3,
  "generated_at": "2026-04-08T10:00:00Z"
}
```

**Field Specifications**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | integer | > 0 | Unique card identifier |
| title | string | 1-50 chars, ≤15 Chinese chars | Card title |
| summary | string | 1-200 chars, ≤50 Chinese chars | One-sentence summary |
| category | string | enum | One of: "全部", "热门", "转会传闻", "球队动态", "赛程赛制", "球迷讨论" |
| credibility | string | enum | One of: "可信", "待确认", "传闻" |
| sources | array[string] | 1-10 items | Source platform names |
| image_url | string \| null | valid URL or null | Card image URL |
| hotness_score | float | 0-100 | Calculated hotness score |
| generated_at | string | ISO 8601 datetime | When card was generated |

**Pydantic Model**:
```python
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional, List

class HotCardSchema(BaseModel):
    id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=50)
    summary: str = Field(min_length=1, max_length=200)
    category: str = Field(pattern="^(全部|热门|转会传闻|球队动态|赛程赛制|球迷讨论)$")
    credibility: str = Field(pattern="^(可信|待确认|传闻)$")
    sources: List[str] = Field(min_items=1, max_items=10)
    image_url: Optional[HttpUrl] = None
    hotness_score: float = Field(ge=0, le=100)
    generated_at: datetime
```

---

### DetailPageSchema

Represents detailed AI-generated content for a topic.

```json
{
  "id": 123,
  "card": {
    "title": "梅西确认参加2026世界杯",
    "credibility": "可信",
    "generated_at": "2026-04-08T10:00:00Z"
  },
  "overview": "阿根廷球星梅西在接受采访时明确表示将参加2026年美加墨世界杯...",
  "viewpoints": [
    {
      "source": "虎扑用户",
      "view": "梅西状态保持得很好，2026年他39岁仍有竞争力",
      "citation": "[1]"
    }
  ],
  "timeline": [
    {
      "time": "2026-04-08 09:30",
      "event": "梅西在采访中首次提及2026世界杯计划",
      "citation": "[1]"
    }
  ],
  "sources": [
    {
      "id": 1,
      "platform": "虎扑",
      "title": "梅西：我会参加2026世界杯",
      "url": "https://bbs.hupu.com/...",
      "author": "足球话题君",
      "published_at": "2026-04-08T09:30:00Z"
    }
  ]
}
```

**Field Specifications**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | integer | > 0 | Detail page identifier |
| card | object | CardSummary | Basic card info |
| overview | string | 100-600 chars | Event overview |
| viewpoints | array[Viewpoint] | 0-20 items | Different viewpoints with citations |
| timeline | array[TimelineEvent] | 0-50 items | Chronological events |
| sources | array[SourceDetail] | 1-50 items | Original source details |

**Nested Schemas**:

**CardSummary**:
```json
{
  "title": "梅西确认参加2026世界杯",
  "credibility": "可信",
  "generated_at": "2026-04-08T10:00:00Z"
}
```

**Viewpoint**:
```json
{
  "source": "虎扑用户",
  "view": "梅西状态保持得很好，2026年他39岁仍有竞争力",
  "citation": "[1]"
}
```

**TimelineEvent**:
```json
{
  "time": "2026-04-08 09:30",
  "event": "梅西在采访中首次提及2026世界杯计划",
  "citation": "[1]"
}
```

**SourceDetail**:
```json
{
  "id": 1,
  "platform": "虎扑",
  "title": "梅西：我会参加2026世界杯",
  "url": "https://bbs.hupu.com/...",
  "author": "足球话题君",
  "published_at": "2026-04-08T09:30:00Z"
}
```

**Pydantic Models**:
```python
class CardSummary(BaseModel):
    title: str
    credibility: str
    generated_at: datetime

class Viewpoint(BaseModel):
    source: str = Field(min_length=1, max_length=100)
    view: str = Field(min_length=1, max_length=500)
    citation: str = Field(pattern=r"^\[\d+\]$")

class TimelineEvent(BaseModel):
    time: str = Field(pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")
    event: str = Field(min_length=1, max_length=300)
    citation: str = Field(pattern=r"^\[\d+\]$")

class SourceDetail(BaseModel):
    id: int = Field(gt=0)
    platform: str
    title: str
    url: HttpUrl
    author: str
    published_at: datetime

class DetailPageSchema(BaseModel):
    id: int = Field(gt=0)
    card: CardSummary
    overview: str = Field(min_length=100, max_length=600)
    viewpoints: List[Viewpoint] = Field(max_items=20)
    timeline: List[TimelineEvent] = Field(max_items=50)
    sources: List[SourceDetail] = Field(min_items=1, max_items=50)
```

---

### CategorySchema

Represents a channel category with card count.

```json
{
  "name": "转会传闻",
  "count": 8
}
```

**Field Specifications**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| name | string | enum | Category name |
| count | integer | >= 0 | Number of cards in category |

**Pydantic Model**:
```python
class CategorySchema(BaseModel):
    name: str = Field(pattern="^(全部|热门|转会传闻|球队动态|赛程赛制|球迷讨论)$")
    count: int = Field(ge=0)
```

---

### SourceHealthSchema

Represents health status of a scraping source.

```json
{
  "platform": "bilibili",
  "status": "degraded",
  "failure_count": 5,
  "last_check": "2026-04-08T10:25:00Z",
  "last_success": "2026-04-08T09:50:00Z",
  "degraded_at": "2026-04-08T10:20:00Z"
}
```

**Field Specifications**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| platform | string | enum | One of: "hupu", "dongqiudi", "bilibili" |
| status | string | enum | One of: "healthy", "degraded", "failed" |
| failure_count | integer | >= 0 | Consecutive failure count |
| last_check | string | ISO 8601 datetime | Last probe check time |
| last_success | string \| null | ISO 8601 datetime or null | Last successful check |
| degraded_at | string \| null | ISO 8601 datetime or null | When degraded (if applicable) |

**Pydantic Model**:
```python
class SourceHealthSchema(BaseModel):
    platform: str = Field(pattern="^(hupu|dongqiudi|bilibili)$")
    status: str = Field(pattern="^(healthy|degraded|failed)$")
    failure_count: int = Field(ge=0)
    last_check: datetime
    last_success: Optional[datetime] = None
    degraded_at: Optional[datetime] = None
```

---

## Request Schemas

### Query Parameters

**GetCardsParams**:
```python
class GetCardsParams(BaseModel):
    category: str = Field(default="全部", pattern="^(全部|热门|转会传闻|球队动态|赛程赛制|球迷讨论)$")
    limit: int = Field(default=20, ge=1, le=50)
    offset: int = Field(default=0, ge=0)
```

**GetNewCardsParams**:
```python
class GetNewCardsParams(BaseModel):
    since: datetime
    category: str = Field(default="全部", pattern="^(全部|热门|转会传闻|球队动态|赛程赛制|球迷讨论)$")
```

---

## Internal Schemas (AI Processing)

### RelevanceScoreSchema

AI output for relevance filtering.

```json
{
  "score": 8,
  "reason": "内容直接相关2026世界杯预选赛，包含具体球队和赛程信息"
}
```

**Pydantic Model**:
```python
class RelevanceScoreSchema(BaseModel):
    score: int = Field(ge=1, le=10)
    reason: str = Field(min_length=10, max_length=200)
```

---

### ClusteringDecisionSchema

AI output for topic clustering.

```json
{
  "same_topic": true,
  "reason": "两篇文章都讨论梅西参加2026世界杯的决定，事件相同"
}
```

**Pydantic Model**:
```python
class ClusteringDecisionSchema(BaseModel):
    same_topic: bool
    reason: str = Field(min_length=10, max_length=200)
```

---

### CardGenerationSchema

AI output for card generation.

```json
{
  "title": "梅西确认参加世界杯",
  "summary": "阿根廷球星梅西表示将参加2026年世界杯，这将是他的第六次世界杯之旅",
  "category": "球队动态"
}
```

**Pydantic Model**:
```python
class CardGenerationSchema(BaseModel):
    title: str = Field(min_length=1, max_length=50)
    summary: str = Field(min_length=1, max_length=200)
    category: str = Field(pattern="^(转会传闻|球队动态|赛程赛制|球迷讨论)$")
```

---

### DetailGenerationSchema

AI output for detail page generation.

```json
{
  "overview": "阿根廷球星梅西在接受采访时明确表示将参加2026年美加墨世界杯...",
  "viewpoints": [
    {
      "source": "虎扑用户",
      "view": "梅西状态保持得很好，2026年他39岁仍有竞争力",
      "citation": "[1]"
    }
  ],
  "timeline": [
    {
      "time": "2026-04-08 09:30",
      "event": "梅西在采访中首次提及2026世界杯计划",
      "citation": "[1]"
    }
  ]
}
```

**Pydantic Model**:
```python
class DetailGenerationSchema(BaseModel):
    overview: str = Field(min_length=100, max_length=600)
    viewpoints: List[Viewpoint] = Field(max_items=20)
    timeline: List[TimelineEvent] = Field(max_items=50)
```

---

### CredibilityScoreSchema

AI output for credibility scoring.

```json
{
  "credibility": "可信",
  "reason": "多个权威来源交叉验证，包含官方声明"
}
```

**Pydantic Model**:
```python
class CredibilityScoreSchema(BaseModel):
    credibility: str = Field(pattern="^(可信|待确认|传闻)$")
    reason: str = Field(min_length=10, max_length=200)
```

---

## Validation Examples

### Valid HotCard
```python
card = HotCardSchema(
    id=123,
    title="梅西确认参加2026世界杯",
    summary="阿根廷球星梅西在接受采访时表示将参加2026年世界杯",
    category="球队动态",
    credibility="可信",
    sources=["虎扑", "懂球帝"],
    image_url="https://cdn.example.com/images/messi.jpg",
    hotness_score=95.3,
    generated_at=datetime.now()
)
```

### Invalid HotCard (ValidationError)
```python
# Title too long (>15 Chinese chars)
card = HotCardSchema(
    title="梅西在接受采访时明确表示将参加2026年美加墨世界杯",  # Too long!
    # ... other fields
)
# Raises: ValidationError
```

### Parsing AI Response
```python
def parse_ai_card_generation(response: str) -> Optional[CardGenerationSchema]:
    """Safely parse AI card generation response."""
    try:
        data = json.loads(response)
        return CardGenerationSchema(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        logger.error(f"AI parse failed: {e}")
        return None
```

---

## Schema Evolution

**Versioning Strategy**:
- Add new optional fields without breaking changes
- Deprecate fields with 6-month notice
- Use schema version field for major changes

**Example Migration**:
```python
# v1 schema
class HotCardSchemaV1(BaseModel):
    id: int
    title: str
    # ... existing fields

# v2 schema (adds optional field)
class HotCardSchemaV2(HotCardSchemaV1):
    tags: Optional[List[str]] = None  # New optional field
```
