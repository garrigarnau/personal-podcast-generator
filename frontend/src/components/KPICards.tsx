import React from 'react';
import { KPIData } from '../types/admin';
import { TrendingUp, Clock, DollarSign, CheckCircle } from 'lucide-react';

interface KPICardsProps {
  data: KPIData;
  loading?: boolean;
}

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color: string;
  loading?: boolean;
}

const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  subtitle,
  icon,
  color,
  loading = false,
}) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 transition-all duration-200 hover:shadow-lg">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
          {loading ? (
            <div className="h-8 w-24 bg-gray-200 rounded animate-pulse" />
          ) : (
            <p className="text-3xl font-bold text-gray-900 mb-1">{value}</p>
          )}
          {subtitle && (
            <p className="text-xs text-gray-500">{subtitle}</p>
          )}
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          {icon}
        </div>
      </div>
    </div>
  );
};

export const KPICards: React.FC<KPICardsProps> = ({ data, loading = false }) => {
  const formatLatency = (seconds: number): string => {
    if (seconds < 60) {
      return `${seconds.toFixed(1)}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  };

  const formatCost = (cost: number): string => {
    return `$${cost.toFixed(2)}`;
  };

  const formatSuccessRate = (rate: number): string => {
    return `${(rate * 100).toFixed(1)}%`;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <KPICard
        title="Total Podcasts"
        value={loading ? '...' : data.totalPodcasts.toLocaleString()}
        subtitle="All time generated"
        icon={<TrendingUp size={24} className="text-blue-600" />}
        color="bg-blue-100"
        loading={loading}
      />

      <KPICard
        title="Avg Latency"
        value={loading ? '...' : formatLatency(data.avgLatency)}
        subtitle="Processing time"
        icon={<Clock size={24} className="text-green-600" />}
        color="bg-green-100"
        loading={loading}
      />

      <KPICard
        title="Total API Cost"
        value={loading ? '...' : formatCost(data.totalApiCost)}
        subtitle="OpenAI + ElevenLabs + Firecrawl"
        icon={<DollarSign size={24} className="text-yellow-600" />}
        color="bg-yellow-100"
        loading={loading}
      />

      <KPICard
        title="Success Rate"
        value={loading ? '...' : formatSuccessRate(data.successRate)}
        subtitle="Successful generations"
        icon={<CheckCircle size={24} className="text-purple-600" />}
        color="bg-purple-100"
        loading={loading}
      />
    </div>
  );
};

export default KPICards;
