# API Endpoints: 世界杯热点监控助手

**Feature**: 001-worldcup-monitor  
**Date**: 2026-04-08  
**Base URL**: `http://localhost:8000/api`  
**Protocol**: REST over HTTP/HTTPS

## Overview

This document defines all REST API endpoints for the World Cup Hot Topics Monitor. The API follows RESTful conventions and returns JSON responses.

## Authentication

**MVP**: No authentication required (public read-only API)

**Future**: Optional authentication for personalization features (P1)

## Common Response Format

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2026-04-08T10:30:00Z"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { ... }
  },
  "timestamp": "2026-04-08T10:30:00Z"
}
```

## Endpoints

### 1. Get Hot Topic Cards

Retrieve paginated list of hot topic cards for discovery feed.

**Endpoint**: `GET /api/cards`

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| category | string | No | "全部" | Channel filter: "全部", "热门", "转会传闻", "球队动态", "赛程赛制", "球迷讨论" |
| limit | integer | No | 20 | Number of cards to return (max 50) |
| offset | integer | No | 0 | Pagination offset |

**Response**: `200 OK`
```json
{
  "success": true,
  "data": {
    "cards": [
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
    ],
    "total": 45,
    "has_more": true
  },
  "timestamp": "2026-04-08T10:30:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid category or pagination parameters
- `500 Internal Server Error`: Database or processing error

**Caching**: Cards cached for 30 minutes, returns cached data if available

---

### 2. Get New Cards (Polling)

Check for new hot topic cards since a given timestamp.

**Endpoint**: `GET /api/cards/new`

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| since | string | Yes | - | ISO 8601 timestamp (e.g., "2026-04-08T10:00:00Z") |
| category | string | No | "全部" | Channel filter |

**Response**: `200 OK`
```json
{
  "success": true,
  "data": {
    "new_count": 3,
    "cards": [
      {
        "id": 126,
        "title": "C罗宣布退出国家队",
        "summary": "葡萄牙球星C罗在社交媒体宣布将不参加2026世界杯，结束国家队生涯",
        "category": "球队动态",
        "credibility": "待确认",
        "sources": ["B站"],
        "image_url": null,
        "hotness_score": 88.7,
        "generated_at": "2026-04-08T10:25:00Z"
      }
    ]
  },
  "timestamp": "2026-04-08T10:30:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid timestamp format
- `500 Internal Server Error`: Database error

**Usage**: Frontend polls this endpoint every 30 seconds to check for new content

---

### 3. Get Card Detail

Retrieve detailed AI-generated content for a specific hot topic.

**Endpoint**: `GET /api/cards/{card_id}/detail`

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| card_id | integer | Hot card ID |

**Response**: `200 OK`
```json
{
  "success": true,
  "data": {
    "id": 123,
    "card": {
      "title": "梅西确认参加2026世界杯",
      "credibility": "可信",
      "generated_at": "2026-04-08T10:00:00Z"
    },
    "overview": "阿根廷球星梅西在接受采访时明确表示将参加2026年美加墨世界杯。这将是梅西的第六次世界杯之旅，也可能是他职业生涯的最后一届世界杯。",
    "viewpoints": [
      {
        "source": "虎扑用户",
        "view": "梅西状态保持得很好，2026年他39岁仍有竞争力",
        "citation": "[1]"
      },
      {
        "source": "懂球帝专家",
        "view": "这可能是梅西最后的世界杯机会，阿根廷队将全力支持",
        "citation": "[2]"
      }
    ],
    "timeline": [
      {
        "time": "2026-04-08 09:30",
        "event": "梅西在采访中首次提及2026世界杯计划",
        "citation": "[1]"
      },
      {
        "time": "2026-04-08 10:00",
        "event": "阿根廷足协官方转发梅西采访内容",
        "citation": "[2]"
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
      },
      {
        "id": 2,
        "platform": "懂球帝",
        "title": "官方：梅西确认参加下届世界杯",
        "url": "https://www.dongqiudi.com/...",
        "author": "懂球帝编辑部",
        "published_at": "2026-04-08T10:00:00Z"
      }
    ]
  },
  "timestamp": "2026-04-08T10:30:00Z"
}
```

**Error Responses**:
- `404 Not Found`: Card ID does not exist
- `500 Internal Server Error`: Generation or database error

**Caching**: Detail pages cached for 1 hour, regenerated if cache expired

---

### 4. Get Channel Categories

Retrieve list of available channel categories with card counts.

**Endpoint**: `GET /api/categories`

**Response**: `200 OK`
```json
{
  "success": true,
  "data": {
    "categories": [
      {
        "name": "全部",
        "count": 45
      },
      {
        "name": "热门",
        "count": 12
      },
      {
        "name": "转会传闻",
        "count": 8
      },
      {
        "name": "球队动态",
        "count": 15
      },
      {
        "name": "赛程赛制",
        "count": 6
      },
      {
        "name": "球迷讨论",
        "count": 4
      }
    ]
  },
  "timestamp": "2026-04-08T10:30:00Z"
}
```

**Error Responses**:
- `500 Internal Server Error`: Database error

**Caching**: Category counts cached for 5 minutes

---

### 5. Health Check

Check API and system health status.

**Endpoint**: `GET /api/health`

**Response**: `200 OK`
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2026-04-08T10:30:00Z",
    "components": {
      "database": "healthy",
      "scheduler": "healthy",
      "sources": {
        "hupu": "healthy",
        "dongqiudi": "healthy",
        "bilibili": "degraded"
      },
      "api_usage": {
        "calls_today": 1234,
        "limit": 10000,
        "remaining": 8766
      }
    }
  },
  "timestamp": "2026-04-08T10:30:00Z"
}
```

**Error Responses**:
- `503 Service Unavailable`: Critical component failure

**Usage**: Monitoring systems can poll this endpoint to check service health

---

### 6. Get Source Health Status

Retrieve detailed health status of all scraping sources.

**Endpoint**: `GET /api/sources/health`

**Response**: `200 OK`
```json
{
  "success": true,
  "data": {
    "sources": [
      {
        "platform": "hupu",
        "status": "healthy",
        "failure_count": 0,
        "last_check": "2026-04-08T10:25:00Z",
        "last_success": "2026-04-08T10:25:00Z"
      },
      {
        "platform": "dongqiudi",
        "status": "healthy",
        "failure_count": 0,
        "last_check": "2026-04-08T10:25:00Z",
        "last_success": "2026-04-08T10:25:00Z"
      },
      {
        "platform": "bilibili",
        "status": "degraded",
        "failure_count": 5,
        "last_check": "2026-04-08T10:25:00Z",
        "last_success": "2026-04-08T09:50:00Z",
        "degraded_at": "2026-04-08T10:20:00Z"
      }
    ],
    "backup_active": true,
    "backup_source": "bing"
  },
  "timestamp": "2026-04-08T10:30:00Z"
}
```

**Error Responses**:
- `500 Internal Server Error`: Database error

**Usage**: Admin dashboard to monitor source reliability

---

## Rate Limiting

**MVP**: No rate limiting (public API, single-server deployment)

**Future**: Implement rate limiting if abuse detected:
- 100 requests per minute per IP
- 1000 requests per hour per IP

## CORS Configuration

**Development**:
```
Access-Control-Allow-Origin: http://localhost:5173
Access-Control-Allow-Methods: GET, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

**Production**:
```
Access-Control-Allow-Origin: https://worldcup-monitor.example.com
Access-Control-Allow-Methods: GET, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| INVALID_PARAMETER | 400 | Invalid query parameter or request body |
| NOT_FOUND | 404 | Resource not found |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests (future) |
| INTERNAL_ERROR | 500 | Internal server error |
| SERVICE_UNAVAILABLE | 503 | Service temporarily unavailable |
| DATABASE_ERROR | 500 | Database connection or query error |
| AI_PROCESSING_ERROR | 500 | AI API call or parsing error |

## API Versioning

**Current Version**: v1 (implicit, no version prefix in URL)

**Future Versioning Strategy**: 
- Add `/api/v2/` prefix when breaking changes introduced
- Maintain v1 for 6 months after v2 release
- Deprecation warnings in response headers

## Performance Targets

| Endpoint | Target Latency (p95) | Notes |
|----------|---------------------|-------|
| GET /api/cards | < 500ms | Cached responses < 100ms |
| GET /api/cards/new | < 200ms | Lightweight query |
| GET /api/cards/{id}/detail | < 1000ms | May trigger AI generation |
| GET /api/categories | < 200ms | Cached responses |
| GET /api/health | < 100ms | Simple status check |
| GET /api/sources/health | < 200ms | Database query |

## Testing

### Example cURL Commands

**Get hot cards**:
```bash
curl -X GET "http://localhost:8000/api/cards?category=热门&limit=10"
```

**Check for new cards**:
```bash
curl -X GET "http://localhost:8000/api/cards/new?since=2026-04-08T10:00:00Z"
```

**Get card detail**:
```bash
curl -X GET "http://localhost:8000/api/cards/123/detail"
```

**Health check**:
```bash
curl -X GET "http://localhost:8000/api/health"
```

### Integration Test Coverage

- All endpoints return valid JSON
- Error responses follow standard format
- Pagination works correctly
- Caching headers present
- CORS headers configured
- Performance targets met
