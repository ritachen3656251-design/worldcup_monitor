import React from 'react';
import type { Viewpoint, TimelineEvent, Source } from '../types';

interface DetailPageProps {
  overview: string;
  viewpoints: Viewpoint[];
  timeline: TimelineEvent[];
  sources: Source[];
  cardTitle: string;
  credibility: string;
  onCitationClick?: (sourceId: number) => void;
}

const credibilityColors: Record<string, string> = {
  '可信': 'bg-green-100 text-green-800 border-green-200',
  '待确认': 'bg-yellow-100 text-yellow-800 border-yellow-200',
  '传闻': 'bg-red-100 text-red-800 border-red-200',
};

export const DetailPageComponent: React.FC<DetailPageProps> = ({
  overview,
  viewpoints,
  timeline,
  sources,
  cardTitle,
  credibility,
  onCitationClick,
}) => {
  const handleCitationClick = (citation: string) => {
    const match = citation.match(/\[(\d+)\]/);
    if (match && onCitationClick) {
      onCitationClick(parseInt(match[1]));
    }
    // Scroll to sources section
    const sourcesEl = document.getElementById('sources-section');
    if (sourcesEl) {
      sourcesEl.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Title & Credibility */}
      <div className="mb-6">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-3">
          {cardTitle}
        </h1>
        <span
          className={`text-sm px-3 py-1 rounded-full border font-medium ${
            credibilityColors[credibility] || 'bg-gray-100 text-gray-600 border-gray-200'
          }`}
        >
          {credibility}
        </span>
      </div>

      {/* Overview Section */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
          <span className="w-1 h-5 bg-blue-500 rounded-full" />
          事件概述
        </h2>
        <div className="bg-blue-50 rounded-xl p-5 text-gray-700 leading-relaxed">
          {overview}
        </div>
      </section>

      {/* Viewpoints Section */}
      {viewpoints.length > 0 && (
        <section className="mb-8">
          <h2 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <span className="w-1 h-5 bg-purple-500 rounded-full" />
            各方观点
          </h2>
          <div className="space-y-3">
            {viewpoints.map((vp, idx) => (
              <div
                key={idx}
                className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm"
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-sm font-medium text-purple-700 bg-purple-50 px-2 py-0.5 rounded">
                    {vp.source}
                  </span>
                  <button
                    onClick={() => handleCitationClick(vp.citation)}
                    className="text-xs text-blue-500 hover:text-blue-700 cursor-pointer font-mono"
                  >
                    {vp.citation}
                  </button>
                </div>
                <p className="text-gray-700 leading-relaxed">{vp.view}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Timeline Section */}
      {timeline.length > 0 && (
        <section className="mb-8">
          <h2 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <span className="w-1 h-5 bg-teal-500 rounded-full" />
            事件时间线
          </h2>
          <div className="relative pl-6 border-l-2 border-teal-200 space-y-4">
            {timeline.map((event, idx) => (
              <div key={idx} className="relative">
                <div className="absolute -left-[25px] w-3 h-3 bg-teal-500 rounded-full border-2 border-white" />
                <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs text-teal-600 font-medium">
                      {event.time}
                    </span>
                    <button
                      onClick={() => handleCitationClick(event.citation)}
                      className="text-xs text-blue-500 hover:text-blue-700 cursor-pointer font-mono"
                    >
                      {event.citation}
                    </button>
                  </div>
                  <p className="text-gray-700">{event.event}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Sources Section */}
      <section id="sources-section" className="mb-8">
        <h2 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
          <span className="w-1 h-5 bg-orange-500 rounded-full" />
          信息来源
        </h2>
        <div className="flex gap-3 overflow-x-auto pb-2">
          {sources.map((source) => (
            <a
              key={source.id}
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-shrink-0 bg-white rounded-xl border border-gray-100 p-4 shadow-sm hover:shadow-md transition-shadow w-64"
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-mono text-blue-500">[{source.id}]</span>
                <span className="text-xs font-medium text-gray-500">{source.platform}</span>
              </div>
              <h4 className="text-sm font-medium text-gray-900 line-clamp-2 mb-1">
                {source.title}
              </h4>
              <div className="flex items-center justify-between text-xs text-gray-400">
                <span>{source.author}</span>
                <span>{source.published_at}</span>
              </div>
            </a>
          ))}
        </div>
      </section>
    </div>
  );
};

export default DetailPageComponent;
