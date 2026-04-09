"""Topic clustering using embeddings and LLM refinement."""
import pickle
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import numpy as np

from src.ai.client import call_qwen_api, parse_llm_response
from src.core.config import get_config
from src.core.logging import get_logger
from src.utils.mock import generate_mock_cluster_judgment

logger = get_logger(__name__)

# Lazy-loaded sentence transformer model
_model = None


class ClusteringDecision(BaseModel):
    """AI output for topic clustering."""
    same_topic: bool
    reason: str = Field(min_length=1, max_length=200)


def _get_embedding_model():
    """
    Lazy-load the sentence-transformers model.
    Uses paraphrase-multilingual-MiniLM-L12-v2 for Chinese text support.
    """
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error("Failed to load embedding model", error=str(e))
            raise
    return _model


def compute_embeddings(texts: List[str]) -> np.ndarray:
    """
    Compute embedding vectors for a list of texts.

    Args:
        texts: List of text strings to embed

    Returns:
        NumPy array of shape (len(texts), embedding_dim)
    """
    config = get_config()

    if config.dry_run.enabled:
        logger.info("[DRY-RUN] Using random embeddings")
        return np.random.randn(len(texts), 384).astype(np.float32)

    model = _get_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return embeddings


def compute_single_embedding(text: str) -> np.ndarray:
    """
    Compute embedding for a single text.

    Args:
        text: Text string to embed

    Returns:
        NumPy array of shape (embedding_dim,)
    """
    embeddings = compute_embeddings([text])
    return embeddings[0]


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.

    Args:
        vec_a: First vector
        vec_b: Second vector

    Returns:
        Cosine similarity score (0.0 to 1.0)
    """
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))


def cluster_by_similarity(
    items: List[Dict[str, Any]],
    threshold: float = 0.8,
) -> List[List[int]]:
    """
    Cluster items by embedding similarity.

    Stage 1 of two-stage clustering: fast embedding-based grouping.

    Args:
        items: List of dicts with 'title' and 'cleaned_text' keys
        threshold: Cosine similarity threshold for clustering (default: 0.8)

    Returns:
        List of clusters, where each cluster is a list of item indices
    """
    if not items:
        return []

    config = get_config()
    effective_threshold = config.clustering.embedding_similarity_threshold

    # Compute embeddings for all items
    texts = [f"{item.get('title', '')} {item.get('cleaned_text', '')[:200]}" for item in items]
    embeddings = compute_embeddings(texts)

    # Build clusters using greedy single-link clustering
    clusters: List[List[int]] = []
    assigned = set()

    for i in range(len(items)):
        if i in assigned:
            continue

        # Start new cluster
        cluster = [i]
        assigned.add(i)

        # Find all items similar to any item in this cluster
        for j in range(i + 1, len(items)):
            if j in assigned:
                continue

            # Check similarity against the first item in cluster (representative)
            sim = cosine_similarity(embeddings[i], embeddings[j])

            if sim >= effective_threshold:
                cluster.append(j)
                assigned.add(j)

        clusters.append(cluster)

    logger.info(
        "Embedding clustering done",
        total_items=len(items),
        clusters_found=len(clusters),
        threshold=effective_threshold,
    )

    return clusters


def _load_clustering_prompt() -> str:
    """Load clustering prompt template from file."""
    prompt_path = Path(__file__).parent.parent.parent / "prompts" / "topic_clustering.txt"
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def refine_with_llm(
    item_a: Dict[str, Any],
    item_b: Dict[str, Any],
) -> Optional[ClusteringDecision]:
    """
    Use LLM to judge whether two items discuss the same topic.

    Stage 2 of two-stage clustering: LLM-based refinement for nuanced cases.

    Args:
        item_a: First item dict with 'title' and 'cleaned_text'
        item_b: Second item dict with 'title' and 'cleaned_text'

    Returns:
        ClusteringDecision with same_topic and reason, or None if failed
    """
    config = get_config()

    # Dry-run mode: return mock data
    if config.dry_run.enabled:
        logger.info("[DRY-RUN] Using mock clustering judgment")
        mock_data = generate_mock_cluster_judgment()
        return ClusteringDecision(**mock_data)

    try:
        # Load and format prompt
        template = _load_clustering_prompt()
        prompt = template.replace("{title_a}", item_a.get("title", ""))
        prompt = prompt.replace("{content_a}", item_a.get("cleaned_text", "")[:300])
        prompt = prompt.replace("{title_b}", item_b.get("title", ""))
        prompt = prompt.replace("{content_b}", item_b.get("cleaned_text", "")[:300])

        # Call Qwen-Turbo (lightweight for yes/no decision)
        model = config.ai.models.get("clustering", "qwen-turbo")
        response = call_qwen_api(prompt, model=model)

        if response is None:
            return None

        result = parse_llm_response(response, ClusteringDecision)
        if result:
            logger.info(
                "LLM clustering judgment",
                same_topic=result.same_topic,
                reason=result.reason,
            )
        return result

    except Exception as e:
        logger.error(
            "LLM clustering refinement failed",
            error=str(e),
            exc_info=True,
        )
        return None


def serialize_embedding(embedding: np.ndarray) -> bytes:
    """Serialize a numpy embedding to bytes for database storage."""
    return pickle.dumps(embedding)


def deserialize_embedding(data: bytes) -> np.ndarray:
    """Deserialize bytes back to a numpy embedding."""
    return pickle.loads(data)
