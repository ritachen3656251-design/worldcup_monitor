import React from 'react';

interface ChannelTabsProps {
  categories: { name: string; count: number }[];
  activeCategory: string;
  onCategoryChange: (category: string) => void;
}

export const ChannelTabs: React.FC<ChannelTabsProps> = ({
  categories,
  activeCategory,
  onCategoryChange,
}) => {
  return (
    <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
      {categories.map((cat) => (
        <button
          key={cat.name}
          onClick={() => onCategoryChange(cat.name)}
          className={`
            flex-shrink-0 px-4 py-2 rounded-full text-sm font-medium transition-all
            ${activeCategory === cat.name
              ? 'bg-blue-600 text-white shadow-sm'
              : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
            }
          `}
        >
          {cat.name}
          {cat.count > 0 && (
            <span
              className={`ml-1.5 text-xs ${
                activeCategory === cat.name ? 'text-blue-200' : 'text-gray-400'
              }`}
            >
              {cat.count}
            </span>
          )}
        </button>
      ))}
    </div>
  );
};

export default ChannelTabs;
