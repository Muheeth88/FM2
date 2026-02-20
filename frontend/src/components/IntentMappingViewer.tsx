import { useState, useEffect } from 'react';
import {
    Layers,
    Terminal,
    Activity,
    AlertTriangle,
    CheckCircle2,
    ChevronRight,
    Globe,
    GitBranch,
    Hash,
    Cpu,
    ChevronDown,
    Workflow
} from 'lucide-react';
import { api } from '../services/api';
import { useMigrationStore } from '../store/migrationStore';

interface IntentResult {
    feature_id: string;
    feature_name: string;
    intent_hash: string;
    raw_model: string; // JSON string from DB
    normalized_model: string; // JSON string from DB
    enriched_model: string | null; // JSON string from DB
    extraction_version: string;
    llm_used: number;
    validation_status: string;
}

const JsonTree = ({ data, label }: { data: any, label?: string }) => {
    const [isExpanded, setIsExpanded] = useState(true);

    if (typeof data !== 'object' || data === null) {
        return <span className="text-blue-600">{JSON.stringify(data)}</span>;
    }

    return (
        <div className="ml-4">
            {label && (
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="flex items-center gap-1 text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors"
                >
                    {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    {label}
                </button>
            )}
            {isExpanded && (
                <div className="border-l border-gray-200 ml-2 mt-1 space-y-1">
                    {Object.entries(data).map(([key, value]) => (
                        <div key={key} className="pl-4">
                            <span className="text-purple-600 font-medium">{key}:</span>{' '}
                            <JsonTree data={value} />
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

const StepTimeline = ({ model }: { model: any }) => {
    // Combine steps and assertions into a single ordered timeline
    // Note: In a more advanced version, we'd use line numbers to interleave them perfectly
    const actions = (model?.steps || []).map((s: any) => ({ ...s, category: 'action' }));
    const assertions = (model?.assertions || []).map((s: any) => ({ ...s, category: 'assertion' }));

    // For now, we append assertions after steps, or try to sort by line if available
    const allSteps = [...actions, ...assertions];

    if (allSteps.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-12 bg-gray-50 rounded-xl border border-dashed border-gray-200">
                <div className="text-gray-400 italic mb-2">No steps or assertions extracted</div>
                <p className="text-xs text-gray-500 text-center px-8">
                    This might happen if the test uses complex logic that the AST parser couldn't fully map yet.
                </p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {allSteps.map((step: any, index: number) => {
                const isAction = step.category === 'action';
                const actionName = step.action || step.operator || (isAction ? 'Unknown Action' : 'Assertion');

                // Binding: Handle both new 'locator' object and legacy 'target' field
                const locator = step.locator || {};
                const targetValue = locator.field_name || locator.value || step.target?.value || step.target || step.right || '...';
                const strategy = locator.strategy || (step.target?.strategy) || null;

                return (
                    <div key={index} className="flex gap-4 items-start group relative">
                        {index < allSteps.length - 1 && (
                            <div className="absolute left-4 top-10 bottom-0 w-0.5 bg-gray-100 group-hover:bg-blue-100 transition-colors" />
                        )}
                        <div className="flex flex-col items-center z-10">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-all shadow-sm ${isAction
                                ? 'bg-blue-50 border-blue-200 text-blue-600 group-hover:bg-blue-600 group-hover:text-white group-hover:border-blue-600'
                                : 'bg-green-50 border-green-200 text-green-600 group-hover:bg-green-600 group-hover:text-white group-hover:border-green-600'
                                }`}>
                                {index + 1}
                            </div>
                        </div>
                        <div className="flex-1 pt-1">
                            <div className="flex flex-wrap items-center gap-2 mb-2">
                                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${isAction ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'
                                    }`}>
                                    {isAction ? (step.type || 'action') : 'assertion'}
                                </span>
                                <span className="font-bold text-gray-900 capitalize">
                                    {actionName.replace(/_/g, ' ')}
                                </span>
                                <span className="text-gray-400">→</span>
                                <div className="flex items-center gap-1.5">
                                    <span className="text-gray-700 font-mono text-sm font-medium bg-gray-50 px-2 py-0.5 rounded border border-gray-100">
                                        {targetValue}
                                    </span>
                                    {strategy && (
                                        <span className="text-[10px] text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">
                                            via {strategy}
                                        </span>
                                    )}
                                </div>
                            </div>

                            <div className="flex flex-col gap-1.5">
                                {step.source_method && (
                                    <div className="text-[11px] text-gray-500 font-mono flex items-center gap-1.5">
                                        <div className="w-1 h-1 rounded-full bg-gray-300" />
                                        Defined in: <span className="text-blue-600 hover:underline cursor-default">{step.source_method}</span>
                                    </div>
                                )}
                                {step.left && (
                                    <div className="text-[11px] text-amber-600 italic bg-amber-50 px-2 py-1 rounded border border-amber-100 w-fit">
                                        Verifying actual: <span className="font-mono font-bold">{step.left}</span>
                                    </div>
                                )}
                                {locator.class && (
                                    <div className="text-[10px] text-gray-400">
                                        Page Class: {locator.class}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                );
            })}
        </div>
    );
};

export const IntentMappingViewer = ({ autoFetch = true }: { autoFetch?: boolean }) => {
    const { sessionId, repoDetails } = useMigrationStore();
    const [intents, setIntents] = useState<IntentResult[]>([]);
    const [activeFeatureIndex, setActiveFeatureIndex] = useState(0);
    const [activePanel, setActivePanel] = useState<'raw' | 'normalized' | 'enriched'>('normalized');
    const [viewMode, setViewMode] = useState<'timeline' | 'json'>('timeline');
    const [loading, setLoading] = useState(true);
    const [archLoading, setArchLoading] = useState(false);
    const [archResult, setArchResult] = useState<any>(null);

    useEffect(() => {
        if (sessionId) {
            api.getSessionIntents(sessionId).then(data => {
                setIntents(data);
                setLoading(false);
            });
            // Try to load existing architecture analysis IF autoFetch is true
            if (autoFetch) {
                api.getArchitecture(sessionId).then(data => {
                    setArchResult(data);
                }).catch(() => {
                    // Not found, that's fine
                });
            }
        }
    }, [sessionId, autoFetch]);

    const handleAnalyzeArchitecture = async () => {
        if (!sessionId) return;
        setArchLoading(true);
        try {
            const result = await api.analyzeArchitecture(sessionId);
            setArchResult(result);
            alert("Architecture analysis completed successfully!");
        } catch (error) {
            console.error("Architecture analysis failed:", error);
            alert("Failed to analyze architecture. Check console for details.");
        } finally {
            setArchLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-64 bg-white rounded-2xl border border-gray-100">
                <Activity className="w-12 h-12 text-blue-500 animate-spin mb-4" />
                <p className="text-gray-500 font-medium">Loading Intent Mappings...</p>
            </div>
        );
    }

    const safeJsonParse = (str: string | null) => {
        if (!str) return null;
        try {
            return typeof str === 'object' ? str : JSON.parse(str);
        } catch (e) {
            console.error("Failed to parse intent model:", e);
            return null;
        }
    };

    const activeIntent = intents[activeFeatureIndex];
    if (!activeIntent) {
        return (
            <div className="bg-white p-12 rounded-2xl shadow-sm border border-gray-200 text-center">
                <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto mb-4" />
                <h2 className="text-xl font-bold text-gray-900">No Intent Results Found</h2>
                <p className="text-gray-600 mt-2">Finish the analysis and select features to see their intent extraction results.</p>
            </div>
        );
    }

    const currentModel = activePanel === 'raw' ? safeJsonParse(activeIntent.raw_model) :
        activePanel === 'normalized' ? safeJsonParse(activeIntent.normalized_model) :
            safeJsonParse(activeIntent.enriched_model);


    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* 1️⃣ Header Section */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="bg-gray-50 px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-600 rounded-lg text-white">
                            <Workflow size={20} />
                        </div>
                        <h2 className="text-lg font-bold text-gray-900 tracking-tight">🔍 Intent Mapping Viewer</h2>
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            onClick={handleAnalyzeArchitecture}
                            disabled={archLoading}
                            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all border shadow-sm ${archResult
                                ? 'bg-green-50 text-green-700 border-green-200 hover:bg-green-100'
                                : 'bg-white text-blue-600 border-blue-100 hover:border-blue-300'
                                } ${archLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            {archLoading ? (
                                <Activity size={14} className="animate-spin" />
                            ) : archResult ? (
                                <CheckCircle2 size={14} />
                            ) : (
                                <Layers size={14} />
                            )}
                            {archLoading ? 'Analyzing...' : archResult ? 'Architecture Analyzed' : 'Analyze Repository Architecture'}
                        </button>
                        <div className="flex items-center gap-4 text-xs ml-4 border-l pl-4">
                            <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded-full font-semibold border border-blue-200">
                                Extraction: {activeIntent.extraction_version || 'v1'}
                            </span>
                            <span className={`px-2 py-1 rounded-full font-semibold border ${activeIntent.llm_used ? 'bg-purple-100 text-purple-700 border-purple-200' : 'bg-gray-100 text-gray-700 border-gray-200'}`}>
                                LLM Enrichment: {activeIntent.llm_used ? 'YES' : 'NO'}
                            </span>
                        </div>
                    </div>
                </div>

                <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <div className="space-y-3">
                        <div className="flex items-center gap-2 text-gray-500 text-sm">
                            <Hash size={16} />
                            <span className="font-medium">Session ID:</span>
                            <span className="text-gray-900 font-mono text-xs truncate">{sessionId}</span>
                        </div>
                        <div className="flex items-center gap-2 text-gray-500 text-sm">
                            <Globe size={16} />
                            <span className="font-medium">Source Repo:</span>
                            <span className="text-gray-900 truncate max-w-[200px]">{repoDetails.repoUrl}</span>
                        </div>
                    </div>
                    <div className="space-y-3">
                        <div className="flex items-center gap-2 text-gray-500 text-sm">
                            <GitBranch size={16} />
                            <span className="font-medium">Branch:</span>
                            <span className="text-gray-900">{repoDetails.branches?.[0] || 'main'}</span>
                        </div>
                        <div className="flex items-center gap-2 text-gray-500 text-sm">
                            <Layers size={16} />
                            <span className="font-medium">Selected Features:</span>
                            <span className="text-gray-900">{intents.length} features</span>
                        </div>
                    </div>
                    <div className="bg-blue-50 rounded-xl p-4 border border-blue-100 flex flex-col justify-center">
                        <span className="text-blue-700 text-[10px] font-bold uppercase tracking-widest mb-1">Status</span>
                        <div className="flex items-center gap-2 text-blue-900 font-bold">
                            <CheckCircle2 size={18} className="text-blue-600" />
                            Extraction Complete
                        </div>
                    </div>
                </div>
            </div>

            {/* 2️⃣ Feature Tabs */}
            <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
                {intents.map((intent, idx) => (
                    <button
                        key={intent.feature_id}
                        onClick={() => setActiveFeatureIndex(idx)}
                        className={`px-6 py-2 rounded-full font-bold text-sm transition-all whitespace-nowrap shadow-sm border ${activeFeatureIndex === idx
                            ? 'bg-blue-600 text-white border-blue-600 ring-4 ring-blue-50'
                            : 'bg-white text-gray-600 border-gray-200 hover:border-blue-300'
                            }`}
                    >
                        {intent.feature_name}
                    </button>
                ))}
            </div>

            {/* 3️⃣ Controls Panel */}
            <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
                <div className="bg-gray-100 p-1 rounded-xl flex self-start">
                    <button
                        onClick={() => setActivePanel('raw')}
                        className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${activePanel === 'raw' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                            }`}
                    >
                        RAW MODEL
                    </button>
                    <button
                        onClick={() => setActivePanel('normalized')}
                        className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${activePanel === 'normalized' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                            }`}
                    >
                        NORMALIZED
                    </button>
                    <button
                        onClick={() => setActivePanel('enriched')}
                        disabled={!activeIntent.enriched_model}
                        className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${activePanel === 'enriched' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed'
                            }`}
                    >
                        ENRICHED
                    </button>
                </div>

                <div className="bg-gray-100 p-1 rounded-xl flex self-start lg:self-auto">
                    <button
                        onClick={() => setViewMode('timeline')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${viewMode === 'timeline' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                            }`}
                    >
                        <Activity size={14} />
                        TIMELINE
                    </button>
                    <button
                        onClick={() => setViewMode('json')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${viewMode === 'json' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                            }`}
                    >
                        <Terminal size={14} />
                        JSON TREE
                    </button>
                </div>
            </div>

            {/* 4️⃣ Three-Panel View */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                {/* Left Panel — Summary */}
                <div className="lg:col-span-4 space-y-6">
                    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
                        <h3 className="text-sm font-bold text-gray-900 uppercase tracking-widest mb-6 border-b pb-2 flex items-center justify-between">
                            Step Summary
                            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                        </h3>
                        <div className="space-y-5">
                            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl border border-gray-100">
                                <span className="text-gray-600 flex items-center gap-3 font-medium">
                                    <Workflow size={18} className="text-purple-500" />
                                    Lifecycle Hooks
                                </span>
                                <span className="text-gray-900 font-bold bg-white px-3 py-1 rounded-lg shadow-sm border border-gray-100">
                                    {currentModel?.lifecycle_hooks?.length || 0}
                                </span>
                            </div>
                            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl border border-gray-100">
                                <span className="text-gray-600 flex items-center gap-3 font-medium">
                                    <Cpu size={18} className="text-blue-500" />
                                    Actions Count
                                </span>
                                <span className="text-gray-900 font-bold bg-white px-3 py-1 rounded-lg shadow-sm border border-gray-100">
                                    {currentModel?.steps?.filter((s: any) => s.type === 'action').length || 0}
                                </span>
                            </div>
                            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl border border-gray-100">
                                <span className="text-gray-600 flex items-center gap-3 font-medium">
                                    <CheckCircle2 size={18} className="text-green-500" />
                                    Assertions
                                </span>
                                <span className="text-gray-900 font-bold bg-white px-3 py-1 rounded-lg shadow-sm border border-gray-100">
                                    {currentModel?.assertions?.length || 0}
                                </span>
                            </div>
                            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl border border-gray-100">
                                <span className="text-gray-600 flex items-center gap-3 font-medium">
                                    <Layers size={18} className="text-amber-500" />
                                    Control Flow
                                </span>
                                <span className="text-gray-900 font-bold bg-white px-3 py-1 rounded-lg shadow-sm border border-gray-100">
                                    {currentModel?.control_flow?.length || 0}
                                </span>
                            </div>
                        </div>

                        {currentModel?.validation_warnings?.length > 0 && (
                            <div className="mt-6">
                                <h4 className="text-[10px] font-bold text-amber-600 uppercase tracking-widest mb-3 flex items-center gap-2">
                                    <AlertTriangle size={12} />
                                    Validation Warnings
                                </h4>
                                <div className="space-y-2">
                                    {currentModel.validation_warnings.map((warn: string, i: number) => (
                                        <div key={i} className="text-xs bg-amber-50 text-amber-700 p-2 rounded-lg border border-amber-100 flex gap-2">
                                            <span className="font-bold">•</span>
                                            {warn}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {currentModel?.risk_flags?.length > 0 && (
                            <div className="mt-6">
                                <h4 className="text-[10px] font-bold text-red-600 uppercase tracking-widest mb-3 flex items-center gap-2">
                                    <AlertTriangle size={12} />
                                    LLM Risk Flags
                                </h4>
                                <div className="space-y-2">
                                    {currentModel.risk_flags.map((risk: any, i: number) => (
                                        <div key={i} className="text-xs bg-red-50 text-red-700 p-2 rounded-lg border border-red-100 flex gap-2">
                                            <span className="font-bold">•</span>
                                            {typeof risk === 'string' ? risk : risk.message || JSON.stringify(risk)}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="bg-gray-900 rounded-2xl shadow-xl p-6 text-white">
                        <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-4">Intent Hash</h3>
                        <div className="flex items-center gap-3 group">
                            <div className="flex-1 bg-gray-800 p-3 rounded-xl border border-gray-700 text-xs font-mono text-blue-400 break-all select-all">
                                {activeIntent.intent_hash}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Panel — Viewer */}
                <div className="lg:col-span-8 bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden min-h-[500px]">
                    <div className="bg-gray-800 px-6 py-3 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <div className="flex gap-1.5 mr-4">
                                <div className="w-2.5 h-2.5 rounded-full bg-red-400" />
                                <div className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                                <div className="w-2.5 h-2.5 rounded-full bg-green-400" />
                            </div>
                            <span className="text-xs font-mono text-gray-400">
                                {activeIntent.feature_name.toLowerCase().replace(/\s+/g, '_')}_intent.json
                            </span>
                        </div>
                        <div className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${activeIntent.validation_status === 'validated' ? 'bg-green-900 text-green-300' : 'bg-amber-900 text-amber-300'
                            }`}>
                            {activeIntent.validation_status}
                        </div>
                    </div>

                    <div className="p-8 h-full max-h-[600px] overflow-y-auto">
                        {viewMode === 'timeline' ? (
                            <StepTimeline model={currentModel} />
                        ) : (
                            <div className="font-mono text-sm">
                                <JsonTree data={currentModel} />
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};
