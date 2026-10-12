import { useState } from 'react';
import { Header } from './components/Header';
import { UrlForm } from './components/UrlForm';
import { SummaryCard } from './components/SummaryCard';
import { ErrorBanner } from './components/ErrorBanner';
import { summarizeUrl } from './services/api';
import type { SummarizeSuccessResponse } from './services/api';
import { Shield, Cpu, Zap, Loader2 } from 'lucide-react';

export function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [summaryData, setSummaryData] = useState<SummarizeSuccessResponse | null>(null);
  const [errorState, setErrorState] = useState<{ message: string; code?: string } | null>(null);
  const [lastSubmittedUrl, setLastSubmittedUrl] = useState<string>('');
  const [requestDurationMs, setRequestDurationMs] = useState<number | null>(null);

  const handleSummarize = async (url: string) => {
    setSummaryData(null);
    setErrorState(null);
    setRequestDurationMs(null);
    setIsLoading(true);
    setLastSubmittedUrl(url);

    const startTime = performance.now();
    try {
      const result = await summarizeUrl(url);
      const elapsed = Math.round(performance.now() - startTime);
      setRequestDurationMs(elapsed);
      setSummaryData(result);
    } catch (err: any) {
      setErrorState({
        message: err.message || 'An unexpected error occurred while summarizing the webpage.',
        code: err.code || 'UNKNOWN_ERROR',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setSummaryData(null);
    setErrorState(null);
    setRequestDurationMs(null);
    setLastSubmittedUrl('');
  };

  return (
    <div className="min-h-screen bg-subtle-canvas text-slate-100 flex flex-col font-sans">
      {/* Product Header */}
      <Header />

      {/* Main Workspace */}
      <main className="flex-1 max-w-3xl w-full mx-auto px-4 py-8 sm:py-12 flex flex-col items-center">
        {/* Workspace Introduction */}
        <div className="text-center max-w-xl mx-auto mb-7">
          <h1 className="font-heading font-semibold text-2xl sm:text-3xl text-slate-100 tracking-tight">
            Webpage Summarization Workspace
          </h1>
          <p className="mt-2 text-slate-400 text-xs sm:text-sm leading-relaxed">
            Extract readable content, strip layout noise, and generate high-density objective summaries from public URLs.
          </p>
        </div>

        {/* Primary Input Workspace Card */}
        <div className="w-full mb-6">
          <UrlForm onSubmit={handleSummarize} isLoading={isLoading} />
        </div>

        {/* Loading State Feedback (Indeterminate state without fabricated progressive stages) */}
        {isLoading && (
          <div className="w-full surface-card rounded-xl p-8 flex flex-col items-center justify-center text-center my-2">
            <Loader2 className="w-6 h-6 text-cyan-500 animate-spin mb-3" />
            <h2 className="text-sm font-medium text-slate-200">Processing Webpage Content</h2>
            <p className="mt-1 text-xs text-slate-400 max-w-sm leading-relaxed">
              Safely fetching HTML, extracting readable text, and generating AI summary...
            </p>
          </div>
        )}

        {/* Actionable Error Banner */}
        {errorState && !isLoading && (
          <div className="w-full mb-6">
            <ErrorBanner
              message={errorState.message}
              code={errorState.code}
              onRetry={lastSubmittedUrl ? () => handleSummarize(lastSubmittedUrl) : undefined}
            />
          </div>
        )}

        {/* Formatted Summary Result Card */}
        {summaryData && !isLoading && (
          <div className="w-full mb-8">
            <SummaryCard data={summaryData} durationMs={requestDurationMs} onReset={handleReset} />
          </div>
        )}

        {/* Supporting Architecture Specifications */}
        <section aria-label="System Specifications" className="w-full grid grid-cols-1 sm:grid-cols-3 gap-2.5 sm:gap-3.5 mt-6 sm:mt-8 pt-6 sm:pt-8 border-t border-slate-800/80">
          <div className="py-2.5 px-3 sm:p-3.5 rounded-lg bg-slate-900/50 border border-slate-800/80 text-left">
            <div className="flex items-center space-x-2 text-cyan-400 mb-1.5 sm:mb-2">
              <Shield className="w-4 h-4 shrink-0" />
              <h3 className="text-xs font-semibold text-slate-200">SSRF Protection</h3>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Pre-request DNS resolution checks and socket pinning against private/loopback IPs.
            </p>
          </div>

          <div className="py-2.5 px-3 sm:p-3.5 rounded-lg bg-slate-900/50 border border-slate-800/80 text-left">
            <div className="flex items-center space-x-2 text-indigo-400 mb-1.5 sm:mb-2">
              <Cpu className="w-4 h-4 shrink-0" />
              <h3 className="text-xs font-semibold text-slate-200">Clean Extraction</h3>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              HTML parser removes non-content tags and boilerplate; caps AI input at 20k characters.
            </p>
          </div>

          <div className="py-2.5 px-3 sm:p-3.5 rounded-lg bg-slate-900/50 border border-slate-800/80 text-left">
            <div className="flex items-center space-x-2 text-emerald-400 mb-1.5 sm:mb-2">
              <Zap className="w-4 h-4 shrink-0" />
              <h3 className="text-xs font-semibold text-slate-200">Free-Tier Operation</h3>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Architected to run within free-tier quotas on Render, Vercel, and Gemini/Groq APIs.
            </p>
          </div>
        </section>
      </main>

      {/* Product Footer */}
      <footer className="w-full py-4 px-4 sm:px-6 border-t border-slate-800/80 text-xs text-slate-500 bg-slate-950/50">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2.5">
          <span>WebSage AI • Demonstrator Project v1.2</span>
          <div className="flex items-center space-x-4">
            <a
              href="https://websage-ai.onrender.com/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-slate-300 transition-colors"
            >
              API Docs
            </a>
            <a
              href="https://github.com/shlok926/WebSage-AI"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-slate-300 transition-colors"
            >
              GitHub Repository
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
