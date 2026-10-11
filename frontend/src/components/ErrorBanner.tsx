import { AlertCircle, ShieldAlert, Clock, FileWarning, ZapOff, RefreshCcw } from 'lucide-react';

interface ErrorBannerProps {
  message: string;
  code?: string;
  onRetry?: () => void;
}

export const ErrorBanner = ({ message, code, onRetry }: ErrorBannerProps) => {
  // Determine appropriate icon based on error code
  const getIcon = () => {
    switch (code) {
      case 'SSRF_BLOCKED':
        return <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0" />;
      case 'UPSTREAM_TIMEOUT':
      case 'AI_TIMEOUT':
        return <Clock className="w-5 h-5 text-amber-400 shrink-0" />;
      case 'UNSUPPORTED_CONTENT':
      case 'INSUFFICIENT_CONTENT':
        return <FileWarning className="w-5 h-5 text-orange-400 shrink-0" />;
      case 'RATE_LIMIT_EXCEEDED':
        return <ZapOff className="w-5 h-5 text-yellow-400 shrink-0" />;
      default:
        return <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />;
    }
  };

  return (
    <div className="w-full rounded-2xl p-5 bg-rose-950/20 border border-rose-500/20 backdrop-blur-md animate-in fade-in slide-in-from-bottom-2 duration-200">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start space-x-3">
          <div className="mt-0.5 p-1.5 rounded-lg bg-rose-500/10 border border-rose-500/20">
            {getIcon()}
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-semibold text-rose-200">Processing Error</h3>
              {code && (
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20">
                  {code}
                </span>
              )}
            </div>
            <p className="mt-1 text-sm text-slate-300 leading-relaxed">{message}</p>
          </div>
        </div>

        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-rose-900/40 hover:bg-rose-900/60 border border-rose-500/30 text-rose-200 text-xs font-medium transition-colors cursor-pointer shrink-0"
          >
            <RefreshCcw className="w-3 h-3" />
            <span>Try again</span>
          </button>
        )}
      </div>
    </div>
  );
};
