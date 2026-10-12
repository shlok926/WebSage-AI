import { useState } from 'react';
import type { FormEvent } from 'react';
import { Loader2, ArrowRight, Globe, X, AlertCircle } from 'lucide-react';

interface UrlFormProps {
  onSubmit: (url: string) => void;
  isLoading: boolean;
}

export const UrlForm: React.FC<UrlFormProps> = ({ onSubmit, isLoading }) => {
  const [url, setUrl] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (isLoading) return;
    setValidationError(null);

    const trimmed = url.trim();
    if (!trimmed) {
      setValidationError('Please enter a public webpage URL.');
      return;
    }

    if (!trimmed.startsWith('http://') && !trimmed.startsWith('https://')) {
      setValidationError('URL must begin with http:// or https://');
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

  const sampleUrls = [
    { label: 'Wikipedia Security', url: 'https://en.wikipedia.org/wiki/Computer_security' },
    { label: 'Python AsyncIO Docs', url: 'https://docs.python.org/3/library/asyncio.html' },
  ];

  const isInputEmpty = !url.trim();

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="surface-card rounded-xl p-4 sm:p-5">
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center">
          {/* Input field wrapper */}
          <div className="relative flex-1 flex items-center">
            <div className="absolute left-3.5 text-slate-500 pointer-events-none">
              <Globe className="w-4 h-4 text-cyan-500" />
            </div>

            <input
              id="url-input"
              type="url"
              value={url}
              onChange={(e) => {
                setUrl(e.target.value);
                if (validationError) setValidationError(null);
              }}
              placeholder="https://example.com/article"
              disabled={isLoading}
              autoFocus
              aria-label="Webpage URL to summarize"
              className="w-full pl-10 pr-9 py-2.5 rounded-lg bg-slate-950/80 border border-slate-800 text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/40 focus:border-cyan-500 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            />

            {url && !isLoading && (
              <button
                type="button"
                onClick={handleClear}
                aria-label="Clear URL"
                className="absolute right-2.5 p-1 text-slate-500 hover:text-slate-300 rounded hover:bg-slate-800 transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Primary Submit Button */}
          <button
            id="submit-button"
            type="submit"
            disabled={isLoading || isInputEmpty}
            className={`flex items-center justify-center space-x-2 px-5 py-2.5 rounded-lg font-medium text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500/50 shrink-0 ${
              isLoading
                ? 'bg-cyan-700/90 text-cyan-100 border border-cyan-600/40 cursor-wait shadow-none'
                : isInputEmpty
                ? 'bg-slate-800/90 text-slate-400 border border-slate-700/60 cursor-not-allowed shadow-none'
                : 'bg-cyan-600 hover:bg-cyan-500 active:bg-cyan-700 text-white border border-cyan-500/40 shadow-sm shadow-cyan-950/40 cursor-pointer'
            }`}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-cyan-200" aria-hidden="true" />
                <span>Summarizing...</span>
              </>
            ) : (
              <>
                <span>Summarize</span>
                <ArrowRight
                  className={`w-4 h-4 transition-colors ${
                    isInputEmpty ? 'text-slate-500' : 'text-white'
                  }`}
                  aria-hidden="true"
                />
              </>
            )}
          </button>
        </div>

        {/* Validation Error Message */}
        {validationError && (
          <div className="mt-2.5 flex items-center space-x-1.5 text-xs text-rose-400">
            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
            <span>{validationError}</span>
          </div>
        )}

        {/* Suggested Samples */}
        <div className="mt-3.5 pt-3 border-t border-slate-800/60 flex flex-wrap items-center gap-2 text-xs text-slate-500">
          <span className="text-[11px] font-medium text-slate-500">Sample targets:</span>
          {sampleUrls.map((sample) => (
            <button
              key={sample.label}
              type="button"
              disabled={isLoading}
              onClick={() => {
                setUrl(sample.url);
                setValidationError(null);
              }}
              className="text-[11px] px-2 py-0.5 rounded bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800/80 transition-colors cursor-pointer"
            >
              {sample.label}
            </button>
          ))}
        </div>
      </form>
    </div>
  );
};
