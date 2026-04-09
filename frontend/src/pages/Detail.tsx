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
          setError('内容生成失败，请重试');
        }
      } catch (err: any) {
        const msg = err?.response?.data?.detail || '内容加载失败，请重试';
        setError(msg);
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
        {error && !loading && (
          <div className="text-center py-16">
            <div className="text-5xl mb-4">😵</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">{error}</h3>
            <p className="text-gray-500 mb-6">AI正在处理中，请稍后再试</p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={() => { setError(null); setLoading(true); api.getCardDetail(parseInt(id!)).then(r => { if(r.success) setDetail(r.data); else setError('内容生成失败'); }).catch(() => setError('内容加载失败，请重试')).finally(() => setLoading(false)); }}
                className="px-5 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm"
              >
                重试
              </button>
              <button
                onClick={() => navigate('/')}
                className="px-5 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
              >
                返回首页
              </button>
            </div>
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
