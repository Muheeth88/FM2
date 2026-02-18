import type { AnalysisResponse } from '../types';
import {
    Info, Package, Settings, Shield, HardDrive,
    FileText, Code, GitBranch, Terminal
} from 'lucide-react';

interface AnalysisMetadataProps {
    data: AnalysisResponse;
}

export const AnalysisMetadata = ({ data }: AnalysisMetadataProps) => {
    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {/* Core Info Cards */}
                <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-start gap-4">
                    <div className="bg-blue-50 p-3 rounded-xl">
                        <Code className="w-6 h-6 text-blue-600" />
                    </div>
                    <div>
                        <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">Language</p>
                        <p className="text-xl font-bold text-gray-900">{data.language}</p>
                    </div>
                </div>

                <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-start gap-4">
                    <div className="bg-purple-50 p-3 rounded-xl">
                        <Package className="w-6 h-6 text-purple-600" />
                    </div>
                    <div>
                        <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">Framework</p>
                        <p className="text-xl font-bold text-gray-900">{data.framework}</p>
                    </div>
                </div>

                <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-start gap-4">
                    <div className="bg-orange-50 p-3 rounded-xl">
                        <Terminal className="w-6 h-6 text-orange-600" />
                    </div>
                    <div>
                        <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">Build System</p>
                        <p className="text-xl font-bold text-gray-900">{data.build_system}</p>
                    </div>
                </div>

                <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-start gap-4">
                    <div className="bg-green-50 p-3 rounded-xl">
                        <GitBranch className="w-6 h-6 text-green-600" />
                    </div>
                    <div>
                        <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">Features</p>
                        <p className="text-xl font-bold text-gray-900">{data.features.length}</p>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Build Dependencies */}
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden text-black">
                    <div className="px-6 py-4 border-b border-gray-100 bg-gray-50/50 flex items-center gap-2 font-bold text-gray-700">
                        <HardDrive className="w-5 h-5 text-gray-400" /> Build Dependencies
                    </div>
                    <div className="p-0 max-h-[400px] overflow-y-auto">
                        <table className="min-w-full divide-y divide-gray-100">
                            <thead className="bg-white sticky top-0">
                                <tr>
                                    <th className="px-6 py-3 text-left text-[10px] font-bold text-gray-400 uppercase tracking-wider">Dependency</th>
                                    <th className="px-6 py-3 text-left text-[10px] font-bold text-gray-400 uppercase tracking-wider">Version</th>
                                    <th className="px-6 py-3 text-left text-[10px] font-bold text-gray-400 uppercase tracking-wider">Type</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50">
                                {data.build_dependencies.map((dep, i) => (
                                    <tr key={i} className="hover:bg-gray-50/50 transition-colors">
                                        <td className="px-6 py-3 text-sm font-medium text-gray-700">{dep.name}</td>
                                        <td className="px-6 py-3 text-sm text-gray-500 font-mono">{dep.version || '-'}</td>
                                        <td className="px-6 py-3">
                                            <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-600 uppercase">
                                                {dep.type}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Driver & Assertions */}
                <div className="space-y-8">
                    {/* Driver Model */}
                    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden text-black">
                        <div className="px-6 py-4 border-b border-gray-100 bg-gray-50/50 flex items-center gap-2 font-bold text-gray-700">
                            <Settings className="w-5 h-5 text-gray-400" /> Driver Configuration
                        </div>
                        <div className="p-6 grid grid-cols-2 gap-6">
                            <div>
                                <p className="text-[10px] font-bold text-gray-400 uppercase mb-1">Driver Type</p>
                                <p className="text-sm font-semibold text-gray-700 bg-gray-50 p-2 rounded-lg border border-gray-100 italic">
                                    {data.driver_model?.driver_type || 'Unknown'}
                                </p>
                            </div>
                            <div>
                                <p className="text-[10px] font-bold text-gray-400 uppercase mb-1">Initialization</p>
                                <p className="text-sm font-semibold text-gray-700 bg-gray-50 p-2 rounded-lg border border-gray-100 italic">
                                    {data.driver_model?.initialization_pattern || 'Standard'}
                                </p>
                            </div>
                            <div className="col-span-2">
                                <p className="text-[10px] font-bold text-gray-400 uppercase mb-1">Thread Model</p>
                                <p className="text-sm font-semibold text-gray-700 bg-gray-50 p-2 rounded-lg border border-gray-100 italic">
                                    {data.driver_model?.thread_model || 'Sequential'}
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Assertions */}
                    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden text-black">
                        <div className="px-6 py-4 border-b border-gray-100 bg-gray-50/50 flex items-center gap-2 font-bold text-gray-700">
                            <Shield className="w-5 h-5 text-gray-400" /> Assertion Patterns
                        </div>
                        <div className="p-0 max-h-[250px] overflow-y-auto">
                            <table className="min-w-full divide-y divide-gray-100">
                                <thead className="bg-white sticky top-0">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-[10px] font-bold text-gray-400 uppercase tracking-wider">Library</th>
                                        <th className="px-6 py-3 text-left text-[10px] font-bold text-gray-400 uppercase tracking-wider">Type</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-50">
                                    {data.assertions.map((ass, i) => (
                                        <tr key={i} className="hover:bg-gray-50/50">
                                            <td className="px-6 py-3 text-sm font-medium text-gray-700">{ass.library}</td>
                                            <td className="px-6 py-3 text-xs text-gray-500">{ass.assertion_type}</td>
                                        </tr>
                                    ))}
                                    {data.assertions.length === 0 && (
                                        <tr><td colSpan={2} className="px-6 py-8 text-center text-sm text-gray-400 italic">No assertions detected</td></tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Config Files */}
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden text-black">
                    <div className="px-6 py-4 border-b border-gray-100 bg-gray-50/50 flex items-center gap-2 font-bold text-gray-700">
                        <FileText className="w-5 h-5 text-gray-400" /> Configuration Files
                    </div>
                    <div className="p-4 grid gap-3 max-h-[300px] overflow-y-auto">
                        {data.config_files.map((cfg, i) => (
                            <div key={i} className="flex flex-col gap-1 p-3 rounded-xl border border-gray-100 bg-gray-50/50">
                                <div className="flex items-center justify-between">
                                    <span className="text-sm font-bold text-gray-700">{cfg.file_path.split('/').pop()}</span>
                                    <span className="text-[10px] px-2 py-0.5 rounded bg-white border border-gray-200 text-gray-400 font-bold uppercase">{cfg.type}</span>
                                </div>
                                <span className="text-[10px] text-gray-400 font-mono truncate">{cfg.file_path}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Shared Modules */}
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden text-black">
                    <div className="px-6 py-4 border-b border-gray-100 bg-gray-50/50 flex items-center gap-2 font-bold text-gray-700">
                        <Info className="w-5 h-5 text-gray-400" /> Global Shared Modules
                    </div>
                    <div className="p-4 grid gap-3 max-h-[300px] overflow-y-auto">
                        {data.shared_modules.map((mod, i) => (
                            <div key={i} className="flex flex-col gap-1 p-3 rounded-xl border border-gray-100 bg-gray-50/50">
                                <span className="text-sm font-bold text-gray-700">{mod.split('/').pop()}</span>
                                <span className="text-[10px] text-gray-400 font-mono truncate">{mod}</span>
                            </div>
                        ))}
                        {data.shared_modules.length === 0 && (
                            <div className="p-8 text-center text-sm text-gray-400 italic">No shared modules identified</div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};
