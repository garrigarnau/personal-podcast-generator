import React, { useState, KeyboardEvent } from 'react';
import { X, Plus } from 'lucide-react';

interface InterestSelectorProps {
  interests: string[];
  onChange: (interests: string[]) => void;
  maxInterests?: number;
  placeholder?: string;
  disabled?: boolean;
}

export const InterestSelector: React.FC<InterestSelectorProps> = ({
  interests,
  onChange,
  maxInterests = 10,
  placeholder = 'Add interests (e.g., AI, Technology, Space...)',
  disabled = false,
}) => {
  const [inputValue, setInputValue] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && inputValue.trim()) {
      e.preventDefault();
      addInterest(inputValue.trim());
    }
  };

  const addInterest = (interest: string) => {
    // Validate
    if (!interest) {
      return;
    }

    if (interests.length >= maxInterests) {
      setError(`Maximum ${maxInterests} interests allowed`);
      return;
    }

    if (interests.some((i) => i.toLowerCase() === interest.toLowerCase())) {
      setError('Interest already added');
      return;
    }

    if (interest.length < 2) {
      setError('Interest must be at least 2 characters');
      return;
    }

    if (interest.length > 50) {
      setError('Interest must be less than 50 characters');
      return;
    }

    // Add interest
    onChange([...interests, interest]);
    setInputValue('');
    setError(null);
  };

  const removeInterest = (index: number) => {
    onChange(interests.filter((_, i) => i !== index));
    setError(null);
  };

  const handleAddClick = () => {
    if (inputValue.trim()) {
      addInterest(inputValue.trim());
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center space-x-2">
        <div className="flex-1 relative">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => {
              setInputValue(e.target.value);
              setError(null);
            }}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled || interests.length >= maxInterests}
            className={`
              w-full px-4 py-3 border rounded-lg
              focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
              transition-all duration-200
              ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'}
              ${error ? 'border-red-400' : 'border-gray-300'}
            `}
            maxLength={50}
          />
        </div>
        <button
          type="button"
          onClick={handleAddClick}
          disabled={disabled || !inputValue.trim() || interests.length >= maxInterests}
          className={`
            p-3 rounded-lg transition-all duration-200
            ${
              disabled || !inputValue.trim() || interests.length >= maxInterests
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700 active:scale-95'
            }
          `}
          aria-label="Add interest"
        >
          <Plus size={20} />
        </button>
      </div>

      {error && (
        <p className="text-sm text-red-600 animate-fade-in">{error}</p>
      )}

      {interests.length > 0 && (
        <div className="flex flex-wrap gap-2 animate-fade-in">
          {interests.map((interest, index) => (
            <div
              key={index}
              className="
                flex items-center space-x-2 px-3 py-2 bg-blue-100 text-blue-800
                rounded-full text-sm font-medium
                transition-all duration-200 hover:bg-blue-200
                animate-scale-in
              "
            >
              <span>{interest}</span>
              <button
                type="button"
                onClick={() => removeInterest(index)}
                disabled={disabled}
                className={`
                  rounded-full transition-colors duration-200
                  ${disabled ? 'cursor-not-allowed' : 'hover:bg-blue-300'}
                `}
                aria-label={`Remove ${interest}`}
              >
                <X size={16} />
              </button>
            </div>
          ))}
        </div>
      )}

      <p className="text-sm text-gray-500">
        {interests.length}/{maxInterests} interests added
      </p>
    </div>
  );
};

export default InterestSelector;
