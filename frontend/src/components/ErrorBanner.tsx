import { AlertCircle, ShieldAlert, Clock, FileWarning, ZapOff, RefreshCcw } from 'lucide-react';

interface ErrorBannerProps {
  message: string;
  code?: string;
  onRetry?: () => void;
}

export const ErrorBanner = ({ message, code, onRetry }: ErrorBannerProps) => {
  const getIcon = () => {
    switch (code) {
      case 'SSRF_BLOCKED':
        return <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" />;
      case 'UPSTREAM_TIMEOUT':
      case 'AI_TIMEOUT':
        return <Clock className="w-4 h-4 text-amber-400 shrink-0" />;
      case 'UNSUPPORTED_CONTENT':
      case 'INSUFFICIENT_CONTENT':
      case 'PAYLOAD_TOO_LARGE':
        return <FileWarning className="w-4 h-4 text-orange-400 shrink-0" />;
      case 'RATE_LIMIT_EXCEEDED':
        return <ZapOff className="w-4 h-4 text-yellow-400 shrink-0" />;
      default:
        return <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />;
    }
  };

  return (
    <div
      role="alert"
      className="w-full rounded-xl p-4 bg-rose-950/25 border border-rose-800/40 text-slate-200"
    >
      <div className="flex items-start justify-between gap-3.5">
        <div className="flex items-start space-x-3">
          <div className="mt-0.5 p-1 rounded-md bg-rose-500/10 border border-rose-500/20 shrink-0">
            {getIcon()}
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold text-rose-200">Unable to Summarize</span>
              {code && (
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20">
                  {code}
                </span>
              )}
            </div>
            <p className="mt-1 text-xs sm:text-sm text-slate-300 leading-relaxed">{message}</p>
          </div>
        </div>

        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-rose-900/30 hover:bg-rose-900/50 border border-rose-700/40 text-rose-200 text-xs font-medium transition-colors cursor-pointer shrink-0"
          >
            <RefreshCcw className="w-3 h-3" />
            <span>Try again</span>
          </button>
        )}
      </div>
    </div>
  );
};
