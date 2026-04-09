import React from 'react';

interface SourceInfo {
  platform: string;
  status: string;
  failure_count: number;
  last_check: string | null;
}

interface SourceStatusProps {
  sources: SourceInfo[];
  backupActive: boolean;
}

const statusColors: Record<string, string> = {
  healthy: 'bg-green-500',
  degraded: 'bg-yellow-500',
  failed: 'bg-red-500',
  unknown: 'bg-gray-400',
};

const statusLabels: Record<string, string> = {
  healthy: '正常',
  degraded: '降级',
  failed: '异常',
  unknown: '未知',
};

const platformNames: Record<string, string> = {
  hupu: '虎扑',
  dongqiudi: '懂球帝',
  bilibili: 'B站',
};

export const SourceStatus: React.FC<SourceStatusProps> = ({ sources, backupActive }) => {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
      <h3 className="text-sm font-semibold text-gray-800 mb-3">数据源状态</h3>
      <div className="space-y-2">
        {sources.map((source) => (
          <div key={source.platform} className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span
                className={`w-2 h-2 rounded-full ${statusColors[source.status] || statusColors.unknown}`}
              />
              <span className="text-sm text-gray-700">
                {platformNames[source.platform] || source.platform}
              </span>
            </div>
            <span className="text-xs text-gray-500">
              {statusLabels[source.status] || source.status}
            </span>
          </div>
        ))}
      </div>
      {backupActive && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <div className="flex items-center gap-2 text-xs text-yellow-600">
            <span className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
            Bing 备用搜索已激活
          </div>
        </div>
      )}
    </div>
  );
};

export default SourceStatus;
