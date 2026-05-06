export type PodcastStatus = 'pending' | 'processing' | 'completed' | 'failed';

export type PodcastLength = 'short' | 'medium' | 'long';

export type PodcastTone = 'professional' | 'casual' | 'educational' | 'conversational';

export interface PodcastPreferences {
  length: PodcastLength;
  tone: PodcastTone;
}

export interface ArticleSource {
  title: string;
  source: string;
  url: string;
}

export interface PodcastMetadata {
  topics?: string[];
  sources?: string[];
  articles?: ArticleSource[];
  word_count?: number;
  estimated_duration?: number;
  tone?: string;
  length?: string;
}

export interface Podcast {
  id: string;
  user_id: string;
  title?: string;
  status: PodcastStatus;
  audio_url?: string;
  script?: string;
  error_message?: string;
  metadata?: string; // JSON string
  podcast_metadata?: string; // JSON string (backend alias)
  created_at: string;
  updated_at: string;
  // Parsed from metadata
  interests?: string[];
  preferences?: PodcastPreferences;
  duration?: number; // Duration in seconds
  parsedMetadata?: PodcastMetadata;
}

export interface GeneratePodcastRequest {
  interests: string[];
  tone: string;
  length: number;
  sources?: string[];
}

export interface GeneratePodcastResponse {
  id: string;
  status: PodcastStatus;
  audio_url?: string;
  script?: string;
  error_message?: string;
  progress?: number;
}

export interface PodcastStatusResponse {
  id: string;
  title?: string;
  status: PodcastStatus;
  audio_url?: string;
  script?: string;
  error_message?: string;
  progress?: number;
  metadata?: string;
  podcast_metadata?: string; // Backend alias
}
