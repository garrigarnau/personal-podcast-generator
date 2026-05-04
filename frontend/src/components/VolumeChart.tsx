import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  TooltipProps,
} from 'recharts';
import { VolumeDataPoint } from '../types/admin';
import { TrendingUp } from 'lucide-react';

interface VolumeChartProps {
  data: VolumeDataPoint[];
  loading?: boolean;
}

// Custom tooltip component
const CustomTooltip: React.FC<TooltipProps<number, string>> = ({
  active,
  payload,
  label,
}) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-4 rounded-lg shadow-lg border border-gray-200">
        <p className="font-semibold text-gray-900 mb-2">{label}</p>
        <p className="text-sm text-blue-600">
          Podcasts: <span className="font-semibold">{payload[0].value}</span>
        </p>
        <p className="text-sm text-green-600">
          Avg Latency: <span className="font-semibold">{payload[1].value}s</span>
        </p>
      </div>
    );
  }
  return null;
};

export const VolumeChart: React.FC<VolumeChartProps> = ({
  data,
  loading = false,
}) => {
  // Format date for display
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  // Prepare chart data
  const chartData = data.map((point) => ({
    date: formatDate(point.date),
    count: point.count,
    avgLatency: parseFloat(point.avgLatency.toFixed(1)),
  }));

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <TrendingUp size={24} className="text-blue-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Daily Podcast Volume
            </h3>
            <p className="text-sm text-gray-600">
              Last {data.length} days of activity
            </p>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="h-80 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading chart data...</p>
          </div>
        </div>
      ) : data.length === 0 ? (
        <div className="h-80 flex items-center justify-center">
          <div className="text-center">
            <p className="text-gray-600 text-lg mb-2">No data available</p>
            <p className="text-gray-500 text-sm">
              Generate some podcasts to see the volume chart
            </p>
          </div>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart
            data={chartData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis
              dataKey="date"
              stroke="#6B7280"
              style={{ fontSize: '12px' }}
            />
            <YAxis
              yAxisId="left"
              stroke="#3B82F6"
              style={{ fontSize: '12px' }}
              label={{
                value: 'Podcasts',
                angle: -90,
                position: 'insideLeft',
                style: { fontSize: '12px', fill: '#6B7280' },
              }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              stroke="#10B981"
              style={{ fontSize: '12px' }}
              label={{
                value: 'Avg Latency (s)',
                angle: 90,
                position: 'insideRight',
                style: { fontSize: '12px', fill: '#6B7280' },
              }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: '14px' }}
              iconType="line"
            />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="count"
              stroke="#3B82F6"
              strokeWidth={2}
              dot={{ fill: '#3B82F6', r: 4 }}
              activeDot={{ r: 6 }}
              name="Podcasts"
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="avgLatency"
              stroke="#10B981"
              strokeWidth={2}
              dot={{ fill: '#10B981', r: 4 }}
              activeDot={{ r: 6 }}
              name="Avg Latency (s)"
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};

export default VolumeChart;
