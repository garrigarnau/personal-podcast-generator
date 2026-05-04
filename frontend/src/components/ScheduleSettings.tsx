import React, { useState, useEffect } from 'react';
import { Clock, Save } from 'lucide-react';

interface ScheduleSettingsProps {
  initialSettings: {
    enabled: boolean;
    frequency: string;
    time: string;
    timezone: string;
    days_of_week: number[];
  };
  onSave: (settings: any) => Promise<void>;
}

const DAYS_OF_WEEK = [
  { value: 1, label: 'Mon' },
  { value: 2, label: 'Tue' },
  { value: 3, label: 'Wed' },
  { value: 4, label: 'Thu' },
  { value: 5, label: 'Fri' },
  { value: 6, label: 'Sat' },
  { value: 7, label: 'Sun' },
];

const ScheduleSettings: React.FC<ScheduleSettingsProps> = ({
  initialSettings,
  onSave,
}) => {
  const [enabled, setEnabled] = useState(initialSettings.enabled);
  const [time, setTime] = useState(initialSettings.time);
  const [daysOfWeek, setDaysOfWeek] = useState<number[]>(initialSettings.days_of_week);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setEnabled(initialSettings.enabled);
    setTime(initialSettings.time);
    setDaysOfWeek(initialSettings.days_of_week);
  }, [initialSettings]);

  const toggleDay = (day: number) => {
    if (daysOfWeek.includes(day)) {
      setDaysOfWeek(daysOfWeek.filter((d) => d !== day));
    } else {
      setDaysOfWeek([...daysOfWeek, day].sort());
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      await onSave({
        enabled,
        time,
        days_of_week: daysOfWeek,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (error) {
      console.error('Failed to save schedule settings:', error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Clock size={20} />
          <span>Schedule Settings</span>
        </h2>
      </div>

      <div className="space-y-4">
        {/* Enable/Disable Toggle */}
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-gray-700">
            Automatic Generation
          </label>
          <button
            onClick={() => setEnabled(!enabled)}
            className={`
              relative inline-flex h-6 w-11 items-center rounded-full
              transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
              ${enabled ? 'bg-blue-600' : 'bg-gray-300'}
            `}
          >
            <span
              className={`
                inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                ${enabled ? 'translate-x-6' : 'translate-x-1'}
              `}
            />
          </button>
        </div>

        {/* Time Picker */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Time
          </label>
          <input
            type="time"
            value={time}
            onChange={(e) => setTime(e.target.value)}
            disabled={!enabled}
            className={`
              w-full px-3 py-2 border border-gray-300 rounded-lg
              focus:ring-2 focus:ring-blue-500 focus:border-transparent
              ${!enabled ? 'bg-gray-100 cursor-not-allowed' : ''}
            `}
          />
        </div>

        {/* Days of Week */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Days of Week
          </label>
          <div className="flex gap-2 flex-wrap">
            {DAYS_OF_WEEK.map((day) => (
              <button
                key={day.value}
                onClick={() => toggleDay(day.value)}
                disabled={!enabled}
                className={`
                  px-3 py-2 rounded-lg text-sm font-medium transition-colors
                  ${
                    daysOfWeek.includes(day.value)
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }
                  ${!enabled ? 'opacity-50 cursor-not-allowed' : ''}
                `}
              >
                {day.label}
              </button>
            ))}
          </div>
        </div>

        {/* Save Button */}
        <button
          onClick={handleSave}
          disabled={saving}
          className={`
            w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg
            font-medium transition-all
            ${
              saved
                ? 'bg-green-600 text-white'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }
            ${saving ? 'opacity-70 cursor-not-allowed' : ''}
          `}
        >
          <Save size={18} />
          <span>{saved ? 'Saved!' : saving ? 'Saving...' : 'Save Schedule'}</span>
        </button>

        {enabled && (
          <p className="text-xs text-gray-600 text-center">
            Podcast will be generated {time} on{' '}
            {daysOfWeek.length === 7
              ? 'every day'
              : DAYS_OF_WEEK.filter((d) => daysOfWeek.includes(d.value))
                  .map((d) => d.label)
                  .join(', ')}
          </p>
        )}
      </div>
    </div>
  );
};

export default ScheduleSettings;
