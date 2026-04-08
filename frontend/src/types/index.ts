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
  source_labels: string[];
  image_url: string | null;
  hotness_score: number;
  generated_at: string;
}

export interface DetailPage {
  id: number;
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
