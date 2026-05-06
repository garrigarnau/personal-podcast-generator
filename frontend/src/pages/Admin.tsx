import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Home as HomeIcon, RefreshCw } from 'lucide-react';
import KPICards from '../components/KPICards';
import VolumeChart from '../components/VolumeChart';
import HealthMonitor from '../components/HealthMonitor';
import { AdminStats } from '../types/admin';
import { getAdminStats, ApiError } from '../services/api';

// Mock data for fallback (matches live data structure)
const MOCK_DATA: AdminStats = {
  kpis: {
    totalPodcasts: 28,
    avgLatency: 120.0,
    totalApiCost: 14.25,
    successRate: 0.679,
    totalFirecrawlScrapes: 420,
    totalFirecrawlCost: 2.10,
    totalOpenaiCost: 1.18,
    totalElevenlabsCost: 10.97,
    costBreakdown: {
      openai: 1.18,
      elevenlabs: 10.97,
      firecrawl: 2.10,
    },
    latencyBreakdown: {
      newsFetch: 35000.0,
      scriptGeneration: 40000.0,
      audioGeneration: 45000.0,
    },
  },
  volumeData: [
    { date: '2026-04-28', count: 3, avgLatency: 115.2 },
    { date: '2026-04-29', count: 5, avgLatency: 122.1 },
    { date: '2026-04-30', count: 4, avgLatency: 118.5 },
    { date: '2026-05-01', count: 2, avgLatency: 108.9 },
    { date: '2026-05-02', count: 6, avgLatency: 126.2 },
    { date: '2026-05-03', count: 4, avgLatency: 120.4 },
    { date: '2026-05-04', count: 4, avgLatency: 114.7 },
  ],
  recentTasks: [
    {
      id: 'task-001',
      status: 'completed',
      createdAt: new Date(Date.now() - 15 * 60000).toISOString(),
      completedAt: new Date(Date.now() - 13 * 60000).toISOString(),
      duration: 120,
      interests: ['AI', 'Technology', 'Space'],
      firecrawlScrapes: 15,
      firecrawlCost: 0.075,
      tokensUsed: 5000,
      elevenlabsChars: 3750,
      openaiCost: 0.042,
      elevenlabsCost: 1.125,
      totalCost: 1.242,
    },
    {
      id: 'task-002',
      status: 'completed',
      createdAt: new Date(Date.now() - 45 * 60000).toISOString(),
      completedAt: new Date(Date.now() - 43 * 60000).toISOString(),
      duration: 115,
      interests: ['Climate', 'Environment'],
      firecrawlScrapes: 15,
      firecrawlCost: 0.075,
      tokensUsed: 4800,
      elevenlabsChars: 3600,
      openaiCost: 0.040,
      elevenlabsCost: 1.080,
      totalCost: 1.195,
    },
    {
      id: 'task-003',
      status: 'failed',
      createdAt: new Date(Date.now() - 75 * 60000).toISOString(),
      duration: 30,
      error: 'API timeout',
      interests: ['Politics', 'Economy'],
      firecrawlScrapes: 10,
      firecrawlCost: 0.050,
      tokensUsed: 1234,
    },
    {
      id: 'task-004',
      status: 'processing',
      createdAt: new Date(Date.now() - 5 * 60000).toISOString(),
      interests: ['Health', 'Fitness', 'Nutrition'],
    },
    {
      id: 'task-005',
      status: 'completed',
      createdAt: new Date(Date.now() - 120 * 60000).toISOString(),
      completedAt: new Date(Date.now() - 118 * 60000).toISOString(),
      duration: 125,
      interests: ['Science', 'Research'],
      firecrawlScrapes: 15,
      firecrawlCost: 0.075,
      tokensUsed: 5200,
      elevenlabsChars: 3900,
      openaiCost: 0.044,
      elevenlabsCost: 1.170,
      totalCost: 1.289,
    },
  ],
};

export const Admin: React.FC = () => {
  const [stats, setStats] = useState<AdminStats>(MOCK_DATA);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [useMockData, setUseMockData] = useState(false);

  // Fetch admin stats
  const fetchStats = useCallback(async () => {
    if (useMockData) {
      // Use mock data for development
      setStats(MOCK_DATA);
      setLastUpdated(new Date());
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await getAdminStats(7); // Last 7 days
      setStats(data);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Failed to fetch admin stats:', err);

      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to load dashboard data. Using mock data instead.');
      }

      // Fallback to mock data on error
      setStats(MOCK_DATA);
    } finally {
      setLoading(false);
    }
  }, [useMockData]);

  // Initial load
  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      if (!useMockData) {
        fetchStats();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [fetchStats, useMockData]);

  const handleRefresh = () => {
    fetchStats();
  };

  const toggleMockData = () => {
    setUseMockData(!useMockData);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Admin Dashboard
              </h1>
              <p className="text-gray-600 mt-1">
                Monitor podcast generation metrics and system health
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={toggleMockData}
                className={`
                  px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200
                  ${
                    useMockData
                      ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200'
                      : 'bg-green-100 text-green-800 hover:bg-green-200'
                  }
                `}
              >
                {useMockData ? 'Mock Data' : 'Live Data'}
              </button>
              <button
                onClick={handleRefresh}
                disabled={loading}
                className={`
                  flex items-center space-x-2 px-4 py-2 rounded-lg
                  transition-all duration-200
                  ${
                    loading
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700 active:scale-95'
                  }
                `}
              >
                <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
                <span>Refresh</span>
              </button>
              <Link
                to="/"
                className="
                  flex items-center space-x-2 px-4 py-2 rounded-lg
                  bg-gray-100 hover:bg-gray-200 text-gray-700
                  transition-colors duration-200
                "
              >
                <HomeIcon size={20} />
                <span>Home</span>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Alert */}
        {error && !useMockData && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg animate-fade-in">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}

        {/* Last Updated Info */}
        <div className="mb-6 flex items-center justify-between">
          <div className="text-sm text-gray-600">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </div>
          {useMockData && (
            <div className="text-sm text-yellow-700 bg-yellow-50 px-3 py-1 rounded-full">
              Displaying mock data for development
            </div>
          )}
        </div>

        <div className="space-y-8">
          {/* KPI Cards */}
          <KPICards data={stats.kpis} loading={loading} />

          {/* Volume Chart */}
          <VolumeChart data={stats.volumeData} loading={loading} />

          {/* Health Monitor */}
          <HealthMonitor tasks={stats.recentTasks} loading={loading} />

          {/* Additional Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* System Status */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                System Status
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">API Status</span>
                  <span className="px-3 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                    Operational
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Database</span>
                  <span className="px-3 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                    Connected
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Queue</span>
                  <span className="px-3 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                    Healthy
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Storage</span>
                  <span className="px-3 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                    Available
                  </span>
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Quick Stats
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Avg Cost per Podcast</span>
                  <span className="text-sm font-semibold text-gray-900">
                    ${stats.kpis.totalPodcasts > 0 ? (stats.kpis.totalApiCost / stats.kpis.totalPodcasts).toFixed(2) : '0.00'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Today's Volume</span>
                  <span className="text-sm font-semibold text-gray-900">
                    {stats.volumeData[stats.volumeData.length - 1]?.count || 0}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Failed Tasks</span>
                  <span className="text-sm font-semibold text-gray-900">
                    {stats.recentTasks.filter((t) => t.status === 'failed').length}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Fastest Generation</span>
                  <span className="text-sm font-semibold text-gray-900">
                    {(() => {
                      const durations = stats.recentTasks
                        .filter((t) => t.duration && t.duration > 0)
                        .map((t) => t.duration!);
                      return durations.length > 0 ? `${Math.min(...durations).toFixed(0)}s` : 'N/A';
                    })()}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Admin;
