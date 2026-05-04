import React from 'react';
import { TaskHealth } from '../types/admin';
import {
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  AlertCircle,
} from 'lucide-react';

interface HealthMonitorProps {
  tasks: TaskHealth[];
  loading?: boolean;
}

const StatusBadge: React.FC<{ status: TaskHealth['status'] }> = ({ status }) => {
  const configs = {
    completed: {
      icon: <CheckCircle size={16} />,
      className: 'bg-green-100 text-green-800',
      label: 'Completed',
    },
    failed: {
      icon: <XCircle size={16} />,
      className: 'bg-red-100 text-red-800',
      label: 'Failed',
    },
    processing: {
      icon: <Loader2 size={16} className="animate-spin" />,
      className: 'bg-blue-100 text-blue-800',
      label: 'Processing',
    },
    pending: {
      icon: <Clock size={16} />,
      className: 'bg-yellow-100 text-yellow-800',
      label: 'Pending',
    },
  };

  const config = configs[status];

  return (
    <div
      className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${config.className}`}
    >
      {config.icon}
      <span>{config.label}</span>
    </div>
  );
};

export const HealthMonitor: React.FC<HealthMonitorProps> = ({
  tasks,
  loading = false,
}) => {
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;

    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;

    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  const formatDuration = (seconds?: number): string => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${seconds.toFixed(1)}s`;

    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <AlertCircle size={24} className="text-purple-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Recent Tasks
            </h3>
            <p className="text-sm text-gray-600">
              Last {tasks.length} podcast generation tasks
            </p>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className="h-20 bg-gray-200 rounded animate-pulse"
            />
          ))}
        </div>
      ) : tasks.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-600 text-lg mb-2">No tasks yet</p>
          <p className="text-gray-500 text-sm">
            Generate your first podcast to see tasks here
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Task ID
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Interests
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Duration
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {tasks.map((task) => (
                <tr
                  key={task.id}
                  className="hover:bg-gray-50 transition-colors duration-150"
                >
                  <td className="px-4 py-4 whitespace-nowrap">
                    <div className="text-sm font-mono text-gray-900">
                      {task.id.substring(0, 8)}...
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex flex-wrap gap-1">
                      {task.interests.slice(0, 3).map((interest, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                        >
                          {interest}
                        </span>
                      ))}
                      {task.interests.length > 3 && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                          +{task.interests.length - 3}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap">
                    <StatusBadge status={task.status} />
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {formatDuration(task.duration)}
                    </div>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {formatDate(task.createdAt)}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Summary Stats */}
      {tasks.length > 0 && !loading && (
        <div className="mt-6 grid grid-cols-4 gap-4 pt-4 border-t border-gray-200">
          <div className="text-center">
            <p className="text-sm text-gray-600">Completed</p>
            <p className="text-2xl font-bold text-green-600">
              {tasks.filter((t) => t.status === 'completed').length}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600">Failed</p>
            <p className="text-2xl font-bold text-red-600">
              {tasks.filter((t) => t.status === 'failed').length}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600">Processing</p>
            <p className="text-2xl font-bold text-blue-600">
              {tasks.filter((t) => t.status === 'processing').length}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600">Pending</p>
            <p className="text-2xl font-bold text-yellow-600">
              {tasks.filter((t) => t.status === 'pending').length}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default HealthMonitor;
