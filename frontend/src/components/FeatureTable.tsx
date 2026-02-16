import { useState } from 'react';
import type { FeatureSummary, FeatureDetail } from '../types';
import {
    CheckCircle2, Circle, AlertCircle, Clock, FileText,
    ChevronDown, ChevronRight, Hash, Settings, Layers, Calendar,
    Loader2
} from 'lucide-react';
import { clsx } from 'clsx';
import { api } from '../services/api';

interface FeatureTableProps {
    sessionId: string;
    features: FeatureSummary[];
    selectedFeatures: string[];
    onToggleFeature: (featureId: string) => void;
    onToggleAll: () => void;
}

export const FeatureTable = ({ sessionId, features, selectedFeatures, onToggleFeature, onToggleAll }: FeatureTableProps) => {
    const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});
    const [featureDetails, setFeatureDetails] = useState<Record<string, FeatureDetail>>({});
    const [loadingDetails, setLoadingDetails] = useState<Record<string, boolean>>({});

    const allSelected = features.length > 0 && selectedFeatures.length === features.length;

    const toggleRow = async (featureId: string) => {
        const isExpanded = !!expandedRows[featureId];
        setExpandedRows(prev => ({ ...prev, [featureId]: !isExpanded }));

        if (!isExpanded && !featureDetails[featureId]) {
            setLoadingDetails(prev => ({ ...prev, [featureId]: true }));
            try {
                const detail = await api.getFeatureDetail(sessionId, featureId);
                setFeatureDetails(prev => ({ ...prev, [featureId]: detail }));
            } catch (err) {
                console.error("Failed to load feature detail", err);
            } finally {
                setLoadingDetails(prev => ({ ...prev, [featureId]: false }));
            }
        }
    };

    const getStatusBadge = (status: FeatureSummary['status']) => {
        switch (status) {
            case 'MIGRATED':
                return <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"><CheckCircle2 className="w-3.5 h-3.5" /> Migrated</span>;
            case 'NEEDS_UPDATE':
                return <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800"><Clock className="w-3.5 h-3.5" /> Needs Update</span>;
            case 'CONFLICTED':
                return <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800"><AlertCircle className="w-3.5 h-3.5" /> Conflected</span>;
            default:
                return <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">Not Migrated</span>;
        }
    };

    return (
        <div className="overflow-hidden border border-gray-200 rounded-xl bg-white shadow-sm">
            <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                    <tr>
                        <th className="px-6 py-4 w-10">
                            <button
                                onClick={onToggleAll}
                                className="flex items-center justify-center w-5 h-5 rounded border border-gray-300 bg-white"
                            >
                                {allSelected ? <CheckCircle2 className="w-4 h-4 text-blue-600 fill-current" /> : <Circle className="w-4 h-4 text-gray-300" />}
                            </button>
                        </th>
                        <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Feature</th>
                        <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                        <th className="px-6 py-4 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">Dependent Files</th>
                        <th className="px-6 py-4 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">Config Deps</th>
                        <th className="px-6 py-4 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">Shared Modules</th>
                        <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Last Migrated</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                    {features.map((feature) => {
                        const isSelected = selectedFeatures.includes(feature.feature_id);
                        const isExpanded = expandedRows[feature.feature_id];
                        const detail = featureDetails[feature.feature_id];
                        const isLoading = loadingDetails[feature.feature_id];

                        return (
                            <>
                                <tr key={feature.feature_id} className={clsx("hover:bg-gray-50 transition-colors cursor-pointer", isSelected && "bg-blue-50/50")}>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    onToggleFeature(feature.feature_id);
                                                }}
                                                className="flex items-center justify-center w-5 h-5 rounded border border-gray-300 bg-white"
                                            >
                                                {isSelected && <CheckCircle2 className="w-4 h-4 text-blue-600 fill-current" />}
                                            </button>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4" onClick={() => toggleRow(feature.feature_id)}>
                                        <div className="flex items-center gap-3">
                                            {isExpanded ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
                                            <div className="flex flex-col">
                                                <span className="text-sm font-semibold text-gray-900">{feature.feature_name}</span>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4" onClick={() => toggleRow(feature.feature_id)}>
                                        {getStatusBadge(feature.status)}
                                    </td>
                                    <td className="px-6 py-4 text-center" onClick={() => toggleRow(feature.feature_id)}>
                                        <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium bg-blue-50 text-blue-700">
                                            <Hash className="w-3 h-3" /> {feature.dependent_file_count}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-center" onClick={() => toggleRow(feature.feature_id)}>
                                        <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium bg-purple-50 text-purple-700">
                                            <Settings className="w-3 h-3" /> {feature.config_dependency_count}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-center" onClick={() => toggleRow(feature.feature_id)}>
                                        <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium bg-amber-50 text-amber-700">
                                            <Layers className="w-3 h-3" /> {feature.shared_module_count}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4" onClick={() => toggleRow(feature.feature_id)}>
                                        <span className="text-xs text-gray-500 flex items-center gap-1.5">
                                            <Calendar className="w-3.5 h-3.5" />
                                            {feature.last_migrated_commit ? feature.last_migrated_commit.substring(0, 7) : 'Never'}
                                        </span>
                                    </td>
                                </tr>
                                {isExpanded && (
                                    <tr className="bg-gray-50/50">
                                        <td colSpan={7} className="px-12 py-6">
                                            {isLoading ? (
                                                <div className="flex items-center justify-center py-4 text-gray-500 text-sm gap-2">
                                                    <Loader2 className="w-4 h-4 animate-spin" /> Loading details...
                                                </div>
                                            ) : detail ? (
                                                <div className="grid grid-cols-2 gap-8 animate-in fade-in slide-in-from-top-2 duration-300">
                                                    <div className="space-y-4">
                                                        <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400">Dependency Files</h4>
                                                        <ul className="space-y-2">
                                                            {detail.dependency_files.map(file => (
                                                                <li key={file} className="flex items-center gap-2 text-sm text-gray-600 bg-white p-2 rounded border border-gray-100">
                                                                    <FileText className="w-4 h-4 text-blue-400" />
                                                                    {file.split(/[\/\\]/).pop()}
                                                                    <span className="text-[10px] text-gray-400 font-mono truncate">{file}</span>
                                                                </li>
                                                            ))}
                                                            {detail.dependency_files.length === 0 && <li className="text-sm text-gray-400 italic">No direct dependencies</li>}
                                                        </ul>
                                                    </div>
                                                    <div className="space-y-6">
                                                        <div>
                                                            <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-4">Config & Shared</h4>
                                                            <div className="flex flex-wrap gap-2">
                                                                {detail.config_dependencies.map(cfg => (
                                                                    <span key={cfg} className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-[11px] font-medium border border-purple-200">
                                                                        {cfg.split(/[\/\\]/).pop()}
                                                                    </span>
                                                                ))}
                                                                {detail.shared_modules.map(mod => (
                                                                    <span key={mod} className="px-2 py-1 bg-amber-100 text-amber-700 rounded text-[11px] font-medium border border-amber-200">
                                                                        {mod.split(/[\/\\]/).pop()}
                                                                    </span>
                                                                ))}
                                                            </div>
                                                        </div>
                                                        <div>
                                                            <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-4">Tests Detected</h4>
                                                            <div className="space-y-2">
                                                                {detail.tests.map(test => (
                                                                    <div key={test.name} className="bg-white p-2 rounded border border-gray-100 flex items-center justify-between">
                                                                        <span className="text-sm font-medium text-gray-700">{test.name}</span>
                                                                        <div className="flex gap-1">
                                                                            {test.annotations.map(anno => (
                                                                                <span key={anno} className="text-[10px] bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">@{anno}</span>
                                                                            ))}
                                                                        </div>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            ) : (
                                                <div className="text-center text-red-500 text-sm">Failed to load details.</div>
                                            )}
                                        </td>
                                    </tr>
                                )}
                            </>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};
