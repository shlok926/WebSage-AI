import { ShieldCheck, Zap } from 'lucide-react';

export const Header = () => {
  return (
    <header className="w-full py-6 px-4 border-b border-slate-800/80 bg-slate-950/60 backdrop-blur-md sticky top-0 z-20">
      <div className="max-w-5xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <img
            src="/logo.png"
            alt="WebSage AI"
            className="w-10 h-10 rounded-xl object-cover shadow-lg shadow-cyan-500/20 border border-cyan-500/30"
          />
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-heading font-bold text-xl tracking-tight text-white">WebSage</span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                AI v1.2
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">Intelligent, secure public webpage summarizer</p>
          </div>
        </div>

        <div className="flex items-center space-x-3 text-xs">
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span className="font-medium">SSRF Protected</span>
          </div>
          <div className="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-slate-300">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            <span>₹0 Free Tier</span>
          </div>
        </div>
      </div>
    </header>
  );
};
