import React, { useState } from 'react';
import { X, Info, Sparkles } from 'lucide-react';
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
  const [showTooltip, setShowTooltip] = useState(false);

  if (!isOpen) return null;

  const handleSave = () => {
    onSave();
    onClose();
  };

  // Mock recommended interests based on current selections
  const getRecommendedInterests = () => {
    const recommendations: { [key: string]: string[] } = {
      'technology': ['artificial intelligence', 'cybersecurity', 'blockchain', 'cloud computing'],
      'sports': ['fitness', 'nutrition', 'athletics', 'sports psychology'],
      'politics': ['international relations', 'economics', 'public policy', 'geopolitics'],
      'science': ['astronomy', 'biology', 'physics', 'environmental science'],
      'business': ['entrepreneurship', 'startups', 'finance', 'marketing'],
      'health': ['mental health', 'wellness', 'nutrition', 'medical research'],
    };

    const recommended = new Set<string>();
    interests.forEach(interest => {
      const key = interest.toLowerCase();
      if (recommendations[key]) {
        recommendations[key].forEach(rec => {
          if (!interests.includes(rec)) {
            recommended.add(rec);
          }
        });
      }
    });

    return Array.from(recommended).slice(0, 4);
  };

  const recommendedInterests = interests.length > 0 ? getRecommendedInterests() : [];

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

              {/* AI Recommendations */}
              {recommendedInterests.length > 0 && (
                <div className="pt-4 border-t border-gray-200">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Sparkles className="text-purple-600" size={20} />
                      <h3 className="text-lg font-semibold text-gray-900">
                        Recommended For You
                      </h3>
                    </div>
                    <div className="relative">
                      <button
                        onMouseEnter={() => setShowTooltip(true)}
                        onMouseLeave={() => setShowTooltip(false)}
                        className="p-1 rounded-full hover:bg-gray-100 transition-colors"
                      >
                        <Info size={18} className="text-gray-500" />
                      </button>
                      {showTooltip && (
                        <div className="absolute right-0 top-8 w-80 z-50 bg-gray-900 text-white text-xs rounded-lg p-4 shadow-xl">
                          <div className="space-y-2">
                            <p className="font-semibold text-sm">How it works:</p>
                            <p>
                              In production, this would use:
                            </p>
                            <ul className="list-disc list-inside space-y-1 ml-2">
                              <li><strong>K-Means Clustering:</strong> Group similar user preferences</li>
                              <li><strong>Collaborative Filtering:</strong> Find users with similar interests</li>
                              <li><strong>Content-Based Filtering:</strong> Analyze topic relationships using embeddings (Word2Vec/BERT)</li>
                              <li><strong>Matrix Factorization:</strong> Decompose user-interest interactions</li>
                              <li><strong>Neural Networks:</strong> Deep learning models for personalized recommendations</li>
                            </ul>
                            <p className="pt-2 border-t border-gray-700">
                              This mockup uses simple rule-based suggestions.
                            </p>
                          </div>
                          <div className="absolute -top-2 right-4 w-4 h-4 bg-gray-900 transform rotate-45"></div>
                        </div>
                      )}
                    </div>
                  </div>
                  <p className="text-gray-600 mb-4 text-sm">
                    Based on your interests, you might also like:
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {recommendedInterests.map((interest) => (
                      <button
                        key={interest}
                        onClick={() => onInterestsChange([...interests, interest])}
                        className="px-4 py-2 bg-purple-50 hover:bg-purple-100 text-purple-700 rounded-full text-sm font-medium transition-colors border border-purple-200 hover:border-purple-300 flex items-center gap-2"
                      >
                        <span>+</span>
                        <span>{interest}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

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
