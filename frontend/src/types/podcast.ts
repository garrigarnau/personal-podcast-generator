export type PodcastStatus = 'pending' | 'processing' | 'completed' | 'failed';

export type PodcastLength = 'short' | 'medium' | 'long';

export type PodcastTone = 'serious' | 'balanced' | 'casual';

export interface PodcastPreferences {
  length: PodcastLength;
  tone: PodcastTone;
}

export interface Podcast {
  id: string;
  user_id: string;
  status: PodcastStatus;
  audio_url?: string;
  script?: string;
  error_message?: string;
  metadata?: string; // JSON string
  created_at: string;
  updated_at: string;
  // Parsed from metadata
  interests?: string[];
  preferences?: PodcastPreferences;
  duration?: number; // Duration in seconds
}

export interface GeneratePodcastRequest {
  interests: string[];
  preferences: PodcastPreferences;
}

export interface GeneratePodcastResponse {
  podcastId: string;
  status: PodcastStatus;
  message: string;
}

export interface PodcastStatusResponse {
  podcast: Podcast;
}
