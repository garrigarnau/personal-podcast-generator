import React, { useState } from 'react';
import { FileText, ChevronDown, ChevronUp, Copy, Check, ExternalLink } from 'lucide-react';

interface ScriptLine {
  type: 'speaker' | 'break';
  speaker?: string;
  emotion?: string;
  text?: string;
}

interface ArticleSource {
  title: string;
  source: string;
  url: string;
}

interface ScriptViewerProps {
  script: string;
  isExpanded?: boolean;
  articles?: ArticleSource[];
}

const ScriptViewer: React.FC<ScriptViewerProps> = ({ script, isExpanded: initialExpanded = false, articles }) => {
  const [isExpanded, setIsExpanded] = useState(initialExpanded);
  const [copied, setCopied] = useState(false);

  // Parse script into structured lines
  const parseScript = (scriptText: string): ScriptLine[] => {
    const lines: ScriptLine[] = [];
    const scriptLines = scriptText.split('\n').filter(line => line.trim());

    for (const line of scriptLines) {
      // Check for [BREAK]
      if (line.trim() === '[BREAK]') {
        lines.push({ type: 'break' });
        continue;
      }

      // Parse speaker lines: [SPEAKER](emotion): text
      // or [SPEAKER]: text
      const speakerMatch = line.match(/^\[(\w+)\](?:\s*\(([^)]+)\))?\s*:\s*(.+)$/);

      if (speakerMatch) {
        const [, speaker, emotion, text] = speakerMatch;
        lines.push({
          type: 'speaker',
          speaker: speaker,
          emotion: emotion,
          text: text.trim(),
        });
      }
    }

    return lines;
  };

  const lines = parseScript(script);

  const handleCopy = () => {
    navigator.clipboard.writeText(script);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getSpeakerColor = (speaker: string) => {
    switch (speaker?.toUpperCase()) {
      case 'ALEX':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'SONIA':
        return 'bg-purple-100 text-purple-800 border-purple-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getSpeakerInitial = (speaker: string) => {
    return speaker?.charAt(0).toUpperCase() || '?';
  };

  if (!script) {
    return null;
  }

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden bg-white">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <FileText size={20} className="text-gray-600" />
          <h3 className="font-semibold text-gray-900">Podcast Script</h3>
          <span className="text-xs text-gray-500">
            ({lines.filter(l => l.type === 'speaker').length} lines)
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
            title="Copy script"
          >
            {copied ? (
              <Check size={18} className="text-green-600" />
            ) : (
              <Copy size={18} className="text-gray-600" />
            )}
          </button>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
          >
            {isExpanded ? (
              <ChevronUp size={20} className="text-gray-600" />
            ) : (
              <ChevronDown size={20} className="text-gray-600" />
            )}
          </button>
        </div>
      </div>

      {/* Script Content */}
      {isExpanded && (
        <div className="p-4 max-h-96 overflow-y-auto space-y-3">
          {lines.map((line, index) => {
            if (line.type === 'break') {
              return (
                <div key={index} className="flex items-center gap-2 my-4">
                  <div className="flex-1 h-px bg-gray-300"></div>
                  <span className="text-xs text-gray-500 font-medium">BREAK</span>
                  <div className="flex-1 h-px bg-gray-300"></div>
                </div>
              );
            }

            return (
              <div key={index} className="flex gap-3 items-start">
                {/* Speaker Avatar */}
                <div
                  className={`
                    flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
                    font-bold text-sm border-2
                    ${getSpeakerColor(line.speaker || '')}
                  `}
                >
                  {getSpeakerInitial(line.speaker || '')}
                </div>

                {/* Speaker Content */}
                <div className="flex-1">
                  <div className="flex items-baseline gap-2 mb-1">
                    <span className="font-semibold text-sm text-gray-900">
                      {line.speaker}
                    </span>
                    {line.emotion && (
                      <span className="text-xs text-gray-500 italic">
                        ({line.emotion})
                      </span>
                    )}
                  </div>
                  <p className="text-gray-700 leading-relaxed">
                    {line.text}
                  </p>
                </div>
              </div>
            );
          })}

          {lines.length === 0 && (
            <p className="text-center text-gray-500 py-8">
              No script content available
            </p>
          )}

          {/* Sources Section */}
          {articles && articles.length > 0 && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <ExternalLink size={16} />
                Sources
              </h4>
              <div className="space-y-2">
                {articles.map((article, index) => (
                  <div key={index} className="flex items-start gap-2 text-sm">
                    <span className="text-gray-500 font-medium">{index + 1}.</span>
                    <div className="flex-1">
                      <a
                        href={article.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 hover:underline font-medium"
                      >
                        {article.title}
                      </a>
                      <div className="text-gray-500 text-xs mt-0.5">
                        {article.source}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Collapsed Preview */}
      {!isExpanded && (
        <div className="p-4 text-sm text-gray-600 line-clamp-2">
          {lines.slice(0, 2).map((line, idx) => (
            line.type === 'speaker' && (
              <span key={idx}>
                <strong>{line.speaker}:</strong> {line.text}{' '}
              </span>
            )
          ))}
        </div>
      )}
    </div>
  );
};

export default ScriptViewer;
