export interface SourceContent {
  id: number;
  platform: string;
  url: string;
  title: string;
  cleaned_text: string;
  author: string | null;
  published_at: string;
  interaction_count: number;
  scraped_at: string;
}

export interface HotCard {
  id: number;
  title: string;
  summary: string;
  category: string;
  credibility: string;
  sources: string[];
  image_url: string | null;
  hotness_score: number;
  generated_at: string;
}

export interface CardsResponse {
  success: boolean;
  data: {
    cards: HotCard[];
    total: number;
    has_more: boolean;
  };
  timestamp: string;
}

export interface CategoriesResponse {
  success: boolean;
  data: {
    categories: CategoryInfo[];
  };
  timestamp: string;
}

export interface CategoryInfo {
  name: string;
  count: number;
}

export interface DetailPage {
  id: number;
  card: {
    title: string;
    credibility: string;
    generated_at: string;
  };
  overview: string;
  viewpoints: Viewpoint[];
  timeline: TimelineEvent[];
  sources: Source[];
}

export interface Viewpoint {
  source: string;
  view: string;
  citation: string;
}

export interface TimelineEvent {
  time: string;
  event: string;
  citation: string;
}

export interface Source {
  id: number;
  platform: string;
  title: string;
  url: string;
  author: string;
  published_at: string;
}

export interface HealthResponse {
  success: boolean;
  data: {
    status: string;
    version: string;
    timestamp: string;
    components: {
      database: string;
      scheduler: string;
      sources: Record<string, string>;
      api_usage: {
        calls_today: number;
        limit: number;
        remaining: number;
      };
    };
  };
  timestamp: string;
}
