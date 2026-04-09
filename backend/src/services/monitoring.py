"""Source health monitoring and degradation handling."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List

import requests

from src.core.config import get_config
from src.core.database import get_session
from src.core.logging import get_logger
from src.models.health_status import SourceHealth

logger = get_logger(__name__)

# URLs to probe for each platform
PROBE_URLS = {
    "hupu": "https://bbs.hupu.com/",
    "dongqiudi": "https://www.dongqiudi.com/",
    "bilibili": "https://www.bilibili.com/",
}


def probe_source_health() -> Dict[str, str]:
    """
    Probe all scraping sources and update health status.

    Performs HTTP HEAD requests to check source availability.
    Updates SourceHealth records in database.

    Returns:
        Dict mapping platform -> status ('healthy', 'degraded', 'failed')
    """
    config = get_config()
    session = get_session()
    statuses = {}

    try:
        for platform, url in PROBE_URLS.items():
            try:
                # Initialize health record if needed
                health = session.query(SourceHealth).filter_by(platform=platform).first()
                if not health:
                    health = SourceHealth(
                        platform=platform,
                        status="healthy",
                        failure_count=0,
                        last_check=datetime.now(),
                    )
                    session.add(health)
                    session.flush()

                # Probe with HEAD request
                try:
                    resp = requests.head(url, timeout=10, allow_redirects=True)
                    is_healthy = resp.status_code < 500
                except Exception:
                    is_healthy = False

                # Update health status
                health.last_check = datetime.now()

                if is_healthy:
                    # Success: reset failure count
                    health.failure_count = 0
                    health.last_success = datetime.now()
                    health.status = "healthy"
                    health.alert_sent = False
                    health.degraded_at = None
                    statuses[platform] = "healthy"
                else:
                    # Failure: increment count
                    health.failure_count += 1

                    # Check thresholds
                    if health.failure_count >= config.monitoring.degradation_threshold:
                        if health.status != "degraded":
                            health.status = "degraded"
                            health.degraded_at = datetime.now()
                            logger.warning(
                                "Source degraded",
                                platform=platform,
                                failure_count=health.failure_count,
                            )
                        statuses[platform] = "degraded"

                    elif health.failure_count >= config.monitoring.failure_alert_threshold:
                        health.status = "failed"
                        # Send alert email if not already sent
                        if not health.alert_sent:
                            send_alert_email(platform, health.failure_count)
                            health.alert_sent = True
                        statuses[platform] = "failed"
                    else:
                        statuses[platform] = health.status

                logger.info(
                    "Source probed",
                    platform=platform,
                    status=statuses[platform],
                    failure_count=health.failure_count,
                )

            except Exception as e:
                logger.error("Failed to probe source", platform=platform, error=str(e))
                statuses[platform] = "unknown"

        session.commit()

    except Exception as e:
        logger.error("Health monitoring failed", error=str(e), exc_info=True)
        session.rollback()

    finally:
        session.close()

    return statuses


def send_alert_email(platform: str, failure_count: int):
    """
    Send email alert when a source fails repeatedly.

    Args:
        platform: Source platform name
        failure_count: Number of consecutive failures
    """
    config = get_config()

    if not config.smtp_server or not config.monitoring.admin_email:
        logger.warning("Email not configured, skipping alert", platform=platform)
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = config.smtp_user
        msg["To"] = config.monitoring.admin_email
        msg["Subject"] = f"[世界杯监控] 数据源告警: {platform} 连续失败 {failure_count} 次"

        body = f"""
数据源健康告警

平台: {platform}
连续失败次数: {failure_count}
检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

请检查数据源可用性并采取相应措施。

如果失败次数达到 {config.monitoring.degradation_threshold} 次，
系统将自动切换到 Bing 搜索引擎备用方案。

---
世界杯热点监控系统
        """
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(config.smtp_server, config.smtp_port) as server:
            server.starttls()
            server.login(config.smtp_user, config.smtp_password)
            server.send_message(msg)

        logger.info("Alert email sent", platform=platform, to=config.monitoring.admin_email)

    except Exception as e:
        logger.error("Failed to send alert email", error=str(e), platform=platform)


def handle_degradation() -> bool:
    """
    Check if any source is degraded and activate Bing fallback if needed.

    Returns:
        True if Bing fallback should be activated
    """
    session = get_session()

    try:
        degraded = session.query(SourceHealth).filter(
            SourceHealth.status.in_(["degraded", "failed"]),
        ).all()

        if degraded:
            degraded_platforms = [h.platform for h in degraded]
            logger.warning(
                "Degraded sources detected",
                platforms=degraded_platforms,
            )

            # If all primary sources are degraded, activate Bing fallback
            all_degraded = len(degraded) >= len(PROBE_URLS)
            return all_degraded

        return False

    finally:
        session.close()


def get_all_health_statuses() -> List[Dict]:
    """Get health status for all sources."""
    session = get_session()

    try:
        records = session.query(SourceHealth).all()
        return [
            {
                "platform": r.platform,
                "status": r.status,
                "failure_count": r.failure_count,
                "last_check": r.last_check.isoformat() if r.last_check else None,
                "last_success": r.last_success.isoformat() if r.last_success else None,
                "degraded_at": r.degraded_at.isoformat() if r.degraded_at else None,
            }
            for r in records
        ]
    finally:
        session.close()
