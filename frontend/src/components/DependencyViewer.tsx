import { clsx } from 'clsx';
import type { AnalysisResponse } from '../types';
import { FileCode, Box, ArrowRight } from 'lucide-react';

interface DependencyViewerProps {
    data: AnalysisResponse;
}

export const DependencyViewer = ({ data }: DependencyViewerProps) => {
    const graph = data.dependency_graph;

    if (!graph || Object.keys(graph).length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-20 bg-gray-50 rounded-2xl border border-dashed border-gray-200">
                <Box className="w-12 h-12 text-gray-300 mb-4" />
                <p className="text-gray-500 font-medium text-lg">No dependencies identified</p>
                <p className="text-gray-400 text-sm mt-1">The analyzer didn't find any cross-file dependencies in this project.</p>
            </div>
        );
    }

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                {Object.entries(graph).map(([filePath, depData]) => (
                    <div
                        key={filePath}
                        className="group bg-white border border-gray-100 p-6 rounded-2xl shadow-sm hover:shadow-md hover:border-blue-100 transition-all duration-300"
                    >
                        <div className="flex items-center justify-between mb-4 border-b border-gray-50 pb-4">
                            <div className="flex items-center gap-4">
                                <div className={clsx(
                                    "p-3 rounded-xl transition-colors",
                                    depData.type === 'test' ? "bg-orange-50 text-orange-600" : "bg-blue-50 text-blue-600",
                                    "group-hover:bg-opacity-80"
                                )}>
                                    <FileCode className="w-5 h-5" />
                                </div>
                                <div>
                                    <h3 className="font-bold text-gray-900 leading-tight">
                                        {depData.class_name || filePath.split('/').pop()}
                                    </h3>
                                    <p className="text-xs text-gray-400 font-medium mt-0.5 truncate max-w-[200px] lg:max-w-xs">
                                        {depData.package || '<default>'}
                                    </p>
                                </div>
                            </div>
                            <span className={clsx(
                                "px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider",
                                depData.type === 'test' ? "bg-orange-100 text-orange-700" : "bg-blue-100 text-blue-700"
                            )}>
                                {depData.type}
                            </span>
                        </div>

                        {depData.imports.length > 0 ? (
                            <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                    <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Dependencies</span>
                                    <span className="text-[10px] text-gray-300 font-medium">{depData.imports.length} imports</span>
                                </div>
                                <div className="grid gap-2">
                                    {depData.imports.slice(0, 5).map((imp, i) => (
                                        <div key={i} className="flex items-center gap-3 p-2 rounded-lg bg-gray-50/50 group-hover:bg-white transition-colors border border-transparent group-hover:border-gray-100 min-w-0">
                                            <ArrowRight className="w-3.5 h-3.5 text-gray-300 flex-shrink-0" />
                                            <span className="text-sm font-mono text-gray-600 truncate min-w-0">{imp}</span>
                                        </div>
                                    ))}
                                    {depData.imports.length > 5 && (
                                        <p className="text-[10px] text-gray-400 italic pl-6">
                                            + {depData.imports.length - 5} more imports...
                                        </p>
                                    )}
                                </div>
                            </div>
                        ) : (
                            <div className="py-4 text-center">
                                <p className="text-xs text-gray-400 italic">No external imports detected</p>
                            </div>
                        )}

                        <div className="mt-4 pt-4 border-t border-gray-50 overflow-hidden">
                            <code className="block text-[10px] text-gray-300 font-mono break-all opacity-0 group-hover:opacity-100 transition-all duration-300">
                                {filePath}
                            </code>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};
