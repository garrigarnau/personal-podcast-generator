import React from 'react';
import { PodcastLength, PodcastTone, PodcastPreferences } from '../types/podcast';
import { Clock, MessageCircle } from 'lucide-react';

interface CustomizationPanelProps {
  preferences: PodcastPreferences;
  onChange: (preferences: PodcastPreferences) => void;
  disabled?: boolean;
}

const LENGTH_OPTIONS: { value: PodcastLength; label: string; duration: string; description: string }[] = [
  { value: 'short', label: 'Short', duration: '~5 min', description: 'Quick overview' },
  { value: 'medium', label: 'Medium', duration: '~10 min', description: 'Balanced coverage' },
  { value: 'long', label: 'Long', duration: '~15 min', description: 'Deep dive' },
];

const TONE_OPTIONS: { value: PodcastTone; label: string; description: string }[] = [
  { value: 'professional', label: 'Professional', description: 'Formal and informative' },
  { value: 'conversational', label: 'Conversational', description: 'Engaging and natural' },
  { value: 'casual', label: 'Casual', description: 'Relaxed and friendly' },
  { value: 'educational', label: 'Educational', description: 'Teaching and explanatory' },
];

export const CustomizationPanel: React.FC<CustomizationPanelProps> = ({
  preferences,
  onChange,
  disabled = false,
}) => {
  const handleLengthChange = (length: PodcastLength) => {
    onChange({ ...preferences, length });
  };

  const handleToneChange = (tone: PodcastTone) => {
    onChange({ ...preferences, tone });
  };

  return (
    <div className="space-y-6">
      {/* Length Selection */}
      <div className="space-y-3">
        <div className="flex items-center space-x-2">
          <Clock className="text-gray-600" size={20} />
          <h3 className="text-lg font-semibold text-gray-800">
            Podcast Length
          </h3>
        </div>
        <div className="grid grid-cols-3 gap-3">
          {LENGTH_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => handleLengthChange(option.value)}
              disabled={disabled}
              className={`
                p-4 rounded-lg border-2 transition-all duration-200
                ${
                  preferences.length === option.value
                    ? 'border-blue-600 bg-blue-50 shadow-md scale-105'
                    : 'border-gray-300 bg-white hover:border-blue-400 hover:bg-gray-50'
                }
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer active:scale-95'}
              `}
            >
              <div className="text-left">
                <div className="font-semibold text-gray-800">
                  {option.label}
                </div>
                <div className="text-sm text-blue-600 font-medium mt-1">
                  {option.duration}
                </div>
                <div className="text-xs text-gray-600 mt-1">
                  {option.description}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Tone Selection */}
      <div className="space-y-3">
        <div className="flex items-center space-x-2">
          <MessageCircle className="text-gray-600" size={20} />
          <h3 className="text-lg font-semibold text-gray-800">
            Podcast Tone
          </h3>
        </div>
        <div className="grid grid-cols-2 gap-3">
          {TONE_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => handleToneChange(option.value)}
              disabled={disabled}
              className={`
                p-4 rounded-lg border-2 transition-all duration-200
                ${
                  preferences.tone === option.value
                    ? 'border-blue-600 bg-blue-50 shadow-md scale-105'
                    : 'border-gray-300 bg-white hover:border-blue-400 hover:bg-gray-50'
                }
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer active:scale-95'}
              `}
            >
              <div className="text-left">
                <div className="font-semibold text-gray-800">
                  {option.label}
                </div>
                <div className="text-xs text-gray-600 mt-1">
                  {option.description}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Visual Summary */}
      <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
        <div className="flex items-center justify-between text-sm">
          <div>
            <span className="text-gray-600">You'll get a </span>
            <span className="font-semibold text-blue-700">
              {preferences.length}
            </span>
            <span className="text-gray-600"> podcast with a </span>
            <span className="font-semibold text-blue-700">
              {preferences.tone}
            </span>
            <span className="text-gray-600"> tone</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CustomizationPanel;
