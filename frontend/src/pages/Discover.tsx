import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { pollingService } from '../services/polling';
import type { HotCard as HotCardType, CategoryInfo } from '../types';
import CardFeed from '../components/CardFeed';
import ChannelTabs from '../components/ChannelTabs';
import Notification from '../components/Notification';

const Discover: React.FC = () => {
  const navigate = useNavigate();
  const [cards, setCards] = useState<HotCardType[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [category, setCategory] = useState('全部');
  const [categories, setCategories] = useState<CategoryInfo[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [newCardCount, setNewCardCount] = useState(0);
  const observerRef = useRef<IntersectionObserver | null>(null);
  const loadMoreRef = useRef<HTMLDivElement>(null);

  const fetchCards = useCallback(async (reset = true) => {
    try {
      if (reset) {
        setLoading(true);
        setError(null);
      }
      const offset = reset ? 0 : cards.length;
      const response = await api.getCards(category, 20, offset);
      if (response.success) {
        if (reset) {
          setCards(response.data.cards);
        } else {
          setCards(prev => [...prev, ...response.data.cards]);
        }
        setHasMore(response.data.has_more);
      } else {
        setError('加载失败，请稍后重试');
      }
    } catch (err) {
      setError('加载失败，请稍后重试');
      console.error('Failed to fetch cards:', err);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [category, cards.length]);

  const fetchCategories = useCallback(async () => {
    try {
      const response = await api.getCategories();
      if (response.success) {
        setCategories(response.data.categories);
      }
    } catch (err) {
      console.error('Failed to fetch categories:', err);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchCards(true);
    fetchCategories();
  }, [category]);

  // Start polling for new cards
  useEffect(() => {
    pollingService.start((newCards) => {
      setNewCardCount(prev => prev + newCards.length);
    }, category);

    return () => {
      pollingService.stop();
    };
  }, [category]);

  // Infinite scroll observer
  useEffect(() => {
    if (observerRef.current) {
      observerRef.current.disconnect();
    }

    observerRef.current = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loadingMore && !loading) {
          setLoadingMore(true);
          fetchCards(false);
        }
      },
      { threshold: 0.1 }
    );

    if (loadMoreRef.current) {
      observerRef.current.observe(loadMoreRef.current);
    }

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [hasMore, loadingMore, loading]);

  const handleCardClick = (card: HotCardType) => {
    navigate(`/detail/${card.id}`);
  };

  const handleCategoryChange = (newCategory: string) => {
    setCategory(newCategory);
    setNewCardCount(0);
    pollingService.setCategory(newCategory);
  };

  const handleRefreshNew = () => {
    setNewCardCount(0);
    fetchCards(true);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* New cards notification */}
      <Notification
        count={newCardCount}
        onRefresh={handleRefreshNew}
        onDismiss={() => setNewCardCount(0)}
      />

      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 py-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
                2026世界杯热点监控
              </h1>
              <p className="text-sm text-gray-500 mt-1">
                AI智能聚合 · 实时追踪世界杯最新动态
              </p>
            </div>
            <button
              onClick={() => fetchCards(true)}
              disabled={loading}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors text-sm font-medium"
            >
              {loading ? '加载中...' : '刷新'}
            </button>
          </div>

          {/* Channel Tabs */}
          {categories.length > 0 && (
            <ChannelTabs
              categories={categories}
              activeCategory={category}
              onCategoryChange={handleCategoryChange}
            />
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-6">
        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Card Feed */}
        <CardFeed
          cards={cards}
          onCardClick={handleCardClick}
          loading={loading && cards.length === 0}
        />

        {/* Load more trigger */}
        {hasMore && (
          <div ref={loadMoreRef} className="py-8 text-center">
            {loadingMore && (
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
            )}
          </div>
        )}

        {/* End of list */}
        {!hasMore && cards.length > 0 && !loading && (
          <div className="py-8 text-center text-gray-400 text-sm">
            — 已加载全部内容 —
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-8">
        <div className="max-w-6xl mx-auto px-4 py-6 text-center text-gray-500 text-sm">
          World Cup Hot Topics Monitor · Powered by AI
        </div>
      </footer>
    </div>
  );
};

export default Discover;
