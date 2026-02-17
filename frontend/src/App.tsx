import { useState, useEffect } from 'react'
import { useMigrationStore } from './store/migrationStore'
import RepoConfiguration from './components/RepoConfiguration'
import BranchSelection from './components/BranchSelection'
import { FeatureTable } from './components/FeatureTable'
import { AnalysisProgress } from './components/AnalysisProgress'
import { useAnalysisStream } from './hooks/useAnalysisStream'
import { api } from './services/api'
import type { FeatureSummary } from './types'
import { Play, Table, ChevronRight, Loader2, CheckCircle } from 'lucide-react'

function App() {
  const { step, sessionId } = useMigrationStore();
  const [analysisStatus, setAnalysisStatus] = useState<string | null>(null);
  const [features, setFeatures] = useState<FeatureSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([]);

  const [processingMigration, setProcessingMigration] = useState(false);

  // WebSocket stream hook — only enabled when analysis is running
  const stream = useAnalysisStream(
    sessionId,
    analysisStatus === 'ANALYZING'
  );

  // When WebSocket reports completion, fetch features
  useEffect(() => {
    if (stream.isComplete && sessionId) {
      setAnalysisStatus('ANALYZED');
      setLoading(false);
      api.getFeatureSummaries(sessionId).then(featureData => {
        setFeatures(featureData);
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

      // Step 8: Create Migration Branch
      const run = await api.createMigrationRun(sessionId);

      alert(`Migration branch created: ${run.branch_name}\nTarget Repo: ${run.target_repo_url}\nBase Branch: ${run.base_branch}\nMigration Run ID: ${run.run_id}`);
      // In a real app, we'd move to Step 4 (Conversion Progress)
    } catch (err: any) {
      console.error("Migration process failed", err);
      alert("Failed to start migration: " + (err.response?.data?.detail || err.message));
    } finally {
      setProcessingMigration(false);
    }
  }

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
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-7xl mx-auto">
        <header className="text-center mb-12">
          <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight">
            QE Framework Migration Tool
          </h1>
          <p className="mt-2 text-lg text-gray-600">
            Seamlessly migrate your automation frameworks with AI-driven analysis.
          </p>
        </header>

        <main>
          {step === 1 && <RepoConfiguration />}
          {step === 2 && <BranchSelection />}

          {step === 3 && (
            <div className="space-y-8">
              {analysisStatus !== 'ANALYZED' ? (
                <div className="space-y-6">
                  {/* Show trigger button if not started or failed */}
                  {(!analysisStatus || analysisStatus === 'FAILED') && (
                    <div className="text-center bg-white p-12 rounded-2xl shadow-sm border border-gray-200">
                      <div className="bg-green-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
                        <CheckCircle className="w-8 h-8 text-green-600" />
                      </div>
                      <h2 className="text-2xl font-bold text-gray-900">
                        Session Initiated!
                      </h2>
                      <p className="text-gray-600 mt-2 max-w-md mx-auto">
                        The source and target repositories are ready. Click below to start the deep analysis of your test suite.
                      </p>
                      <button
                        onClick={handleAnalyze}
                        disabled={loading}
                        className="mt-8 flex items-center gap-2 px-8 py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-bold rounded-xl shadow-lg transition-all transform hover:scale-105 mx-auto"
                      >
                        {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />}
                        {loading ? "Starting..." : analysisStatus === 'FAILED' ? "Retry Analysis" : "Analyze Source Code"}
                      </button>
                    </div>
                  )}

                  {/* Live progress panel during analysis */}
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
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                      <Table className="w-5 h-5 text-blue-600" />
                      Detected Features
                    </h2>

                    <button
                      onClick={handleProcessMigration}
                      disabled={selectedFeatures.length === 0 || processingMigration}
                      className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-300 text-white font-bold rounded-xl shadow-md transition-all disabled:cursor-not-allowed"
                    >
                      {processingMigration ? <Loader2 className="w-5 h-5 animate-spin" /> : null}
                      {processingMigration ? "Preparing Branch..." : `Process Migration (${selectedFeatures.length})`}
                      {!processingMigration && <ChevronRight className="w-5 h-5" />}
                    </button>
                  </div>

                  <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-200">
                    <FeatureTable
                      sessionId={sessionId!}
                      features={features}
                      selectedFeatures={selectedFeatures}
                      onToggleFeature={toggleFeature}
                      onToggleAll={toggleAll}
                    />
                  </div>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

export default App
