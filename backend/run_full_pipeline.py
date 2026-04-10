"""Manual pipeline execution with detailed reporting."""
import sys
sys.path.insert(0, ".")

from src.services.pipeline import run_full_pipeline
from src.core.database import get_session, init_db
from src.models.source_content import SourceContent
from src.models.topic_cluster import TopicCluster
from src.models.hot_card import HotCard
from sqlalchemy import func
from collections import defaultdict

print("=" * 80)
print("手动触发完整抓取+AI处理pipeline")
print("=" * 80)

# Initialize database (create tables if not exist)
print("\n初始化数据库...")
init_db()
print("数据库初始化完成")

# Run full pipeline
result = run_full_pipeline()

print("\n" + "=" * 80)
print("Pipeline执行结果")
print("=" * 80)

session = get_session()

# Get statistics
scraped_count = result.get("scraped", 0)
stored_count = result.get("stored", 0)
filtered_count = result.get("filtered", 0)
clusters_count = result.get("clusters", 0)
cards_count = result.get("cards", 0)

print(f"\n基本统计:")
print(f"  抓取: {scraped_count} 条")
print(f"  存储: {stored_count} 条")
print(f"  过滤后: {filtered_count} 条")
print(f"  聚类: {clusters_count} 个")
print(f"  生成卡片: {cards_count} 张")

# Count by platform
hupu_count = session.query(SourceContent).filter(SourceContent.platform == "hupu").count()
dqd_count = session.query(SourceContent).filter(SourceContent.platform == "dongqiudi").count()
bili_count = session.query(SourceContent).filter(SourceContent.platform == "bilibili").count()

print(f"\n按平台统计（数据库总计）:")
print(f"  虎扑: {hupu_count} 条")
print(f"  懂球帝: {dqd_count} 条")
print(f"  B站: {bili_count} 条")
print(f"  总计: {hupu_count + dqd_count + bili_count} 条")

# Get recent clusters
clusters = session.query(TopicCluster).order_by(TopicCluster.clustered_at.desc()).limit(50).all()

# Analyze clusters
cross_source_clusters = []
multi_item_same_source_clusters = []
single_item_clusters = []

for cluster in clusters:
    sources = set(item.platform for item in cluster.sources)
    item_count = len(cluster.sources)

    if len(sources) > 1:
        cross_source_clusters.append(cluster)
    elif item_count > 1:
        multi_item_same_source_clusters.append(cluster)
    else:
        single_item_clusters.append(cluster)

print(f"\n聚类分析（最近50个簇）:")
print(f"  跨源簇: {len(cross_source_clusters)} 个")
print(f"  同源多条簇: {len(multi_item_same_source_clusters)} 个")
print(f"  单条簇: {len(single_item_clusters)} 个")

# Detailed cluster analysis
print("\n" + "=" * 80)
print("详细聚类分析")
print("=" * 80)

if cross_source_clusters:
    print(f"\n跨源簇 ({len(cross_source_clusters)} 个):")
    print("-" * 80)
    for i, cluster in enumerate(cross_source_clusters, 1):
        sources = [item.platform for item in cluster.sources]
        titles = [item.title for item in cluster.sources]
        print(f"\n簇 {i}: {len(cluster.sources)} 条内容")
        print(f"  来源: {', '.join(sources)}")
        print(f"  标题:")
        for j, title in enumerate(titles, 1):
            print(f"    {j}. [{sources[j-1]}] {title}")

if multi_item_same_source_clusters:
    print(f"\n同源多条簇 ({len(multi_item_same_source_clusters)} 个):")
    print("-" * 80)
    for i, cluster in enumerate(multi_item_same_source_clusters, 1):
        platform = cluster.sources[0].platform
        titles = [item.title for item in cluster.sources]
        print(f"\n簇 {i}: {len(cluster.sources)} 条内容 (来源: {platform})")
        print(f"  标题:")
        for j, title in enumerate(titles, 1):
            print(f"    {j}. {title}")

if single_item_clusters:
    print(f"\n单条簇 ({len(single_item_clusters)} 个):")
    print("-" * 80)
    print("  (仅显示前10个)")
    for i, cluster in enumerate(single_item_clusters[:10], 1):
        item = cluster.sources[0]
        print(f"  {i}. [{item.platform}] {item.title}")

print("\n" + "=" * 80)
print("Pipeline执行完成")
print("=" * 80)

session.close()
