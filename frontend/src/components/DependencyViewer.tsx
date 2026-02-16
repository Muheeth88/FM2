import { useState } from 'react';
import { api } from '../services/api';
import type { AnalysisResponse, JavaFileDependency } from '../types';
import { Loader2, FileCode, Box, ArrowRight, Play } from 'lucide-react';

interface DependencyViewerProps {
    sessionId: string;
    initialData?: AnalysisResponse | null;
}

export const DependencyViewer = ({ sessionId, initialData }: DependencyViewerProps) => {
    const [graph, setGraph] = useState<AnalysisResponse | null>(initialData || null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleAnalyze = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await api.runAnalysis(sessionId);
            setGraph(data);
        } catch (err) {
            setError('Failed to load dependencies');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center p-8 text-gray-600">
                <Loader2 className="animate-spin w-8 h-8 mb-2 text-blue-600" />
                <p>Analyzing Java dependencies...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col items-center gap-4 p-6 text-red-600 bg-red-50 rounded-lg border border-red-200">
                <p className="font-medium">{error}</p>
                <button
                    onClick={handleAnalyze}
                    className="px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-md transition-colors"
                >
                    Retry Analysis
                </button>
            </div>
        );
    }

    if (!graph) {
        return (
            <div className="flex flex-col items-center justify-center py-12 bg-gray-50 rounded-xl border border-dashed border-gray-300">
                <button
                    onClick={handleAnalyze}
                    className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-md transition-all transform hover:scale-105"
                >
                    <Play className="w-5 h-5" />
                    Analyze Source Code
                </button>
                <p className="mt-4 text-gray-500 text-sm">
                    Click to scan the repository for Java dependencies and visualize the project structure.
                </p>
            </div>
        );
    }

    if (graph.status === 'ANALYZING' && !graph.dependency_graph) {
        return (
            <div className="flex flex-col items-center justify-center py-12 bg-blue-50 rounded-xl border border-blue-200">
                <Loader2 className="animate-spin w-8 h-8 mb-4 text-blue-600" />
                <h3 className="text-xl font-semibold text-blue-900">Analysis in Progress</h3>
                <p className="mt-2 text-blue-700 text-center max-w-md">
                    The background analysis task has been triggered. Results will appear here once scanning is complete.
                </p>
                <button
                    onClick={async () => {
                        setLoading(true);
                        try {
                            const data = await api.getFullAnalysis(sessionId);
                            setGraph(data);
                        } catch (err) {
                            setError('Analysis still in progress or failed');
                        } finally {
                            setLoading(false);
                        }
                    }}
                    className="mt-6 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
                >
                    Check Completion
                </button>
            </div>
        );
    }


    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold flex items-center gap-3 text-gray-800">
                <Box className="w-8 h-8 text-blue-600" /> Dependency Graph
            </h2>
            <div className="grid gap-6">
                {graph.dependency_graph && Object.entries(graph.dependency_graph).map(([filePath, data]) => (
                    <div key={filePath} className="border border-gray-200 p-6 rounded-xl bg-white shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex items-center gap-3 font-semibold text-lg text-gray-900 border-b pb-3 mb-3">

                            <FileCode className="w-5 h-5 text-gray-500" />
                            {data.class_name || filePath.split('/').pop()}
                            {data.type !== 'unknown' && (
                                <span className={`px-2 py-0.5 rounded text-xs uppercase font-bold ml-auto
                                   ${data.type === 'test' ? 'bg-orange-100 text-orange-700' : 'bg-blue-100 text-blue-700'}`}>
                                    {data.type}
                                </span>
                            )}
                        </div>
                        <div className="text-sm text-gray-600 mb-2">
                            <span className="font-medium text-gray-500">Package:</span> {data.package || '<default>'}
                        </div>
                        {data.imports.length > 0 ? (
                            <div className="mt-4">
                                <div className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Imports</div>
                                <ul className="text-sm text-gray-600 space-y-1.5 pl-1">
                                    {data.imports.map((imp) => (
                                        <li key={imp} className="flex items-center gap-2 group">
                                            <ArrowRight className="w-3.5 h-3.5 text-gray-300 group-hover:text-blue-500 transition-colors" />
                                            <span className="font-mono text-gray-700">{imp}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        ) : (
                            <div className="text-sm text-gray-400 italic mt-2">No imports detected</div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};
