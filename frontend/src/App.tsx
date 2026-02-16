import { useState } from 'react'
import { useMigrationStore } from './store/migrationStore'
import RepoConfiguration from './components/RepoConfiguration'
import BranchSelection from './components/BranchSelection'
import { DependencyViewer } from './components/DependencyViewer'
import { FeatureTable } from './components/FeatureTable'
import { api } from './services/api'
import type { AnalysisResponse } from './types'
import { Play, Table, Network, ChevronRight, Loader2 } from 'lucide-react'

function App() {
  const { step, sessionId } = useMigrationStore();
  const [analysisData, setAnalysisData] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'features' | 'dependencies'>('features');
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([]);

  const handleAnalyze = async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const data = await api.runAnalysis(sessionId);
      setAnalysisData(data);
      // Select all features by default
      setSelectedFeatures(data.features.map(f => f.file_path));
    } catch (err) {
      console.error("Analysis failed", err);
    } finally {
      setLoading(false);
    }
  };

  const toggleFeature = (filePath: string) => {
    setSelectedFeatures(prev =>
      prev.includes(filePath) ? prev.filter(f => f !== filePath) : [...prev, filePath]
    );
  };

  const toggleAll = () => {
    if (!analysisData) return;
    if (selectedFeatures.length === analysisData.features.length) {
      setSelectedFeatures([]);
    } else {
      setSelectedFeatures(analysisData.features.map(f => f.file_path));
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
              {!analysisData ? (
                <div className="text-center bg-white p-12 rounded-2xl shadow-sm border border-gray-200">
                  <div className="bg-green-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
                    <CheckCircle className="w-8 h-8 text-green-600" />
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900">Session Initiated!</h2>
                  <p className="text-gray-600 mt-2 max-w-md mx-auto">
                    The source and target repositories are ready. Click below to start the deep analysis of your test suite.
                  </p>
                  <button
                    onClick={handleAnalyze}
                    disabled={loading}
                    className="mt-8 flex items-center gap-2 px-8 py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-bold rounded-xl shadow-lg transition-all transform hover:scale-105 mx-auto"
                  >
                    {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />}
                    {loading ? "Analyzing..." : "Analyze Source Code"}
                  </button>
                </div>
              ) : (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div className="flex bg-gray-200/50 p-1 rounded-xl w-fit">
                      <button
                        onClick={() => setActiveTab('features')}
                        className={clsx(
                          "flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-semibold transition-all",
                          activeTab === 'features' ? "bg-white text-blue-600 shadow-sm" : "text-gray-600 hover:text-gray-900"
                        )}
                      >
                        <Table className="w-4 h-4" /> Features
                      </button>
                      <button
                        onClick={() => setActiveTab('dependencies')}
                        className={clsx(
                          "flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-semibold transition-all",
                          activeTab === 'dependencies' ? "bg-white text-blue-600 shadow-sm" : "text-gray-600 hover:text-gray-900"
                        )}
                      >
                        <Network className="w-4 h-4" /> Dependency Graph
                      </button>
                    </div>

                    <button
                      disabled={selectedFeatures.length === 0}
                      className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-300 text-white font-bold rounded-xl shadow-md transition-all"
                    >
                      Process Migration ({selectedFeatures.length})
                      <ChevronRight className="w-5 h-5" />
                    </button>
                  </div>

                  <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-200">
                    {activeTab === 'features' ? (
                      <FeatureTable
                        features={analysisData.features}
                        selectedFeatures={selectedFeatures}
                        onToggleFeature={toggleFeature}
                        onToggleAll={toggleAll}
                      />
                    ) : (
                      <DependencyViewer sessionId={sessionId!} initialData={analysisData} />
                    )}
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

function CheckCircle({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  );
}

import { clsx } from 'clsx';
export default App
