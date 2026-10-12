import { useState } from 'react';
import { Copy, Check, ExternalLink, FileText, Globe, RefreshCw, Clock } from 'lucide-react';
import type { SummarizeSuccessResponse } from '../services/api';

interface SummaryCardProps {
  data: SummarizeSuccessResponse;
  durationMs?: number | null;
  onReset: () => void;
}

export const SummaryCard: React.FC<SummaryCardProps> = ({ data, durationMs, onReset }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(data.summary);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard', err);
    }
  };

  const wordCount = data.summary.trim().split(/\s+/).filter(Boolean).length;

  return (
    <article className="w-full surface-card rounded-xl p-5 sm:p-7 shadow-lg">
      {/* Card Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3.5 pb-4 border-b border-slate-800/80">
        <div>
          <h2 className="text-sm font-semibold text-slate-100 tracking-tight">
            Synthesized Summary
          </h2>
          <div className="flex items-center space-x-1.5 text-xs text-slate-400 mt-1">
            <Globe className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <span className="text-slate-500">Source:</span>
            <a
              href={data.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-cyan-400 hover:text-cyan-300 hover:underline flex items-center space-x-1 font-medium"
            >
              <span className="truncate max-w-[200px] sm:max-w-xs">{data.source_host}</span>
              <ExternalLink className="w-3 h-3 ml-0.5 inline shrink-0" />
            </a>
          </div>
        </div>

        {/* Extraction Metrics */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span
            title={
              data.extracted_characters > 20000
                ? "Total readable characters parsed (AI input bounded to 20,000 maximum)"
                : "Total readable characters parsed from webpage"
            }
            className="px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-slate-400 flex items-center space-x-1.5 font-mono text-[11px]"
          >
            <FileText className="w-3 h-3 text-cyan-500" />
            <span>
              {data.extracted_characters.toLocaleString()} chars
              {data.extracted_characters > 20000 && (
                <span className="text-slate-500 font-sans text-[10px] ml-1">(20k cap)</span>
              )}
            </span>
          </span>
          <span className="px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-slate-400 font-mono text-[11px]">
            ~{wordCount} words
          </span>
          {typeof durationMs === 'number' && (
            <span
              title="Total client request round-trip time"
              className="px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-slate-400 flex items-center space-x-1.5 font-mono text-[11px]"
            >
              <Clock className="w-3 h-3 text-slate-500" />
              <span>{(durationMs / 1000).toFixed(1)}s round-trip</span>
            </span>
          )}
        </div>
      </div>

      {/* Summary Body (Safe plain text rendering) */}
      <div className="py-5">
        <p className="text-slate-200 text-sm sm:text-[15px] leading-relaxed tracking-normal font-normal whitespace-pre-wrap selection:bg-cyan-500/20">
          {data.summary}
        </p>
      </div>

      {/* Action Footer */}
      <div className="pt-4 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs">
        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-200 hover:text-white border border-slate-700/80 transition-colors cursor-pointer"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400 font-medium">Copied to clipboard</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5 text-slate-400" />
              <span>Copy summary</span>
            </>
          )}
        </button>

        <button
          type="button"
          onClick={onReset}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-900 transition-colors cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Summarize another URL</span>
        </button>
      </div>
    </article>
  );
};
