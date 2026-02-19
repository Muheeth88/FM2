import { useState, useEffect } from 'react'
import { useMigrationStore } from './store/migrationStore'
import RepoConfiguration from './components/RepoConfiguration'
import BranchSelection from './components/BranchSelection'
import { FeatureTable } from './components/FeatureTable'
import { AnalysisProgress } from './components/AnalysisProgress'
import { AnalysisMetadata } from './components/AnalysisMetadata'
import { DependencyViewer } from './components/DependencyViewer'
import { useAnalysisStream } from './hooks/useAnalysisStream'
import { api } from './services/api'
import type { FeatureSummary, AnalysisResponse } from './types'
import { Play, Table, ChevronRight, Loader2, BarChart3, Network, ClipboardList } from 'lucide-react'
import { IntentMappingViewer } from './components/IntentMappingViewer'
import { clsx } from 'clsx'

function App() {
  const { step, sessionId, nextStep } = useMigrationStore();
  const [analysisStatus, setAnalysisStatus] = useState<string | null>(null);
  const [features, setFeatures] = useState<FeatureSummary[]>([]);
  const [fullAnalysis, setFullAnalysis] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([]);
  const [processingMigration, setProcessingMigration] = useState(false);
  const [activeTab, setActiveTab] = useState<'features' | 'graph' | 'metadata'>('features');

  // WebSocket stream hook — only enabled when analysis is running
  const stream = useAnalysisStream(
    sessionId,
    analysisStatus === 'ANALYZING'
  );

  // When WebSocket reports completion, fetch features and full analysis
  useEffect(() => {
    if (stream.isComplete && sessionId) {
      setAnalysisStatus('ANALYZED');
      setLoading(false);

      // Fetch both feature summaries and full analysis
      Promise.all([
        api.getFeatureSummaries(sessionId),
        api.getFullAnalysis(sessionId)
      ]).then(([featureData, analysisData]) => {
        setFeatures(featureData);
        setFullAnalysis(analysisData);
        setSelectedFeatures([]);
      });
    }
  }, [stream.isComplete, sessionId]);

  // When WebSocket reports error, stop loading
  useEffect(() => {
    if (stream.error) {
      setAnalysisStatus('FAILED');
      setLoading(false);
    }
  }, [stream.error]);

  const handleAnalyze = async () => {
    if (!sessionId) return;
    setLoading(true);
    setAnalysisStatus('ANALYZING');
    stream.reset();
    try {
      await api.runAnalysis(sessionId);
    } catch (err) {
      console.error("Analysis trigger failed", err);
      setLoading(false);
      setAnalysisStatus(null);
    }
  };

  const handleProcessMigration = async () => {
    if (!sessionId || selectedFeatures.length === 0) return;
    setProcessingMigration(true);
    try {
      // Step 7: Select Features
      await api.selectFeatures(sessionId, selectedFeatures);

      // Step 9: Intent Extraction Deep Analysis
      await api.processIntents(sessionId, selectedFeatures);

      // Transition to Intent Mapping Viewer (Step 4)
      nextStep();
    } catch (err: any) {
      console.error("Intent extraction failed", err);
      alert("Failed to extract intents: " + (err.response?.data?.detail || err.message));
    } finally {
      setProcessingMigration(false);
    }
  }

  const { foundationStatus, setFoundationStatus } = useMigrationStore();

  useEffect(() => {
    if (stream.foundationStatus) {
      setFoundationStatus(stream.foundationStatus);
    }
  }, [stream.foundationStatus]);

  const [bootstrapping, setBootstrapping] = useState(false);

  const handleBootstrap = async () => {
    if (!sessionId) return;
    setBootstrapping(true);
    try {
      await api.bootstrap(sessionId);
      setFoundationStatus('SUCCESS');
      alert("Basic foundation generated successfully!");
    } catch (err: any) {
      console.error("Bootstrap failed", err);
      alert("Failed to generate foundation: " + (err.response?.data?.detail || err.message));
    } finally {
      setBootstrapping(false);
    }
  };

  const toggleFeature = (featureId: string) => {
    setSelectedFeatures(prev =>
      prev.includes(featureId) ? prev.filter(f => f !== featureId) : [...prev, featureId]
    );
  };

  const toggleAll = () => {
    if (selectedFeatures.length === features.length) {
      setSelectedFeatures([]);
    } else {
      setSelectedFeatures(features.map(f => f.feature_id));
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] py-12 px-4 font-sans selection:bg-blue-100 selection:text-blue-900">
      <div className="max-w-7xl mx-auto">
        <header className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-100 text-blue-600 text-sm font-bold mb-4 uppercase tracking-wider">
            Framework Migration 2.0
          </div>
          <h1 className="text-5xl font-black text-gray-900 tracking-tight mb-4">
            QE Automation <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">Migrator</span>
          </h1>
          <p className="max-w-2xl mx-auto text-lg text-gray-500 font-medium">
            AI-powered framework analysis and intelligent code conversion.
            Streamline your transition between testing ecosystems.
          </p>
        </header>

        <main className="space-y-12">
          {step === 1 && <RepoConfiguration />}
          {step === 2 && <BranchSelection />}

          {step === 3 && (
            <div className="space-y-10">
              {analysisStatus !== 'ANALYZED' ? (
                <div className="max-w-3xl mx-auto">
                  {(!analysisStatus || analysisStatus === 'FAILED') && (
                    <div className="text-center bg-white p-12 rounded-[2rem] shadow-xl shadow-gray-200/50 border border-gray-100">
                      <div className="bg-blue-600 w-20 h-20 rounded-3xl flex items-center justify-center mx-auto mb-8 shadow-lg shadow-blue-200 rotate-3">
                        <BarChart3 className="w-10 h-10 text-white" />
                      </div>
                      <h2 className="text-3xl font-black text-gray-900">
                        Ready for Deep Analysis
                      </h2>
                      <p className="text-gray-500 mt-4 text-balanced font-medium">
                        The repositories have been successfully connected. Now we need to scan your codebase to understand dependencies, features, and driver patterns.
                      </p>
                      <button
                        onClick={handleAnalyze}
                        disabled={loading}
                        className="mt-10 flex items-center gap-3 px-10 py-5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-black rounded-2xl shadow-xl shadow-blue-200 transition-all transform hover:scale-[1.02] active:scale-[0.98] mx-auto group"
                      >
                        {loading ? <Loader2 className="w-6 h-6 animate-spin" /> : <Play className="w-6 h-6 fill-current" />}
                        {loading ? "Initializing..." : analysisStatus === 'FAILED' ? "Retry Deep Analysis" : "Start Deep Analysis"}
                      </button>
                    </div>
                  )}

                  {analysisStatus === 'ANALYZING' && (
                    <AnalysisProgress
                      step={stream.step}
                      progress={stream.progress}
                      logs={stream.logs}
                      error={stream.error}
                      trace={stream.trace}
                      isComplete={stream.isComplete}
                      isConnected={stream.isConnected}
                    />
                  )}
                </div>
              ) : (
                <div className="space-y-8 animate-in fade-in duration-700">
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                    <div className="space-y-1">
                      <h2 className="text-3xl font-black text-gray-900 flex items-center gap-3">
                        <ClipboardList className="w-8 h-8 text-blue-600" />
                        Analysis Results
                      </h2>
                      <p className="text-gray-500 font-medium pl-11">Explore detected features and system architecture.</p>
                    </div>

                    <div className="flex items-center gap-4 bg-white p-1.5 rounded-2xl border border-gray-100 shadow-sm">
                      <button
                        onClick={() => setActiveTab('features')}
                        className={clsx(
                          "flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all",
                          activeTab === 'features' ? "bg-blue-600 text-white shadow-lg shadow-blue-200" : "text-gray-500 hover:bg-gray-50"
                        )}
                      >
                        <Table className="w-5 h-5" />
                        Features
                      </button>
                      <button
                        onClick={() => setActiveTab('graph')}
                        className={clsx(
                          "flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all",
                          activeTab === 'graph' ? "bg-blue-600 text-white shadow-lg shadow-blue-200" : "text-gray-500 hover:bg-gray-50"
                        )}
                      >
                        <Network className="w-5 h-5" />
                        Dependencies
                      </button>
                      <button
                        onClick={() => setActiveTab('metadata')}
                        className={clsx(
                          "flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all",
                          activeTab === 'metadata' ? "bg-blue-600 text-white shadow-lg shadow-blue-200" : "text-gray-500 hover:bg-gray-50"
                        )}
                      >
                        <BarChart3 className="w-5 h-5" />
                        Metadata
                      </button>
                    </div>

                    {activeTab === 'features' && (
                      <div className="flex items-center gap-4">
                        {foundationStatus === 'MISSING' && (
                          <button
                            onClick={handleBootstrap}
                            disabled={bootstrapping}
                            className="flex items-center gap-2 px-6 py-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-black rounded-2xl shadow-xl shadow-indigo-100 transition-all transform hover:scale-[1.02] active:scale-[0.98]"
                          >
                            {bootstrapping ? <Loader2 className="w-5 h-5 animate-spin" /> : null}
                            {bootstrapping ? "Generating..." : "Generate Basic Foundation"}
                          </button>
                        )}

                        <button
                          onClick={handleProcessMigration}
                          disabled={selectedFeatures.length === 0 || processingMigration || foundationStatus === 'MISSING'}
                          className="flex items-center gap-3 px-8 py-4 bg-green-600 hover:bg-green-700 disabled:bg-gray-200 text-white font-black rounded-2xl shadow-xl shadow-green-100 transition-all disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-[1.02] active:scale-[0.98]"
                        >
                          {processingMigration ? <Loader2 className="w-5 h-5 animate-spin" /> : null}
                          {processingMigration ? "Extracting Intents..." : `Initiate Migration (${selectedFeatures.length})`}
                          {!processingMigration && <ChevronRight className="w-6 h-6" />}
                        </button>
                      </div>
                    )}
                  </div>

                  <div className="bg-white/50 backdrop-blur-sm p-4 rounded-[2.5rem] border border-gray-100 shadow-sm">
                    {activeTab === 'features' && (
                      <div className="bg-white p-2 rounded-[2rem] shadow-inner">
                        <FeatureTable
                          sessionId={sessionId!}
                          features={features}
                          selectedFeatures={selectedFeatures}
                          onToggleFeature={toggleFeature}
                          onToggleAll={toggleAll}
                        />
                      </div>
                    )}

                    {activeTab === 'graph' && fullAnalysis && (
                      <div className="p-8">
                        <DependencyViewer data={fullAnalysis} />
                      </div>
                    )}

                    {activeTab === 'metadata' && fullAnalysis && (
                      <div className="p-8">
                        <AnalysisMetadata data={fullAnalysis} />
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {step === 4 && <IntentMappingViewer />}
        </main>
      </div>
    </div>
  )
}

export default App
