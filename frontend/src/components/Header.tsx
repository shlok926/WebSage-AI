import { ShieldCheck, ExternalLink } from 'lucide-react';

export const Header = () => {
  return (
    <header className="w-full py-3.5 px-4 sm:px-6 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md sticky top-0 z-30">
      <div className="max-w-5xl mx-auto flex items-center justify-between">
        {/* Brand identity */}
        <div className="flex items-center space-x-3">
          <img
            src="/logo.svg"
            alt="WebSage AI logo"
            className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg border border-slate-800/90 object-contain shrink-0"
          />
          <div className="flex items-center space-x-2.5">
            <span className="font-heading font-semibold text-base sm:text-lg tracking-tight text-slate-100">
              WebSage AI
            </span>
            <span className="text-slate-700 hidden sm:inline select-none">/</span>
            <span className="text-xs text-slate-400 hidden sm:inline font-normal">
              Webpage Summarization
            </span>
          </div>
        </div>

        {/* System & Trust Badges */}
        <div className="flex items-center space-x-3 text-xs">
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-slate-900/90 border border-slate-800 text-slate-300">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span className="font-medium text-[11px] sm:text-xs">SSRF Protection</span>
          </div>

          <a
            href="https://websage-ai.onrender.com/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:flex items-center space-x-1 text-[11px] sm:text-xs text-slate-400 hover:text-slate-200 transition-colors px-2 py-1 rounded hover:bg-slate-900"
          >
            <span>API Docs</span>
            <ExternalLink className="w-3 h-3 ml-0.5 text-slate-500" />
          </a>
        </div>
      </div>
    </header>
  );
};
