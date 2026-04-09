"""Main pipeline orchestration."""
import json
from typing import List, Optional
from datetime import datetime, timedelta

from src.scrapers.hupu import scrape_hupu
from src.scrapers.dongqiudi import scrape_dongqiudi
from src.scrapers.bilibili import scrape_bilibili
from src.scrapers.bing_fallback import scrape_bing_fallback
from src.models.source_content import SourceContent
from src.models.topic_cluster import TopicCluster
from src.models.hot_card import HotCard
from src.models.api_call_log import APICallLog
from src.ai.relevance import filter_relevance
from src.ai.generation import generate_card
from src.ai.credibility import calculate_credibility
from src.ai.clustering import (
    cluster_by_similarity,
    refine_with_llm,
    compute_single_embedding,
    serialize_embedding,
)
from src.utils.text import clean_text
from src.utils.hash import generate_fingerprint
from src.utils.images import select_card_image
from src.core.database import get_session
from src.core.config import get_config
from src.core.logging import get_logger, log_pipeline_stage

logger = get_logger(__name__)


@log_pipeline_stage("scrape_and_store")
def scrape_and_store() -> List[SourceContent]:
    """
    Scrape content from all sources and store in database.

    Pipeline: scrape (all sources parallel) → clean → fingerprint → deduplicate → store

    Spec 5: Multi-source scraping with fallback support.

    Returns:
        List of stored SourceContent objects
    """
    config = get_config()
    session = get_session()

    stored_items = []

    try:
        keyword = config.scraping.keywords[0] if config.scraping.keywords else "2026世界杯"
        logger.info("Starting multi-source scraping pipeline", keyword=keyword)

        # Scrape all sources (with error isolation)
        all_scraped = []

        # Source 1: Hupu
        try:
            hupu_data = scrape_hupu(keyword=keyword, limit=20)
            all_scraped.extend(hupu_data)
            logger.info("Hupu scraped", count=len(hupu_data))
        except Exception as e:
            logger.error("Hupu scraping failed", error=str(e))

        # Source 2: DongQiuDi
        try:
            dqd_data = scrape_dongqiudi(keyword=keyword, limit=20)
            all_scraped.extend(dqd_data)
            logger.info("DongQiuDi scraped", count=len(dqd_data))
        except Exception as e:
            logger.error("DongQiuDi scraping failed", error=str(e))

        # Source 3: Bilibili
        try:
            bili_data = scrape_bilibili(keyword=keyword, limit=10)
            all_scraped.extend(bili_data)
            logger.info("Bilibili scraped", count=len(bili_data))
        except Exception as e:
            logger.error("Bilibili scraping failed", error=str(e))

        # Check if we need Bing fallback (if all primary sources failed)
        if not all_scraped:
            logger.warning("All primary sources failed, activating Bing fallback")
            try:
                bing_data = scrape_bing_fallback(keyword=keyword, limit=10)
                all_scraped.extend(bing_data)
                logger.info("Bing fallback activated", count=len(bing_data))
            except Exception as e:
                logger.error("Bing fallback also failed", error=str(e))

        logger.info("Total scraped data", count=len(all_scraped))

        # Process each scraped item
        for item in all_scraped:
            try:
                # Clean text
                cleaned_text = clean_text(item["raw_html"])

                # Generate fingerprint for deduplication
                fingerprint = generate_fingerprint(item["title"], cleaned_text)

                # Check if already exists in DB
                existing = session.query(SourceContent).filter_by(fingerprint=fingerprint).first()
                if existing:
                    continue

                # Check if already added in this batch (same fingerprint)
                if any(s.fingerprint == fingerprint for s in stored_items):
                    continue

                # Create SourceContent object
                source_content = SourceContent(
                    platform=item["platform"],
                    url=item["url"],
                    title=item["title"],
                    raw_html=item["raw_html"],
                    cleaned_text=cleaned_text,
                    author=item.get("author"),
                    published_at=item["published_at"],
                    interaction_count=item.get("interaction_count", 0),
                    image_urls=str(item.get("image_urls", [])),
                    fingerprint=fingerprint,
                    scraped_at=datetime.now(),
                )

                session.add(source_content)
                session.flush()  # Flush to catch unique constraint early
                stored_items.append(source_content)

            except Exception as e:
                session.rollback()
                logger.warning("Skipped item", error=str(e)[:80])
                continue

        session.commit()
        logger.info("Scraping pipeline completed", stored_count=len(stored_items))

    except Exception as e:
        logger.error("Scraping pipeline failed", error=str(e), exc_info=True)
        session.rollback()
        raise

    finally:
        session.close()

    return stored_items


@log_pipeline_stage("ai_processing")
def run_ai_pipeline() -> List[HotCard]:
    """
    Run AI processing pipeline on unprocessed source content.

    Pipeline: filter relevance → cluster by similarity → refine with LLM → generate cards → score credibility

    Spec 3: Full clustering support (embedding + LLM refinement).

    Returns:
        List of generated HotCard objects
    """
    config = get_config()
    session = get_session()
    generated_cards = []

    try:
        # Step 1: Get unprocessed content (no relevance_score yet)
        unprocessed = session.query(SourceContent).filter(
            SourceContent.relevance_score.is_(None),
            SourceContent.archived == False,
        ).order_by(SourceContent.scraped_at.desc()).all()

        logger.info("AI pipeline starting", unprocessed_count=len(unprocessed))

        if not unprocessed:
            logger.info("No unprocessed content found")
            return generated_cards

        # Step 2: Filter by relevance
        relevant_items = []
        for item in unprocessed:
            try:
                score = filter_relevance(item.title, item.cleaned_text)
                if score is not None:
                    item.relevance_score = score.score
                    if score.score >= 7:
                        relevant_items.append(item)
                        logger.info(
                            "Content passed relevance filter",
                            title=item.title[:30],
                            score=score.score,
                        )
                    else:
                        logger.info(
                            "Content filtered out",
                            title=item.title[:30],
                            score=score.score,
                        )
                else:
                    # If AI fails, default score 5 (borderline) - don't block pipeline
                    item.relevance_score = 5
                    logger.warning(
                        "Relevance scoring failed, using default",
                        title=item.title[:30],
                    )
            except Exception as e:
                logger.error("Relevance scoring error", error=str(e), title=item.title[:30])
                item.relevance_score = 5
                continue

        session.commit()
        logger.info("Relevance filtering done", relevant_count=len(relevant_items))

        if not relevant_items:
            return generated_cards

        # Step 3: Cluster relevant items
        # Get unclustered relevant items
        unclustered = [item for item in relevant_items if item.cluster_id is None]

        if unclustered:
            # Also get existing unclustered items from DB within time window
            time_window = datetime.now() - timedelta(hours=config.clustering.time_window_hours)
            existing_unclustered = session.query(SourceContent).filter(
                SourceContent.relevance_score >= 7,
                SourceContent.cluster_id.is_(None),
                SourceContent.archived == False,
                SourceContent.scraped_at >= time_window,
            ).all()

            # Combine new + existing unclustered, deduplicating by id
            all_unclustered_map = {item.id: item for item in existing_unclustered}
            for item in unclustered:
                all_unclustered_map[item.id] = item
            all_unclustered = list(all_unclustered_map.values())

            # Prepare items for clustering
            cluster_input = [
                {"title": item.title, "cleaned_text": item.cleaned_text, "id": item.id}
                for item in all_unclustered
            ]

            # Stage 1: Embedding-based clustering
            embedding_clusters = cluster_by_similarity(cluster_input)

            # Stage 2: LLM refinement for multi-item clusters
            refined_clusters = []
            for cluster_indices in embedding_clusters:
                if len(cluster_indices) <= 1:
                    refined_clusters.append(cluster_indices)
                    continue

                # For clusters with 2+ items, verify with LLM
                verified = [cluster_indices[0]]  # First item always in cluster
                for idx in cluster_indices[1:]:
                    judgment = refine_with_llm(
                        cluster_input[cluster_indices[0]],
                        cluster_input[idx],
                    )
                    if judgment and judgment.same_topic:
                        verified.append(idx)
                    else:
                        # This item should be in its own cluster
                        refined_clusters.append([idx])
                refined_clusters.append(verified)

            logger.info(
                "Clustering complete",
                input_count=len(all_unclustered),
                clusters=len(refined_clusters),
            )

            # Step 4: Create/update TopicClusters and generate cards
            for cluster_indices in refined_clusters:
                try:
                    cluster_items = [all_unclustered[i] for i in cluster_indices]

                    # Check if any item is already assigned to a cluster
                    existing_cluster_id = None
                    for ci in cluster_items:
                        if ci.cluster_id is not None:
                            existing_cluster_id = ci.cluster_id
                            break

                    if existing_cluster_id:
                        # Add to existing cluster
                        cluster = session.query(TopicCluster).get(existing_cluster_id)
                        if cluster:
                            for ci in cluster_items:
                                if ci.cluster_id is None:
                                    ci.cluster_id = cluster.id
                                    cluster.source_count += 1
                            cluster.last_updated = datetime.now()
                            session.commit()

                            # Regenerate card for updated cluster
                            _regenerate_card_for_cluster(session, cluster, generated_cards)
                        continue

                    # Create new cluster
                    representative = cluster_items[0]
                    cluster_key = (
                        f"{representative.platform}"
                        f"-{generate_fingerprint(representative.title, '')[:8]}"
                        f"-{datetime.now().strftime('%Y%m%d')}"
                    )

                    # Check if cluster key already exists
                    existing = session.query(TopicCluster).filter_by(cluster_key=cluster_key).first()
                    if existing:
                        for ci in cluster_items:
                            if ci.cluster_id is None:
                                ci.cluster_id = existing.id
                                existing.source_count += 1
                        existing.last_updated = datetime.now()
                        session.commit()
                        _regenerate_card_for_cluster(session, existing, generated_cards)
                        continue

                    # Compute cluster embedding (average of item embeddings)
                    try:
                        embedding = compute_single_embedding(
                            f"{representative.title} {representative.cleaned_text[:200]}"
                        )
                        embedding_bytes = serialize_embedding(embedding)
                    except Exception:
                        embedding_bytes = None

                    cluster = TopicCluster(
                        cluster_key=cluster_key,
                        embedding_vector=embedding_bytes,
                        clustered_at=datetime.now(),
                        last_updated=datetime.now(),
                        source_count=len(cluster_items),
                    )
                    session.add(cluster)
                    session.flush()

                    # Assign items to cluster
                    for ci in cluster_items:
                        ci.cluster_id = cluster.id

                    session.commit()

                    # Generate card for this cluster
                    _generate_card_for_cluster(session, cluster, cluster_items, generated_cards)

                except Exception as e:
                    logger.error(
                        "Failed to process cluster",
                        error=str(e),
                        exc_info=True,
                    )
                    continue

        logger.info("AI pipeline completed", cards_generated=len(generated_cards))

    except Exception as e:
        logger.error("AI pipeline failed", error=str(e), exc_info=True)
        session.rollback()
        raise

    finally:
        session.close()

    return generated_cards


def _generate_card_for_cluster(
    session,
    cluster: TopicCluster,
    cluster_items: List[SourceContent],
    generated_cards: List[HotCard],
):
    """Generate a HotCard for a new cluster."""
    try:
        # Check if card already exists
        existing_card = session.query(HotCard).filter_by(cluster_id=cluster.id).first()
        if existing_card:
            return

        # Prepare source data for card generation (multiple sources)
        source_data = [
            {
                "platform": item.platform,
                "title": item.title,
                "cleaned_text": item.cleaned_text,
            }
            for item in cluster_items
        ]

        # Generate card using AI
        card_result = generate_card(source_data)
        if card_result is None:
            logger.warning("Card generation failed for cluster", cluster_id=cluster.id)
            return

        # Calculate credibility
        cred_result = calculate_credibility(source_data, card_result.summary)
        credibility = cred_result.credibility if cred_result else "待确认"

        # Single source always at most "待确认"
        if len(cluster_items) == 1 and credibility == "可信":
            credibility = "待确认"

        # Calculate hotness score
        total_interactions = sum(item.interaction_count for item in cluster_items)
        latest_published = max(item.published_at for item in cluster_items)
        hours_age = max(
            (datetime.now() - latest_published).total_seconds() / 3600,
            0.1,
        )
        has_image = any(
            item.image_urls and item.image_urls != "[]"
            for item in cluster_items
        )
        hotness = total_interactions * (1 / (1 + hours_age * 0.1))
        if has_image:
            hotness *= 1.1

        # Select image: original sources > theme > null
        all_image_urls = []
        for item in cluster_items:
            if item.image_urls and item.image_urls not in ("[]", "['']", ""):
                try:
                    import ast
                    urls = ast.literal_eval(item.image_urls)
                    if isinstance(urls, list):
                        all_image_urls.extend(urls)
                except Exception:
                    pass
        card_image = select_card_image(all_image_urls, card_result.category)

        hot_card = HotCard(
            cluster_id=cluster.id,
            title=card_result.title,
            summary=card_result.summary,
            category=card_result.category,
            credibility=credibility,
            source_labels=json.dumps(card_result.sources, ensure_ascii=False),
            image_url=card_image,
            hotness_score=round(hotness, 2),
            generated_at=datetime.now(),
            cached_until=datetime.now() + timedelta(minutes=30),
        )
        session.add(hot_card)
        session.commit()
        generated_cards.append(hot_card)

        logger.info(
            "Hot card created",
            title=card_result.title,
            category=card_result.category,
            credibility=credibility,
            source_count=len(cluster_items),
        )

    except Exception as e:
        logger.error("Failed to generate card for cluster", error=str(e), exc_info=True)


def _regenerate_card_for_cluster(
    session,
    cluster: TopicCluster,
    generated_cards: List[HotCard],
):
    """Regenerate a HotCard for an updated cluster (new sources added)."""
    try:
        # Get all sources in cluster
        cluster_items = session.query(SourceContent).filter_by(cluster_id=cluster.id).all()

        # Delete existing card
        existing_card = session.query(HotCard).filter_by(cluster_id=cluster.id).first()
        if existing_card:
            session.delete(existing_card)
            session.flush()

        # Generate new card
        _generate_card_for_cluster(session, cluster, cluster_items, generated_cards)

    except Exception as e:
        logger.error("Failed to regenerate card", error=str(e), exc_info=True)


@log_pipeline_stage("full_pipeline")
def run_full_pipeline() -> dict:
    """
    Run the complete pipeline: scraping → AI processing.

    Returns:
        Dict with pipeline results summary
    """
    logger.info("Starting full pipeline")

    # Step 1: Scrape and store
    stored_items = scrape_and_store()

    # Step 2: AI processing
    generated_cards = run_ai_pipeline()

    result = {
        "scraped_count": len(stored_items),
        "cards_generated": len(generated_cards),
        "timestamp": datetime.now().isoformat(),
    }

    logger.info("Full pipeline completed", **result)
    return result
