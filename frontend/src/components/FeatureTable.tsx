import type { Feature } from '../types';
import { CheckCircle2, Circle, AlertCircle, Clock, FileText } from 'lucide-react';
import { clsx } from 'clsx';

interface FeatureTableProps {
    features: Feature[];
    selectedFeatures: string[];
    onToggleFeature: (filePath: string) => void;
    onToggleAll: () => void;
}

export const FeatureTable = ({ features, selectedFeatures, onToggleFeature, onToggleAll }: FeatureTableProps) => {
    const allSelected = features.length > 0 && selectedFeatures.length === features.length;

    const getStatusBadge = (status: Feature['status']) => {
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
                        <th className="px-6 py-4 text-left">
                            <button
                                onClick={onToggleAll}
                                className="flex items-center justify-center w-5 h-5 rounded border border-gray-300 bg-white"
                            >
                                {allSelected ? <CheckCircle2 className="w-4 h-4 text-blue-600 fill-current" /> : <Circle className="w-4 h-4 text-gray-300" />}
                            </button>
                        </th>
                        <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Feature / File</th>
                        <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Tests</th>
                        <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Framework</th>
                        <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                    {features.map((feature) => {
                        const isSelected = selectedFeatures.includes(feature.file_path);
                        return (
                            <tr key={feature.file_path} className={clsx("hover:bg-gray-50 transition-colors cursor-pointer", isSelected && "bg-blue-50/50")} onClick={() => onToggleFeature(feature.file_path)}>
                                <td className="px-6 py-4">
                                    <div className="flex items-center justify-center w-5 h-5 rounded border border-gray-300 bg-white">
                                        {isSelected && <CheckCircle2 className="w-4 h-4 text-blue-600 fill-current" />}
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    <div className="flex flex-col">
                                        <span className="text-sm font-semibold text-gray-900">{feature.feature_name}</span>
                                        <span className="text-xs text-gray-500 flex items-center gap-1 mt-0.5">
                                            <FileText className="w-3 h-3" /> {feature.file_path.split(/[\/\\]/).pop()}
                                        </span>
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    <span className="text-sm text-gray-600">{feature.tests.length} tests</span>
                                </td>
                                <td className="px-6 py-4">
                                    <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded text-gray-700">{feature.framework}</span>
                                </td>
                                <td className="px-6 py-4">
                                    {getStatusBadge(feature.status)}
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};
