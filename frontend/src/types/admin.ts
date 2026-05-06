export interface KPIData {
  totalPodcasts: number;
  avgLatency: number; // Average processing time in seconds
  totalApiCost: number; // Total cost in USD
  successRate: number; // Percentage of successful podcast generations
  totalFirecrawlScrapes?: number; // Total Firecrawl scrapes performed
  totalFirecrawlCost?: number; // Total Firecrawl cost in USD
  totalOpenaiCost?: number; // Total OpenAI cost in USD (actual tracked)
  totalElevenlabsCost?: number; // Total ElevenLabs cost in USD (actual tracked)
  costBreakdown?: {
    openai: number;
    elevenlabs: number;
    firecrawl: number;
  };
  latencyBreakdown?: {
    newsFetch: number; // Average news fetch latency in ms
    scriptGeneration: number; // Average script generation latency in ms
    audioGeneration: number; // Average audio generation latency in ms
  };
}

export interface VolumeDataPoint {
  date: string; // ISO date string
  count: number; // Number of podcasts generated
  avgLatency: number; // Average latency for that day
}

export interface TaskHealth {
  id: string;
  title?: string; // AI-generated podcast title
  status: 'completed' | 'failed' | 'processing' | 'pending';
  createdAt: string;
  completedAt?: string;
  duration?: number; // Duration in seconds
  error?: string;
  interests: string[];
  firecrawlSearches?: number; // Number of Firecrawl searches
  firecrawlScrapes?: number; // Number of Firecrawl scrapes
  tokensUsed?: number; // OpenAI tokens used
  elevenlabsChars?: number; // ElevenLabs characters used
  openaiCost?: number; // Actual OpenAI cost in USD
  elevenlabsCost?: number; // Actual ElevenLabs cost in USD
  firecrawlCost?: number; // Actual Firecrawl cost in USD
  totalCost?: number; // Total cost in USD
}

export interface AdminStats {
  kpis: KPIData;
  volumeData: VolumeDataPoint[];
  recentTasks: TaskHealth[];
}

export interface CostBreakdown {
  firecrawl: number;
  openai: number;
  elevenlabs: number;
  total: number;
}

export interface LatencyBreakdown {
  newsCollection: number;
  scriptGeneration: number;
  audioGeneration: number;
  total: number;
}
