import React, { useState } from 'react';
import { api } from '../services/api';
import { useMigrationStore } from '../store/migrationStore';
import { Loader2 } from 'lucide-react';

const BranchSelection: React.FC = () => {
    const { repoDetails, setStep, setSession, setLoading, setError, isLoading, error } = useMigrationStore();
    const [selectedBranch, setSelectedBranch] = useState(repoDetails.branches[0] || 'main');
    const [success, setSuccess] = useState(false);

    const handleInitiate = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await api.createSession({
                name: repoDetails.sessionName,
                source_repo_url: repoDetails.repoUrl,
                target_repo_url: repoDetails.targetRepoUrl || undefined,
                target_repo_mode: repoDetails.targetRepoMode,
                target_repo_name: repoDetails.targetRepoName || undefined,
                target_repo_owner: repoDetails.targetRepoOwner || undefined,
                target_repo_visibility: repoDetails.targetRepoVisibility || undefined,
                source_framework: repoDetails.sourceFramework,
                target_framework: repoDetails.targetFramework,
                base_branch: selectedBranch,
                pat: repoDetails.pat || undefined,
            });
            setSession(response);
            setSuccess(true);
        } catch (err: any) {
            setError(err.response?.data?.detail || "Failed to initiate migration session");
        } finally {
            setLoading(false);
        }
    };

    if (success) {
        return (
            <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md text-center">
                <h2 className="text-2xl font-bold mb-4 text-green-600">Session "{repoDetails.sessionName}" Initiated!</h2>
                <p className="mb-6 text-gray-600">Migration session has been created successfully.</p>
                <button className="bg-blue-600 text-white py-2 px-4 rounded" onClick={() => window.location.reload()}>
                    Finish
                </button>
            </div>
        );
    }

    return (
        <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md">
            <div className="mb-6 p-4 bg-gray-50 rounded space-y-1 text-sm text-gray-600">
                <p><strong>Session Name:</strong> {repoDetails.sessionName}</p>
                <p><strong>Repo:</strong> {repoDetails.repoUrl}</p>
                <p><strong>Source:</strong> {repoDetails.sourceFramework}</p>
                <p><strong>Target:</strong> {repoDetails.targetFramework}</p>
            </div>

            <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-1">Select Base Branch</label>
                <select
                    className="w-full p-2 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
                    value={selectedBranch}
                    onChange={(e) => setSelectedBranch(e.target.value)}
                >
                    {repoDetails.branches.map(b => <option key={b} value={b}>{b}</option>)}
                </select>
            </div>

            {error && <div className="text-red-500 mb-4 text-sm">{error}</div>}

            <div className="flex gap-4">
                <button onClick={() => setStep(1)} className="w-1/3 py-2 border rounded hover:bg-gray-50">Back</button>
                <button
                    onClick={handleInitiate}
                    disabled={isLoading}
                    className="w-2/3 bg-green-600 text-white py-2 rounded font-semibold hover:bg-green-700 disabled:bg-gray-400 flex justify-center items-center"
                >
                    {isLoading && <Loader2 className="animate-spin mr-2" />}
                    {isLoading ? 'Initiating...' : 'Initiate Migration'}
                </button>
            </div>
        </div>
    );
};

export default BranchSelection;
