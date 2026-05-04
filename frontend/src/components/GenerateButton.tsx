import React from 'react';
import { Loader2, Sparkles } from 'lucide-react';

interface GenerateButtonProps {
  onClick: () => void;
  disabled?: boolean;
  loading?: boolean;
  loadingText?: string;
  className?: string;
}

export const GenerateButton: React.FC<GenerateButtonProps> = ({
  onClick,
  disabled = false,
  loading = false,
  loadingText = 'Generating your podcast...',
  className = '',
}) => {
  const isDisabled = disabled || loading;

  return (
    <button
      onClick={onClick}
      disabled={isDisabled}
      className={`
        relative w-full py-4 px-6 rounded-lg font-semibold text-lg
        transition-all duration-300 transform
        ${
          isDisabled
            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
            : 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700 active:scale-95 shadow-lg hover:shadow-xl'
        }
        ${className}
      `}
    >
      <div className="flex items-center justify-center space-x-2">
        {loading ? (
          <>
            <Loader2 className="animate-spin" size={24} />
            <span>{loadingText}</span>
          </>
        ) : (
          <>
            <Sparkles size={24} />
            <span>Generate Podcast</span>
          </>
        )}
      </div>

      {/* Animated gradient border effect when not disabled */}
      {!isDisabled && !loading && (
        <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-blue-400 to-indigo-400 opacity-0 group-hover:opacity-100 -z-10 blur transition-opacity duration-300" />
      )}
    </button>
  );
};

export default GenerateButton;
