import { useState, useRef, useEffect } from 'react';
import {
    AlertCircle,
    CheckCircle2,
    ChevronDown,
    ChevronUp,
    Loader2,
    Wifi,
    WifiOff,
    Terminal,
} from 'lucide-react';

interface AnalysisProgressProps {
    step: string;
    progress: number;
    logs: string[];
    error: string | null;
    trace: string | null;
    isComplete: boolean;
    isConnected: boolean;
}

const STEPS = [
    'Discovery',
    'Build Metadata',
    'Feature Extraction',
    'Dependency Analysis',
    'Build Graph',
    'Shared Modules',
    'Config Files',
    'Feature Modeling',
    'Assertions',
    'Driver Model',
    'Complete',
];

export function AnalysisProgress({
    step,
    progress,
    logs,
    error,
    trace,
    isComplete,
    isConnected,
}: AnalysisProgressProps) {
    const [showTrace, setShowTrace] = useState(false);
    const [showLogs, setShowLogs] = useState(true);
    const logEndRef = useRef<HTMLDivElement>(null);

    // Auto-scroll logs
    useEffect(() => {
        logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    const currentStepIndex = STEPS.indexOf(step);

    return (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
            {/* Header */}
            <div className="px-8 py-6 border-b border-gray-100 flex items-center justify-between">
                <div>
                    <h2 className="text-xl font-bold text-gray-900">
                        {error
                            ? 'Analysis Failed'
                            : isComplete
                                ? 'Analysis Complete'
                                : 'Analyzing Repository...'}
                    </h2>
                    <p className="text-sm text-gray-500 mt-1">
                        {error
                            ? 'An error occurred during analysis'
                            : isComplete
                                ? 'All analysis steps completed successfully'
                                : `Step: ${step || 'Initializing...'}`}
                    </p>
                </div>
                <div className="flex items-center gap-2 text-xs">
                    {isConnected ? (
                        <span className="flex items-center gap-1 text-green-600 bg-green-50 px-2.5 py-1 rounded-full">
                            <Wifi className="w-3 h-3" /> Connected
                        </span>
                    ) : (
                        <span className="flex items-center gap-1 text-amber-600 bg-amber-50 px-2.5 py-1 rounded-full">
                            <WifiOff className="w-3 h-3" /> Reconnecting...
                        </span>
                    )}
                </div>
            </div>

            {/* Progress Bar */}
            <div className="px-8 py-5">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-semibold text-gray-700">Progress</span>
                    <span className="text-sm font-bold text-blue-600">{progress}%</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
                    <div
                        className={`h-full rounded-full transition-all duration-700 ease-out ${error
                                ? 'bg-red-500'
                                : isComplete
                                    ? 'bg-green-500'
                                    : 'bg-gradient-to-r from-blue-500 to-indigo-500'
                            }`}
                        style={{ width: `${progress}%` }}
                    />
                </div>
            </div>

            {/* Step Indicators */}
            <div className="px-8 pb-4">
                <div className="grid grid-cols-5 gap-2 sm:grid-cols-11">
                    {STEPS.map((s, i) => {
                        const isDone = currentStepIndex > i || isComplete;
                        const isCurrent = s === step && !isComplete && !error;
                        const isFailed = error && s === step;

                        return (
                            <div key={s} className="flex flex-col items-center gap-1">
                                <div
                                    className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 ${isFailed
                                            ? 'bg-red-100 text-red-600 ring-2 ring-red-400'
                                            : isDone
                                                ? 'bg-green-100 text-green-600'
                                                : isCurrent
                                                    ? 'bg-blue-100 text-blue-600 ring-2 ring-blue-400 animate-pulse'
                                                    : 'bg-gray-100 text-gray-400'
                                        }`}
                                >
                                    {isFailed ? (
                                        <AlertCircle className="w-3.5 h-3.5" />
                                    ) : isDone ? (
                                        <CheckCircle2 className="w-3.5 h-3.5" />
                                    ) : isCurrent ? (
                                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                    ) : (
                                        i + 1
                                    )}
                                </div>
                                <span
                                    className={`text-[10px] text-center leading-tight ${isCurrent
                                            ? 'text-blue-600 font-semibold'
                                            : isDone
                                                ? 'text-green-600'
                                                : 'text-gray-400'
                                        }`}
                                >
                                    {s}
                                </span>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Error Section */}
            {error && (
                <div className="mx-8 mb-4 border border-red-200 rounded-xl bg-red-50 overflow-hidden">
                    <div className="px-4 py-3 flex items-start gap-3">
                        <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-red-800">{step} Failed</p>
                            <p className="text-sm text-red-700 mt-1 break-words">{error}</p>
                        </div>
                    </div>
                    {trace && (
                        <>
                            <button
                                onClick={() => setShowTrace(!showTrace)}
                                className="w-full px-4 py-2 flex items-center gap-2 text-xs text-red-600 hover:bg-red-100 transition-colors border-t border-red-200"
                            >
                                {showTrace ? (
                                    <ChevronUp className="w-3.5 h-3.5" />
                                ) : (
                                    <ChevronDown className="w-3.5 h-3.5" />
                                )}
                                {showTrace ? 'Hide' : 'Show'} Stack Trace
                            </button>
                            {showTrace && (
                                <pre className="px-4 py-3 text-xs text-red-800 bg-red-100/50 overflow-x-auto border-t border-red-200 whitespace-pre-wrap max-h-60 overflow-y-auto">
                                    {trace}
                                </pre>
                            )}
                        </>
                    )}
                </div>
            )}

            {/* Log Section */}
            <div className="mx-8 mb-6 border border-gray-200 rounded-xl overflow-hidden">
                <button
                    onClick={() => setShowLogs(!showLogs)}
                    className="w-full px-4 py-2.5 flex items-center justify-between bg-gray-50 hover:bg-gray-100 transition-colors"
                >
                    <span className="flex items-center gap-2 text-sm font-medium text-gray-700">
                        <Terminal className="w-4 h-4" />
                        Analysis Logs ({logs.length})
                    </span>
                    {showLogs ? (
                        <ChevronUp className="w-4 h-4 text-gray-500" />
                    ) : (
                        <ChevronDown className="w-4 h-4 text-gray-500" />
                    )}
                </button>
                {showLogs && (
                    <div className="bg-gray-900 text-gray-200 p-4 max-h-52 overflow-y-auto font-mono text-xs leading-relaxed">
                        {logs.length === 0 ? (
                            <span className="text-gray-500">Waiting for analysis to start...</span>
                        ) : (
                            logs.map((log, i) => (
                                <div
                                    key={i}
                                    className={`py-0.5 ${log.startsWith('❌')
                                            ? 'text-red-400'
                                            : log.startsWith('✅')
                                                ? 'text-green-400'
                                                : 'text-gray-300'
                                        }`}
                                >
                                    <span className="text-gray-600 mr-2 select-none">{String(i + 1).padStart(2, '0')}</span>
                                    {log}
                                </div>
                            ))
                        )}
                        <div ref={logEndRef} />
                    </div>
                )}
            </div>
        </div>
    );
}
