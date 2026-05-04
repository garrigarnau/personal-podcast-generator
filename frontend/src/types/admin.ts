export interface KPIData {
  totalPodcasts: number;
  avgLatency: number; // Average processing time in seconds
  totalApiCost: number; // Total cost in USD
  successRate: number; // Percentage of successful podcast generations
}

export interface VolumeDataPoint {
  date: string; // ISO date string
  count: number; // Number of podcasts generated
  avgLatency: number; // Average latency for that day
}

export interface TaskHealth {
  id: string;
  status: 'completed' | 'failed' | 'processing' | 'pending';
  createdAt: string;
  completedAt?: string;
  duration?: number; // Duration in seconds
  error?: string;
  interests: string[];
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
