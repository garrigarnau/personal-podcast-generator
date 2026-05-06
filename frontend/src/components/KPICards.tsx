import React from 'react';
import { KPIData } from '../types/admin';
import { TrendingUp, Clock, DollarSign, CheckCircle, Search, Globe, Activity } from 'lucide-react';

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
    <div className="space-y-6">
      {/* Main KPI Cards */}
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
          subtitle="All services combined"
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

      {/* Latency Breakdown & Cost Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Latency Breakdown */}
        {data.latencyBreakdown && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-indigo-100 rounded-lg">
                <Clock size={24} className="text-indigo-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Latency Breakdown</h3>
                <p className="text-xs text-gray-500">Average time per stage</p>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 flex items-center gap-1">
                  News Collection
                  <span className="inline-block w-2 h-2 bg-orange-500 rounded-full" title="Firecrawl API"></span>
                </span>
                {loading ? (
                  <div className="h-6 w-16 bg-gray-200 rounded animate-pulse" />
                ) : (
                  <span className="text-lg font-semibold text-orange-600">
                    {(data.latencyBreakdown.newsFetch / 1000).toFixed(1)}s
                  </span>
                )}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 flex items-center gap-1">
                  Script Generation
                  <span className="inline-block w-2 h-2 bg-blue-500 rounded-full" title="OpenAI API"></span>
                </span>
                {loading ? (
                  <div className="h-6 w-16 bg-gray-200 rounded animate-pulse" />
                ) : (
                  <span className="text-lg font-semibold text-blue-600">
                    {(data.latencyBreakdown.scriptGeneration / 1000).toFixed(1)}s
                  </span>
                )}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 flex items-center gap-1">
                  Audio Generation
                  <span className="inline-block w-2 h-2 bg-purple-500 rounded-full" title="ElevenLabs API"></span>
                </span>
                {loading ? (
                  <div className="h-6 w-16 bg-gray-200 rounded animate-pulse" />
                ) : (
                  <span className="text-lg font-semibold text-purple-600">
                    {(data.latencyBreakdown.audioGeneration / 1000).toFixed(1)}s
                  </span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Cost Breakdown */}
        {data.costBreakdown && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-green-100 rounded-lg">
                <DollarSign size={24} className="text-green-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Cost Breakdown</h3>
                <p className="text-xs text-gray-500">Actual tracked costs by service</p>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 flex items-center gap-1">
                  OpenAI
                  <span className="inline-block w-2 h-2 bg-blue-500 rounded-full" title="Actual tracked cost"></span>
                </span>
                {loading ? (
                  <div className="h-6 w-16 bg-gray-200 rounded animate-pulse" />
                ) : (
                  <span className="text-lg font-semibold text-blue-600">
                    {formatCost(data.costBreakdown.openai)}
                  </span>
                )}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 flex items-center gap-1">
                  ElevenLabs
                  <span className="inline-block w-2 h-2 bg-purple-500 rounded-full" title="Actual tracked cost"></span>
                </span>
                {loading ? (
                  <div className="h-6 w-16 bg-gray-200 rounded animate-pulse" />
                ) : (
                  <span className="text-lg font-semibold text-purple-600">
                    {formatCost(data.costBreakdown.elevenlabs)}
                  </span>
                )}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 flex items-center gap-1">
                  Firecrawl
                  <span className="inline-block w-2 h-2 bg-orange-500 rounded-full" title="Actual tracked cost"></span>
                </span>
                {loading ? (
                  <div className="h-6 w-16 bg-gray-200 rounded animate-pulse" />
                ) : (
                  <span className="text-lg font-semibold text-orange-600">
                    {formatCost(data.costBreakdown.firecrawl)}
                  </span>
                )}
              </div>
              <div className="pt-3 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-gray-700">Total</span>
                  {loading ? (
                    <div className="h-7 w-20 bg-gray-200 rounded animate-pulse" />
                  ) : (
                    <span className="text-xl font-bold text-gray-900">
                      {formatCost(
                        data.costBreakdown.openai +
                        data.costBreakdown.elevenlabs +
                        data.costBreakdown.firecrawl
                      )}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Volume Metrics */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2 bg-teal-100 rounded-lg">
            <Activity size={24} className="text-teal-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Operations Volume</h3>
            <p className="text-xs text-gray-500">Total operations performed</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Articles Scraped */}
          <div className="text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              <span className="inline-block w-3 h-3 bg-orange-500 rounded-full" title="Firecrawl"></span>
              <p className="text-sm font-medium text-gray-600">Articles Scraped</p>
            </div>
            {loading ? (
              <div className="h-10 w-20 bg-gray-200 rounded animate-pulse mx-auto" />
            ) : (
              <p className="text-3xl font-bold text-orange-600">
                {data.totalFirecrawlScrapes?.toLocaleString() || 0}
              </p>
            )}
            <p className="text-xs text-gray-500 mt-1">Firecrawl API</p>
          </div>

          {/* Scripts Generated */}
          <div className="text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              <span className="inline-block w-3 h-3 bg-blue-500 rounded-full" title="OpenAI"></span>
              <p className="text-sm font-medium text-gray-600">Scripts Generated</p>
            </div>
            {loading ? (
              <div className="h-10 w-20 bg-gray-200 rounded animate-pulse mx-auto" />
            ) : (
              <p className="text-3xl font-bold text-blue-600">
                {data.totalPodcasts?.toLocaleString() || 0}
              </p>
            )}
            <p className="text-xs text-gray-500 mt-1">OpenAI API</p>
          </div>

          {/* Audio Generated */}
          <div className="text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              <span className="inline-block w-3 h-3 bg-purple-500 rounded-full" title="ElevenLabs"></span>
              <p className="text-sm font-medium text-gray-600">Audio Generated</p>
            </div>
            {loading ? (
              <div className="h-10 w-20 bg-gray-200 rounded animate-pulse mx-auto" />
            ) : (
              <p className="text-3xl font-bold text-purple-600">
                {data.totalPodcasts?.toLocaleString() || 0}
              </p>
            )}
            <p className="text-xs text-gray-500 mt-1">ElevenLabs API</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KPICards;
