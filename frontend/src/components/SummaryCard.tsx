import { useState } from 'react';
import { Copy, Check, ExternalLink, FileText, Globe, Sparkles, RefreshCw } from 'lucide-react';
import type { SummarizeSuccessResponse } from '../services/api';

interface SummaryCardProps {
  data: SummarizeSuccessResponse;
  onReset: () => void;
}

export const SummaryCard: React.FC<SummaryCardProps> = ({ data, onReset }) => {
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

  const wordCount = data.summary.trim().split(/\s+/).length;

  return (
    <div className="w-full glass-panel rounded-2xl p-6 sm:p-8 shadow-2xl relative overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-300">
      {/* Top subtle glow */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-500 via-indigo-500 to-purple-500" />

      {/* Card Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800/80">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">Generated Summary</h2>
            <div className="flex items-center space-x-2 text-xs text-slate-400 mt-0.5">
              <Globe className="w-3.5 h-3.5 text-slate-500" />
              <span>Source:</span>
              <a
                href={data.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-cyan-400 hover:text-cyan-300 hover:underline flex items-center space-x-1"
              >
                <span>{data.source_host}</span>
                <ExternalLink className="w-3 h-3 ml-0.5 inline" />
              </a>
            </div>
          </div>
        </div>

        {/* Action badges */}
        <div className="flex items-center space-x-2">
          <span className="text-xs px-2.5 py-1 rounded-md bg-slate-800/80 border border-slate-700/60 text-slate-300 flex items-center space-x-1">
            <FileText className="w-3 h-3 text-cyan-400" />
            <span>{data.extracted_characters.toLocaleString()} chars parsed</span>
          </span>
          <span className="text-xs px-2.5 py-1 rounded-md bg-slate-800/80 border border-slate-700/60 text-slate-300">
            ~{wordCount} words
          </span>
        </div>
      </div>

      {/* Summary Body */}
      <div className="py-6">
        <p className="text-slate-200 text-sm sm:text-base leading-relaxed tracking-wide font-normal whitespace-pre-line selection:bg-cyan-500/30">
          {data.summary}
        </p>
      </div>

      {/* Card Footer Actions */}
      <div className="pt-4 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs">
        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white border border-slate-700 transition-colors cursor-pointer"
        >
          {copied ? (
            <>
              <Check className="w-4 h-4 text-emerald-400" />
              <span className="text-emerald-400 font-medium">Copied to clipboard</span>
            </>
          ) : (
            <>
              <Copy className="w-4 h-4 text-slate-400" />
              <span>Copy summary</span>
            </>
          )}
        </button>

        <button
          type="button"
          onClick={onReset}
          className="flex items-center space-x-1.5 px-3.5 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800 transition-colors cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Summarize another URL</span>
        </button>
      </div>
    </div>
  );
};
