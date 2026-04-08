import React, { useEffect, useState } from 'react';
import { api, SourceContent } from '../services/api';
import RawList from '../components/RawList';

const Discover: React.FC = () => {
  const [items, setItems] = useState<SourceContent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCards = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getCards(20);
      setItems(data);
    } catch (err) {
      setError('加载失败，请稍后重试');
      console.error('Failed to fetch cards:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCards();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">
            ⚽ 2026世界杯热点监控
          </h1>
          <p className="text-gray-600 mt-2">
            实时追踪世界杯最新动态
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Refresh Button */}
        <div className="mb-6 flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-800">
            最新内容
          </h2>
          <button
            onClick={fetchCards}
            disabled={loading}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? '加载中...' : '刷新'}
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Loading State */}
        {loading && items.length === 0 && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            <p className="mt-4 text-gray-600">加载中...</p>
          </div>
        )}

        {/* Content List */}
        {!loading && items.length === 0 && !error && (
          <div className="text-center py-12 text-gray-500">
            暂无内容，请稍后刷新
          </div>
        )}

        {items.length > 0 && <RawList items={items} />}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-6xl mx-auto px-4 py-6 text-center text-gray-600 text-sm">
          World Cup Hot Topics Monitor - Powered by AI
        </div>
      </footer>
    </div>
  );
};

export default Discover;
