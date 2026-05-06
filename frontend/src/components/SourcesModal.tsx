import React from 'react';
import { X, ExternalLink, Newspaper } from 'lucide-react';

interface ArticleSource {
  title: string;
  source: string;
  url: string;
}

interface SourcesModalProps {
  isOpen: boolean;
  onClose: () => void;
  articles: ArticleSource[];
}

const SourcesModal: React.FC<SourcesModalProps> = ({ isOpen, onClose, articles }) => {
  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Newspaper size={24} className="text-purple-600" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Article Sources</h2>
                <p className="text-sm text-gray-500 mt-0.5">
                  {articles.length} {articles.length === 1 ? 'article' : 'articles'} used to create this podcast
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label="Close"
            >
              <X size={20} className="text-gray-500" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {articles.length === 0 ? (
              <div className="text-center py-12">
                <Newspaper size={48} className="text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">No sources available for this podcast</p>
                <p className="text-xs text-gray-400 mt-2">
                  Sources are only available for podcasts generated after the latest update
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {articles.map((article, index) => (
                  <div
                    key={index}
                    className="border border-gray-200 rounded-lg p-4 hover:border-purple-300 hover:shadow-sm transition-all"
                  >
                    <div className="flex gap-3">
                      {/* Number Badge */}
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center font-semibold text-sm">
                          {index + 1}
                        </div>
                      </div>

                      {/* Article Info */}
                      <div className="flex-1 min-w-0">
                        <a
                          href={article.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="group flex items-start gap-2 mb-2"
                        >
                          <h3 className="text-base font-medium text-gray-900 group-hover:text-purple-600 transition-colors flex-1">
                            {article.title}
                          </h3>
                          <ExternalLink
                            size={16}
                            className="text-gray-400 group-hover:text-purple-600 transition-colors flex-shrink-0 mt-1"
                          />
                        </a>
                        <div className="flex items-center gap-2">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                            {article.source}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 bg-gray-50">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-lg font-medium transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

export default SourcesModal;
