import React from 'react';
import { Sparkles, Loader } from 'lucide-react';

interface GeneratePodcastSectionProps {
  onGenerate: () => void;
  isGenerating: boolean;
  disabled?: boolean;
}

const GeneratePodcastSection: React.FC<GeneratePodcastSectionProps> = ({
  onGenerate,
  isGenerating,
  disabled,
}) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <h2 className="text-lg font-semibold text-gray-900 mb-3">
        Generate Podcast
      </h2>
      <p className="text-sm text-gray-600 mb-4">
        Create a new personalized podcast based on your current preferences
      </p>
      <button
        onClick={onGenerate}
        disabled={disabled || isGenerating}
        className={`
          w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg
          font-medium transition-all
          ${
            disabled || isGenerating
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 text-white hover:shadow-lg'
          }
        `}
      >
        {isGenerating ? (
          <>
            <Loader className="animate-spin" size={20} />
            <span>Generating...</span>
          </>
        ) : (
          <>
            <Sparkles size={20} />
            <span>Generate Now</span>
          </>
        )}
      </button>
    </div>
  );
};

export default GeneratePodcastSection;
