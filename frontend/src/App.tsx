import { useState } from 'react';
import { Header } from './components/Header';
import { UrlForm } from './components/UrlForm';
import { SummaryCard } from './components/SummaryCard';
import { ErrorBanner } from './components/ErrorBanner';
import { summarizeUrl } from './services/api';
import type { SummarizeSuccessResponse } from './services/api';
import { Sparkles, Shield, Cpu } from 'lucide-react';

export function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [summaryData, setSummaryData] = useState<SummarizeSuccessResponse | null>(null);
  const [errorState, setErrorState] = useState<{ message: string; code?: string } | null>(null);
  const [lastSubmittedUrl, setLastSubmittedUrl] = useState<string>('');

  const handleSummarize = async (url: string) => {
    // Clear prior results before starting new request
    setSummaryData(null);
    setErrorState(null);
    setIsLoading(true);
    setLastSubmittedUrl(url);

    try {
      const result = await summarizeUrl(url);
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
    setLastSubmittedUrl('');
  };

  return (
    <div className="min-h-screen bg-slate-950 bg-mesh-pattern text-slate-100 flex flex-col">
      {/* Top Navigation */}
      <Header />

      {/* Main Container */}
      <main className="flex-1 max-w-4xl w-full mx-auto px-4 py-10 md:py-16 flex flex-col items-center">
        {/* Hero Section */}
        <div className="text-center max-w-2xl mx-auto mb-10">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-semibold uppercase tracking-wider mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Webpage Summarizer</span>
          </div>

          <h1 className="font-heading font-extrabold text-3xl sm:text-5xl md:text-6xl text-white tracking-tight leading-tight">
            Read the web in <span className="bg-gradient-to-r from-cyan-400 via-sky-300 to-indigo-400 bg-clip-text text-transparent">seconds.</span>
          </h1>

          <p className="mt-4 text-slate-400 text-sm sm:text-base leading-relaxed">
            Enter any public article, documentation, or news URL. WebSage extracts readable text, strips boilerplate, and produces an instant 150-word synthesis.
          </p>
        </div>

        {/* URL Input Form */}
        <div className="w-full max-w-2xl mb-8">
          <UrlForm onSubmit={handleSummarize} isLoading={isLoading} />
        </div>

        {/* Loading Indicator */}
        {isLoading && (
          <div className="w-full max-w-2xl py-12 flex flex-col items-center justify-center text-center animate-in fade-in duration-300">
            <div className="relative">
              <div className="w-16 h-16 rounded-full border-4 border-slate-800 border-t-cyan-500 animate-spin" />
              <div className="absolute inset-0 flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-cyan-400 animate-pulse" />
              </div>
            </div>
            <h3 className="mt-6 text-base font-semibold text-white">Analyzing & Summarizing Webpage</h3>
            <p className="mt-1 text-xs text-slate-400 max-w-sm">
              Fetching public HTML safely, filtering non-content elements, and synthesizing with AI...
            </p>
          </div>
        )}

        {/* Error Banner */}
        {errorState && !isLoading && (
          <div className="w-full max-w-2xl mb-8">
            <ErrorBanner
              message={errorState.message}
              code={errorState.code}
              onRetry={lastSubmittedUrl ? () => handleSummarize(lastSubmittedUrl) : undefined}
            />
          </div>
        )}

        {/* Summary Result Card */}
        {summaryData && !isLoading && (
          <div className="w-full max-w-3xl mb-12">
            <SummaryCard data={summaryData} onReset={handleReset} />
          </div>
        )}

        {/* Feature Highlights Grid */}
        {!summaryData && !isLoading && !errorState && (
          <div className="w-full max-w-3xl grid grid-cols-1 sm:grid-cols-3 gap-4 mt-8 pt-8 border-t border-slate-900">
            <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 text-left">
              <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center text-cyan-400 mb-3">
                <Shield className="w-4 h-4" />
              </div>
              <h4 className="text-xs font-semibold text-white uppercase tracking-wider">SSRF Defenses</h4>
              <p className="mt-1 text-xs text-slate-400 leading-relaxed">
                Pre-request DNS validation, redirect re-checks, and private network range isolation.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 text-left">
              <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400 mb-3">
                <Cpu className="w-4 h-4" />
              </div>
              <h4 className="text-xs font-semibold text-white uppercase tracking-wider">Clean Extraction</h4>
              <p className="mt-1 text-xs text-slate-400 leading-relaxed">
                Strips scripts, styling, ads, and navigation to feed pure text into the summarization model.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 text-left">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400 mb-3">
                <Sparkles className="w-4 h-4" />
              </div>
              <h4 className="text-xs font-semibold text-white uppercase tracking-wider">Zero Required Cost</h4>
              <p className="mt-1 text-xs text-slate-400 leading-relaxed">
                Architected to operate within free tier quotas with predictable bounds and hard spending limits.
              </p>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="w-full py-6 px-4 border-t border-slate-900 text-center text-xs text-slate-500">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>WebSage AI • Demonstrator Project v1.2</span>
          <span>FastAPI • React • TypeScript • Groq LPU</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
