import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import DetailPageComponent from '../components/DetailPage';
import type { Viewpoint, TimelineEvent, Source } from '../types';

const Detail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<{
    overview: string;
    viewpoints: Viewpoint[];
    timeline: TimelineEvent[];
    sources: Source[];
    card: { title: string; credibility: string; generated_at: string };
  } | null>(null);

  useEffect(() => {
    const fetchDetail = async () => {
      if (!id) return;

      try {
        setLoading(true);
        setError(null);
        const response = await api.getCardDetail(parseInt(id));
        if (response.success) {
          setDetail(response.data);
        } else {
          setError('加载失败，请稍后重试');
        }
      } catch (err) {
        setError('加载失败，请稍后重试');
        console.error('Failed to fetch detail:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDetail();
  }, [id]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center gap-4">
          <button
            onClick={() => navigate('/')}
            className="text-gray-600 hover:text-gray-900 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <h1 className="text-lg font-semibold text-gray-900">
            话题详情
          </h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Loading */}
        {loading && (
          <div className="text-center py-16">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
            <p className="mt-4 text-gray-600">正在生成详情...</p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
            <button
              onClick={() => navigate('/')}
              className="ml-4 text-sm underline hover:no-underline"
            >
              返回首页
            </button>
          </div>
        )}

        {/* Detail Content */}
        {detail && !loading && (
          <DetailPageComponent
            overview={detail.overview}
            viewpoints={detail.viewpoints}
            timeline={detail.timeline}
            sources={detail.sources}
            cardTitle={detail.card.title}
            credibility={detail.card.credibility}
          />
        )}
      </main>
    </div>
  );
};

export default Detail;
