import { useState } from 'react';
import type { FormEvent } from 'react';
import { Loader2, ArrowRight, Globe, X } from 'lucide-react';

interface UrlFormProps {
  onSubmit: (url: string) => void;
  isLoading: boolean;
}

export const UrlForm: React.FC<UrlFormProps> = ({ onSubmit, isLoading }) => {
  const [url, setUrl] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    const trimmed = url.trim();
    if (!trimmed) {
      setValidationError('Please enter a webpage URL to summarize.');
      return;
    }

    if (!trimmed.startsWith('http://') && !trimmed.startsWith('https://')) {
      setValidationError('URL must start with http:// or https://');
      return;
    }

    if (trimmed.length > 2048) {
      setValidationError('URL exceeds the maximum length of 2,048 characters.');
      return;
    }

    onSubmit(trimmed);
  };

  const handleClear = () => {
    setUrl('');
    setValidationError(null);
  };

  const handleExampleClick = (exampleUrl: string) => {
    setUrl(exampleUrl);
    setValidationError(null);
    onSubmit(exampleUrl);
  };

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative flex items-center">
          <div className="absolute left-4 text-slate-400 pointer-events-none">
            <Globe className="w-5 h-5 text-cyan-400" />
          </div>

          <input
            id="url-input"
            type="url"
            value={url}
            onChange={(e) => {
              setUrl(e.target.value);
              if (validationError) setValidationError(null);
            }}
            placeholder="Paste any public webpage URL (e.g. https://en.wikipedia.org/wiki/Artificial_intelligence)..."
            disabled={isLoading}
            autoFocus
            className="w-full pl-12 pr-32 py-4 rounded-2xl bg-slate-900/90 border border-slate-700/80 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-all text-sm md:text-base shadow-xl disabled:opacity-60 disabled:cursor-not-allowed"
          />

          <div className="absolute right-2 flex items-center space-x-1.5">
            {url && !isLoading && (
              <button
                type="button"
                onClick={handleClear}
                aria-label="Clear URL"
                className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            )}

            <button
              id="submit-button"
              type="submit"
              disabled={isLoading || !url.trim()}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-medium text-sm transition-all shadow-md shadow-cyan-500/20 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:from-cyan-500 disabled:hover:to-blue-600 cursor-pointer"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="hidden sm:inline">Summarizing...</span>
                </>
              ) : (
                <>
                  <span>Summarize</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>

        {validationError && (
          <p className="mt-2 text-xs text-rose-400 flex items-center space-x-1 px-2">
            <span>•</span>
            <span>{validationError}</span>
          </p>
        )}
      </form>

      {/* Suggested quick test links */}
      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-400">
        <span className="text-slate-500">Quick tests:</span>
        <button
          type="button"
          disabled={isLoading}
          onClick={() => handleExampleClick('https://example.com')}
          className="px-2.5 py-1 rounded-lg bg-slate-800/60 hover:bg-slate-800 hover:text-cyan-300 border border-slate-700/50 transition-colors cursor-pointer"
        >
          example.com
        </button>
        <button
          type="button"
          disabled={isLoading}
          onClick={() => handleExampleClick('https://en.wikipedia.org/wiki/Python_(programming_language)')}
          className="px-2.5 py-1 rounded-lg bg-slate-800/60 hover:bg-slate-800 hover:text-cyan-300 border border-slate-700/50 transition-colors cursor-pointer"
        >
          Python Wikipedia
        </button>
      </div>
    </div>
  );
};
