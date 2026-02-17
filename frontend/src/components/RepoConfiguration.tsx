import React, { useState, useEffect } from 'react';
import { FRAMEWORK_DATA } from '../constants/frameworks';
import { api } from '../services/api';
import { useMigrationStore } from '../store/migrationStore';
import { Loader2, Globe, Lock, GitBranch, PlusCircle, Database, ShieldCheck, Github } from 'lucide-react';
import { clsx } from 'clsx';

const RepoConfiguration: React.FC = () => {
    const { setStep, setRepoDetails, setLoading, setError, isLoading, error } = useMigrationStore();

    const [sessionName, setSessionName] = useState('Some Migration');
    const [sourceRepoUrl, setSourceRepoUrl] = useState('https://github.com/Qualizeal/utaf-java-demo');
    const [sourcePat, setSourcePat] = useState('');

    // Selection State for Frameworks
    const [sFw, setSourceFw] = useState('Selenium');
    const [sLang, setSourceLang] = useState('Java');
    const [sTest, setSourceTest] = useState('TestNG');

    const [tFw, setTargetFw] = useState('Playwright');
    const [tLang, setTargetLang] = useState('TypeScript');
    const [tTest, setTargetTest] = useState('Jest');

    // Target Repo State
    const [targetRepoMode, setTargetRepoMode] = useState<'existing' | 'new'>('existing');
    const [targetRepoUrl, setTargetRepoUrl] = useState('https://github.com/Muheeth88/someRepo');
    const [targetRepoName, setTargetRepoName] = useState('');
    const [targetRepoOwner, setTargetRepoOwner] = useState('');
    const [targetRepoVisibility, setTargetRepoVisibility] = useState<'public' | 'private'>('public');
    const [targetPat, setTargetPat] = useState('');

    // Selection Handlers (to clear dependent fields ONLY on actual change)
    const handleSourceFwChange = (fw: string) => {
        if (fw !== sFw) {
            setSourceFw(fw);
            setSourceLang('');
            setSourceTest('');
        }
    };

    const handleSourceLangChange = (lang: string) => {
        if (lang !== sLang) {
            setSourceLang(lang);
            setSourceTest('');
        }
    };

    const handleTargetFwChange = (fw: string) => {
        if (fw !== tFw) {
            setTargetFw(fw);
            setTargetLang('');
            setTargetTest('');
        }
    };

    const handleTargetLangChange = (lang: string) => {
        if (lang !== tLang) {
            setTargetLang(lang);
            setTargetTest('');
        }
    };

    const handleVerify = async () => {
        setLoading(true);
        setError(null);

        try {
            // 1. Verify Source Repo & Fetch Branches
            const { branches } = await api.verifyRepo(sourceRepoUrl, sourcePat || undefined);

            if (branches.length === 0) {
                throw new Error("Source repository appears to be empty. Please ensure it has at least one branch (e.g. 'main').");
            }

            // 2. If Existing Target, Verify it too
            if (targetRepoMode === 'existing' && targetRepoUrl) {
                try {
                    await api.verifyRepo(targetRepoUrl, targetPat || undefined);
                } catch (err: any) {
                    throw new Error(`Target Repository Error: ${err.response?.data?.detail || "Could not access target repository"}`);
                }
            }

            const sFwString = `${sFw} ${sLang} - ${sTest}`;
            const tFwString = `${tFw} ${tLang} - ${tTest}`;

            setRepoDetails({
                sessionName,
                repoUrl: sourceRepoUrl,
                targetRepoUrl,
                targetRepoMode,
                targetRepoName,
                targetRepoOwner,
                targetRepoVisibility,
                pat: targetRepoMode === 'new' ? targetPat : (targetPat || sourcePat), // Prefer target pat if provided, fallback to source for existing
                sourceFramework: sFwString,
                targetFramework: tFwString,
                branches
            });
            setStep(2);
        } catch (err: any) {
            setError(err.message || err.response?.data?.detail || "Failed to verify repository access.");
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

    const isTargetValid = targetRepoMode === 'existing'
        ? !!targetRepoUrl
        : (!!targetRepoName && !!targetRepoOwner && !!targetPat);

    const isFormValid = sessionName && sourceRepoUrl && sFw && sLang && sTest && tFw && tLang && tTest && isTargetValid;

    const ChipGroup = ({ label, options, selected, onSelect, checkEnabled }: any) => (
        <div className="mb-6">
            <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">{label}</label>
            <div className="flex flex-wrap gap-2">
                {options.map((opt: string) => {
                    const enabled = checkEnabled ? checkEnabled(opt) : true;
                    return (
                        <button
                            key={opt}
                            disabled={!enabled}
                            onClick={() => enabled && onSelect(opt)}
                            className={clsx(
                                "px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 border",
                                selected === opt
                                    ? "bg-blue-600 text-white border-blue-600 shadow-md transform scale-105"
                                    : enabled
                                        ? "bg-white text-gray-600 border-gray-200 hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50"
                                        : "bg-gray-50 text-gray-300 border-gray-100 cursor-not-allowed"
                            )}
                        >
                            {opt}
                        </button>
                    );
                })}
            </div>
        </div>
    );

    return (
        <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in duration-500">
            {/* Header Section */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-5">
                        <Database size={80} />
                    </div>
                    <h3 className="text-xl font-bold mb-6 text-gray-800 flex items-center gap-2">
                        <span className="w-8 h-8 bg-blue-100 text-blue-600 rounded-lg flex items-center justify-center text-sm">1</span>
                        Source Framework
                    </h3>
                    <ChipGroup label="Framework" options={allFrameworks} selected={sFw} onSelect={handleSourceFwChange} />
                    <ChipGroup label="Language" options={allLanguages} selected={sLang} onSelect={handleSourceLangChange} checkEnabled={(o: string) => isEnabled('lang', sFw, '', o)} />
                    <ChipGroup label="Test Engine" options={allTestEngines} selected={sTest} onSelect={setSourceTest} checkEnabled={(o: string) => isEnabled('test', sFw, sLang, o)} />
                </div>

                <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-5">
                        <Globe size={80} />
                    </div>
                    <h3 className="text-xl font-bold mb-6 text-gray-800 flex items-center gap-2">
                        <span className="w-8 h-8 bg-green-100 text-green-600 rounded-lg flex items-center justify-center text-sm">2</span>
                        Target Framework
                    </h3>
                    <ChipGroup label="Framework" options={allFrameworks} selected={tFw} onSelect={handleTargetFwChange} />
                    <ChipGroup label="Language" options={allLanguages} selected={tLang} onSelect={handleTargetLangChange} checkEnabled={(o: string) => isEnabled('lang', tFw, '', o)} />
                    <ChipGroup label="Test Engine" options={allTestEngines} selected={tTest} onSelect={setTargetTest} checkEnabled={(o: string) => isEnabled('test', tFw, tLang, o)} />
                </div>
            </div>

            {/* Session & Source Repo Section */}
            <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
                <h3 className="text-xl font-bold mb-6 text-gray-800 flex items-center gap-2">
                    <span className="w-8 h-8 bg-indigo-100 text-indigo-600 rounded-lg flex items-center justify-center text-sm">3</span>
                    Migration Details
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Session Name</label>
                        <input
                            type="text"
                            placeholder="e.g. Finance App Migration v1"
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                            value={sessionName}
                            onChange={(e) => setSessionName(e.target.value)}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Source Repository URL</label>
                        <div className="relative">
                            <Github className="absolute left-3 top-3.5 text-gray-400" size={18} />
                            <input
                                type="text"
                                placeholder="https://github.com/org/repo.git"
                                className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                                value={sourceRepoUrl}
                                onChange={(e) => setSourceRepoUrl(e.target.value)}
                            />
                        </div>
                    </div>
                    <div className="md:col-span-2">
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Source Personal Access Token (Optional)</label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-3.5 text-gray-400" size={18} />
                            <input
                                type="password"
                                placeholder="ghp_xxxxxxxxxxxx"
                                className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                                value={sourcePat}
                                onChange={(e) => setSourcePat(e.target.value)}
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* Target Repo Selection */}
            <div className="space-y-4">
                <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2 px-2">
                    <span className="w-8 h-8 bg-purple-100 text-purple-600 rounded-lg flex items-center justify-center text-sm">4</span>
                    Target Repository Configuration
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Option A Card */}
                    <div
                        onClick={() => setTargetRepoMode('existing')}
                        className={clsx(
                            "p-6 rounded-2xl border-2 transition-all cursor-pointer relative overflow-hidden group",
                            targetRepoMode === 'existing'
                                ? "border-blue-500 bg-blue-50 shadow-md"
                                : "border-gray-100 bg-white hover:border-blue-200"
                        )}
                    >
                        <div className="flex items-center gap-4 mb-4">
                            <div className={clsx(
                                "w-12 h-12 rounded-xl flex items-center justify-center transition-colors",
                                targetRepoMode === 'existing' ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-400"
                            )}>
                                <GitBranch size={24} />
                            </div>
                            <div>
                                <h4 className="font-bold text-gray-900">Option A</h4>
                                <p className="text-xs text-gray-500 uppercase font-semibold">Existing Repository</p>
                            </div>
                            <div className="ml-auto">
                                <input type="radio" checked={targetRepoMode === 'existing'} readOnly className="h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-300" />
                            </div>
                        </div>

                        {targetRepoMode === 'existing' && (
                            <div className="space-y-4 mt-6 animate-in slide-in-from-top-2">
                                <div>
                                    <label className="block text-xs font-bold text-gray-500 mb-1">Full GitHub URL</label>
                                    <input
                                        type="text"
                                        placeholder="https://github.com/org/target-repo.git"
                                        className="w-full px-3 py-2 rounded-lg border border-blue-200 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-sm"
                                        value={targetRepoUrl}
                                        onChange={(e) => setTargetRepoUrl(e.target.value)}
                                        onClick={(e) => e.stopPropagation()}
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-gray-500 mb-1">Target PAT (Optional)</label>
                                    <input
                                        type="password"
                                        placeholder="If different from source"
                                        className="w-full px-3 py-2 rounded-lg border border-blue-200 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-sm"
                                        value={targetPat}
                                        onChange={(e) => setTargetPat(e.target.value)}
                                        onClick={(e) => e.stopPropagation()}
                                    />
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Option B Card */}
                    <div
                        onClick={() => setTargetRepoMode('new')}
                        className={clsx(
                            "p-6 rounded-2xl border-2 transition-all cursor-pointer relative overflow-hidden group",
                            targetRepoMode === 'new'
                                ? "border-green-500 bg-green-50 shadow-md"
                                : "border-gray-100 bg-white hover:border-green-200"
                        )}
                    >
                        <div className="flex items-center gap-4 mb-4">
                            <div className={clsx(
                                "w-12 h-12 rounded-xl flex items-center justify-center transition-colors",
                                targetRepoMode === 'new' ? "bg-green-600 text-white" : "bg-gray-100 text-gray-400"
                            )}>
                                <PlusCircle size={24} />
                            </div>
                            <div>
                                <h4 className="font-bold text-gray-900">Option B</h4>
                                <p className="text-xs text-gray-500 uppercase font-semibold">Create New Repository</p>
                            </div>
                            <div className="ml-auto">
                                <input type="radio" checked={targetRepoMode === 'new'} readOnly className="h-5 w-5 text-green-600 focus:ring-green-500 border-gray-300" />
                            </div>
                        </div>

                        {targetRepoMode === 'new' && (
                            <div className="space-y-4 mt-6 animate-in slide-in-from-top-2">
                                <div className="grid grid-cols-2 gap-3">
                                    <div>
                                        <label className="block text-xs font-bold text-gray-500 mb-1">Org / User</label>
                                        <input
                                            type="text"
                                            placeholder="e.g. MyOrg"
                                            className="w-full px-3 py-2 rounded-lg border border-green-200 focus:ring-2 focus:ring-green-500 focus:border-green-500 bg-white text-sm"
                                            value={targetRepoOwner}
                                            onChange={(e) => setTargetRepoOwner(e.target.value)}
                                            onClick={(e) => e.stopPropagation()}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-bold text-gray-500 mb-1">Repo Name</label>
                                        <input
                                            type="text"
                                            placeholder="e.g. next-gen-testing"
                                            className="w-full px-3 py-2 rounded-lg border border-green-200 focus:ring-2 focus:ring-green-500 focus:border-green-500 bg-white text-sm"
                                            value={targetRepoName}
                                            onChange={(e) => setTargetRepoName(e.target.value)}
                                            onClick={(e) => e.stopPropagation()}
                                        />
                                    </div>
                                </div>
                                <div className="flex gap-4">
                                    <label className="flex items-center gap-2 cursor-pointer" onClick={(e) => e.stopPropagation()}>
                                        <input type="radio" checked={targetRepoVisibility === 'public'} onChange={() => setTargetRepoVisibility('public')} className="text-green-600" />
                                        <span className="text-sm text-gray-700 flex items-center gap-1"><Globe size={14} /> Public</span>
                                    </label>
                                    <label className="flex items-center gap-2 cursor-pointer" onClick={(e) => e.stopPropagation()}>
                                        <input type="radio" checked={targetRepoVisibility === 'private'} onChange={() => setTargetRepoVisibility('private')} className="text-green-600" />
                                        <span className="text-sm text-gray-700 flex items-center gap-1"><Lock size={14} /> Private</span>
                                    </label>
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-gray-500 mb-1">Target PAT <span className="text-red-500">*</span></label>
                                    <input
                                        type="password"
                                        placeholder="Required for repo creation"
                                        className="w-full px-3 py-2 rounded-lg border border-green-200 focus:ring-2 focus:ring-green-500 focus:border-green-500 bg-white text-sm"
                                        value={targetPat}
                                        onChange={(e) => setTargetPat(e.target.value)}
                                        onClick={(e) => e.stopPropagation()}
                                    />
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-2xl text-sm flex items-start gap-3">
                    <ShieldCheck className="mt-0.5 flex-shrink-0" size={18} />
                    <span>{error}</span>
                </div>
            )}

            <button
                onClick={handleVerify}
                disabled={isLoading || !isFormValid}
                className={clsx(
                    "w-full py-5 rounded-2xl font-bold text-lg flex items-center justify-center gap-3 transition-all transform shadow-xl shadow-blue-200",
                    isFormValid && !isLoading
                        ? "bg-gradient-to-r from-blue-600 to-indigo-700 text-white hover:scale-[1.01] hover:shadow-2xl active:scale-[0.99]"
                        : "bg-gray-200 text-gray-400 cursor-not-allowed"
                )}
            >
                {isLoading ? (
                    <>
                        <Loader2 className="animate-spin" size={24} />
                        <span>Verifying Repository Access...</span>
                    </>
                ) : (
                    <>
                        <ShieldCheck size={24} />
                        <span>Confirm & Continue to Branch Selection</span>
                    </>
                )}
            </button>
        </div>
    );
};

export default RepoConfiguration;
