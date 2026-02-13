import React, { useState, useEffect } from 'react';
import { FRAMEWORK_DATA } from '../constants/frameworks';
import { api } from '../services/api';
import { useMigrationStore } from '../store/migrationStore';
import { Loader2 } from 'lucide-react';
import { clsx } from 'clsx';

const RepoConfiguration: React.FC = () => {
    const { setStep, setRepoDetails, setLoading, setError, isLoading, error } = useMigrationStore();

    const [sessionName, setSessionName] = useState('');
    const [repoUrl, setRepoUrl] = useState('');
    const [targetRepoUrl, setTargetRepoUrl] = useState('');
    const [pat, setPat] = useState('');

    // Selection State
    const [sFw, setSourceFw] = useState('');
    const [sLang, setSourceLang] = useState('');
    const [sTest, setSourceTest] = useState('');

    const [tFw, setTargetFw] = useState('');
    const [tLang, setTargetLang] = useState('');
    const [tTest, setTargetTest] = useState('');

    // Reset lower levels
    useEffect(() => { setSourceLang(''); setSourceTest(''); }, [sFw]);
    useEffect(() => { setSourceTest(''); }, [sLang]);
    useEffect(() => { setTargetLang(''); setTargetTest(''); }, [tFw]);
    useEffect(() => { setTargetTest(''); }, [tLang]);

    const handleVerify = async () => {
        setLoading(true);
        setError(null);

        const sFwString = `${sFw} ${sLang} - ${sTest}`;
        const tFwString = `${tFw} ${tLang} - ${tTest}`;

        try {
            const { branches } = await api.verifyRepo(repoUrl, pat || undefined);

            setRepoDetails({
                sessionName,
                repoUrl,
                targetRepoUrl,
                pat,
                sourceFramework: sFwString,
                targetFramework: tFwString,
                branches
            });
            setStep(2);
        } catch (err: any) {
            setError(err.response?.data?.detail || "Failed to verify repository");
        } finally {
            setLoading(false);
        }
    };

    const allFrameworks = FRAMEWORK_DATA.map(f => f.framework);
    const allLanguages = Array.from(new Set(FRAMEWORK_DATA.flatMap(f => Object.keys(f.languages))));
    const allTestEngines = Array.from(new Set(FRAMEWORK_DATA.flatMap(f => Object.values(f.languages).flat())));

    const isEnabled = (type: 'lang' | 'test', fw: string, lang: string, opt: string) => {
        const framework = FRAMEWORK_DATA.find(f => f.framework === fw);
        if (type === 'lang') return framework ? Object.keys(framework.languages).includes(opt) : true;
        if (type === 'test') return (framework && lang) ? (framework.languages[lang] || []).includes(opt) : false;
        return false;
    };

    const ChipGroup = ({ label, options, selected, onSelect, checkEnabled }: any) => (
        <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
            <div className="flex flex-wrap gap-2">
                {options.map((opt: string) => {
                    const enabled = checkEnabled ? checkEnabled(opt) : true;
                    return (
                        <button
                            key={opt}
                            onClick={() => enabled && onSelect(opt)}
                            disabled={!enabled}
                            className={clsx(
                                "px-3 py-1 rounded-full text-sm border transition-colors",
                                selected === opt
                                    ? "bg-blue-600 text-white border-blue-600"
                                    : enabled
                                        ? "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                                        : "bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed"
                            )}
                        >
                            {opt}
                        </button>
                    );
                })}
            </div>
        </div>
    );

    const isFormValid = repoUrl && sFw && sLang && sTest && tFw && tLang && tTest;

    return (
        <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-md">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
                <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="text-lg font-semibold mb-4 text-blue-800">Source</h3>
                    <ChipGroup label="Framework" options={allFrameworks} selected={sFw} onSelect={setSourceFw} />
                    <ChipGroup label="Language" options={allLanguages} selected={sLang} onSelect={setSourceLang} checkEnabled={(o: string) => isEnabled('lang', sFw, '', o)} />
                    <ChipGroup label="Test Engine" options={allTestEngines} selected={sTest} onSelect={setSourceTest} checkEnabled={(o: string) => isEnabled('test', sFw, sLang, o)} />
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="text-lg font-semibold mb-4 text-green-800">Target</h3>
                    <ChipGroup label="Framework" options={allFrameworks} selected={tFw} onSelect={setTargetFw} />
                    <ChipGroup label="Language" options={allLanguages} selected={tLang} onSelect={setTargetLang} checkEnabled={(o: string) => isEnabled('lang', tFw, '', o)} />
                    <ChipGroup label="Test Engine" options={allTestEngines} selected={tTest} onSelect={setTargetTest} checkEnabled={(o: string) => isEnabled('test', tFw, tLang, o)} />
                </div>
            </div>

            <div className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Session Name</label>
                    <input
                        type="text"
                        className="w-full p-2 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
                        placeholder="e.g. Pytest to Playwright Phase 1"
                        value={sessionName}
                        onChange={(e) => setSessionName(e.target.value)}
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Source Repo URL</label>
                    <input
                        type="text"
                        className="w-full p-2 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
                        placeholder="https://github.com/user/source-repo.git"
                        value={repoUrl}
                        onChange={(e) => setRepoUrl(e.target.value)}
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Target Repo URL (Optional)</label>
                    <input
                        type="text"
                        className="w-full p-2 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
                        placeholder="https://github.com/user/target-repo.git"
                        value={targetRepoUrl}
                        onChange={(e) => setTargetRepoUrl(e.target.value)}
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Personal Access Token</label>
                    <input
                        type="password"
                        className="w-full p-2 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
                        placeholder="ghp_..."
                        value={pat}
                        onChange={(e) => setPat(e.target.value)}
                    />
                </div>
            </div>

            {error && <div className="text-red-500 my-4 text-sm">{error}</div>}

            <button
                onClick={handleVerify}
                disabled={isLoading || !isFormValid}
                className="w-full mt-6 bg-blue-600 text-white py-3 px-4 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 flex justify-center items-center transition-colors"
            >
                {isLoading && <Loader2 className="animate-spin mr-2" />}
                {isLoading ? 'Verifying...' : 'Verify Access & Fetch Branches'}
            </button>
        </div>
    );
};

export default RepoConfiguration;
