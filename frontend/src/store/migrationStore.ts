import { create } from 'zustand'
import type { CreateSessionResponse } from '../types'

interface RepoDetails {
    sessionName: string;
    repoUrl: string;
    targetRepoUrl: string;
    targetRepoMode: 'existing' | 'new';
    targetRepoName?: string;
    targetRepoOwner?: string;
    targetRepoVisibility?: 'public' | 'private';
    pat: string;
    sourceFramework: string;
    targetFramework: string;
    targetFrameworkId?: string;
    targetLanguage?: string;
    targetEngine?: string;
    branches: string[];
}

interface MigrationState {
    step: number;
    repoDetails: RepoDetails;
    sessionId: string | null;
    isLoading: boolean;
    error: string | null;
    foundationStatus: 'PENDING' | 'SUCCESS' | 'MISSING' | 'ERROR';

    setStep: (step: number) => void;
    setRepoDetails: (details: RepoDetails) => void;
    setSession: (response: CreateSessionResponse) => void;
    setLoading: (isLoading: boolean) => void;
    setError: (error: string | null) => void;
    setFoundationStatus: (status: 'PENDING' | 'SUCCESS' | 'MISSING' | 'ERROR') => void;
    nextStep: () => void;
    reset: () => void;
}

const initialState = {
    step: 1,
    repoDetails: {
        sessionName: '',
        repoUrl: '',
        targetRepoUrl: '',
        targetRepoMode: 'existing' as 'existing' | 'new',
        targetRepoName: '',
        targetRepoOwner: '',
        targetRepoVisibility: 'public' as 'public' | 'private',
        pat: '',
        sourceFramework: '',
        targetFramework: '',
        targetFrameworkId: '',
        targetLanguage: '',
        targetEngine: '',
        branches: []
    },
    sessionId: null,
    isLoading: false,
    error: null,
    foundationStatus: 'PENDING' as 'PENDING' | 'SUCCESS' | 'MISSING' | 'ERROR'
}

export const useMigrationStore = create<MigrationState>((set) => ({
    ...initialState,

    setStep: (step) => set({ step }),
    setRepoDetails: (repoDetails) => set({ repoDetails }),
    setSession: (response) => set({
        sessionId: response.session_id,
        step: 3
    }),
    nextStep: () => set((state) => ({ step: state.step + 1 })),
    setLoading: (isLoading) => set({ isLoading }),
    setError: (error) => set({ error }),
    setFoundationStatus: (foundationStatus) => set({ foundationStatus }),
    reset: () => set(initialState)
}))
