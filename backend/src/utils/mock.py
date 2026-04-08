"""Mock data generator for dry-run mode."""
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random


def generate_mock_source_content(count: int = 10) -> List[Dict[str, Any]]:
    """
    Generate mock scraped content for dry-run mode.

    Args:
        count: Number of mock items to generate

    Returns:
        List of mock source content dicts
    """
    platforms = ["hupu", "dongqiudi", "bilibili"]
    topics = [
        ("梅西确认参加2026世界杯", "阿根廷球星梅西在接受采访时表示将参加2026年世界杯，这可能是他最后一届世界杯。"),
        ("中国队世界杯预选赛分组出炉", "2026世界杯亚洲区预选赛分组抽签结果公布，中国队被分在第三档。"),
        ("世界杯扩军至48队引发争议", "国际足联确认2026世界杯将扩军至48支球队，引发球迷和专家热议。"),
        ("美加墨世界杯球场名单公布", "2026世界杯组委会公布了16座承办城市的球场名单，包括墨西哥城阿兹特克球场。"),
        ("姆巴佩转会皇马传闻升温", "多家媒体报道姆巴佩可能在世界杯前转会皇马，转会费或创纪录。"),
        ("世界杯门票销售政策出台", "FIFA公布2026世界杯门票销售时间表和价格区间，球迷可从2025年开始申请。"),
        ("哈兰德表态渴望世界杯冠军", "挪威前锋哈兰德在采访中表示，世界杯冠军是他职业生涯最大梦想。"),
        ("世界杯吉祥物设计方案曝光", "网传2026世界杯吉祥物设计方案，融合了美洲文化元素。"),
        ("国足备战世界杯预选赛集训名单", "中国男足公布世界杯预选赛集训名单，多名海外球员入选。"),
        ("C罗宣布2026世界杯后退役", "葡萄牙球星C罗在社交媒体暗示2026世界杯将是他最后一届大赛。"),
    ]

    mock_data = []
    base_time = datetime.now()

    for i in range(min(count, len(topics))):
        topic = topics[i]
        platform = random.choice(platforms)

        mock_data.append({
            "platform": platform,
            "url": f"https://{platform}.com/post/{i+1000}",
            "title": topic[0],
            "raw_html": f"<html><body><h1>{topic[0]}</h1><p>{topic[1]}</p></body></html>",
            "cleaned_text": topic[1],
            "author": f"用户{i+1}",
            "published_at": base_time - timedelta(hours=i),
            "interaction_count": random.randint(100, 10000),
            "image_urls": [],
        })

    return mock_data


def generate_mock_relevance_score() -> Dict[str, Any]:
    """
    Generate mock relevance filtering response.

    Returns:
        Mock relevance score dict
    """
    return {
        "score": random.randint(7, 10),
        "reason": "内容与2026世界杯高度相关，包含关键信息。"
    }


def generate_mock_card() -> Dict[str, Any]:
    """
    Generate mock hot card data.

    Returns:
        Mock card dict
    """
    categories = ["转会传闻", "球队动态", "赛程赛制", "球迷讨论"]
    credibility_levels = ["可信", "待确认", "传闻"]

    return {
        "title": "梅西确认参加世界杯",
        "summary": "阿根廷球星梅西表示将参加2026年世界杯，这可能是他最后一届世界杯。",
        "category": random.choice(categories),
        "credibility": random.choice(credibility_levels),
        "sources": ["虎扑", "懂球帝"],
    }


def generate_mock_detail() -> Dict[str, Any]:
    """
    Generate mock detail page data.

    Returns:
        Mock detail dict
    """
    return {
        "overview": "阿根廷球星梅西在近日接受采访时明确表示，他将参加2026年美加墨世界杯。这将是梅西的第六届世界杯，也很可能是他职业生涯的最后一届世界杯。",
        "viewpoints": [
            {
                "source": "虎扑用户",
                "view": "梅西如果能在2026世界杯再次夺冠，将成为历史第一人。",
                "citation": "[1]"
            },
            {
                "source": "懂球帝专家",
                "view": "梅西届时将年满39岁，体能可能是最大挑战。",
                "citation": "[2]"
            }
        ],
        "timeline": [
            {
                "time": "2026-04-08 10:00",
                "event": "梅西在采访中首次明确表态将参加2026世界杯",
                "citation": "[1]"
            },
            {
                "time": "2026-04-08 14:30",
                "event": "阿根廷足协主席表示欢迎梅西的决定",
                "citation": "[2]"
            }
        ],
        "sources": [
            {
                "id": 1,
                "platform": "虎扑",
                "title": "梅西确认参加2026世界杯",
                "url": "https://hupu.com/post/1000",
                "author": "用户1",
                "published_at": "2026-04-08 10:00"
            },
            {
                "id": 2,
                "platform": "懂球帝",
                "title": "梅西：2026是最后一届",
                "url": "https://dongqiudi.com/post/2000",
                "author": "用户2",
                "published_at": "2026-04-08 14:30"
            }
        ]
    }


def generate_mock_cluster_judgment() -> Dict[str, Any]:
    """
    Generate mock clustering judgment.

    Returns:
        Mock judgment dict
    """
    return {
        "same_topic": random.choice([True, False]),
        "reason": "两篇文章都在讨论梅西参加2026世界杯的消息，属于同一话题。"
    }
