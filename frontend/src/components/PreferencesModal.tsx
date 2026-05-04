import React from 'react';
import { X } from 'lucide-react';
import InterestSelector from './InterestSelector';
import CustomizationPanel from './CustomizationPanel';
import { PodcastPreferences } from '../types/podcast';

interface PreferencesModalProps {
  isOpen: boolean;
  onClose: () => void;
  interests: string[];
  preferences: PodcastPreferences;
  onInterestsChange: (interests: string[]) => void;
  onPreferencesChange: (preferences: PodcastPreferences) => void;
  onSave: () => void;
}

const PreferencesModal: React.FC<PreferencesModalProps> = ({
  isOpen,
  onClose,
  interests,
  preferences,
  onInterestsChange,
  onPreferencesChange,
  onSave,
}) => {
  if (!isOpen) return null;

  const handleSave = () => {
    onSave();
    onClose();
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 overflow-y-auto">
        <div className="flex min-h-full items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-gray-900">Podcast Preferences</h2>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X size={24} />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              {/* Interests */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  Your Interests
                </h3>
                <p className="text-gray-600 mb-4 text-sm">
                  Add topics you'd like to hear about in your daily podcast
                </p>
                <InterestSelector
                  interests={interests}
                  onChange={onInterestsChange}
                />
              </div>

              {/* Customization */}
              <div className="pt-4 border-t border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  Podcast Settings
                </h3>
                <p className="text-gray-600 mb-4 text-sm">
                  Customize the length and tone of your podcast
                </p>
                <CustomizationPanel
                  preferences={preferences}
                  onChange={onPreferencesChange}
                />
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 bg-gray-50">
              <button
                onClick={onClose}
                className="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
              >
                Save Preferences
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default PreferencesModal;
