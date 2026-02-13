import { create } from 'zustand'
import type { CreateSessionResponse } from '../types'

interface RepoDetails {
    sessionName: string;
    repoUrl: string;
    targetRepoUrl: string;
    pat: string;
    sourceFramework: string;
    targetFramework: string;
    branches: string[];
}

interface MigrationState {
    step: number;
    repoDetails: RepoDetails;
    sessionId: string | null;
    isLoading: boolean;
    error: string | null;

    setStep: (step: number) => void;
    setRepoDetails: (details: RepoDetails) => void;
    setSession: (response: CreateSessionResponse) => void;
    setLoading: (isLoading: boolean) => void;
    setError: (error: string | null) => void;
    reset: () => void;
}

const initialState = {
    step: 1,
    repoDetails: {
        sessionName: '',
        repoUrl: '',
        targetRepoUrl: '',
        pat: '',
        sourceFramework: '',
        targetFramework: '',
        branches: []
    },
    sessionId: null,
    isLoading: false,
    error: null
}

export const useMigrationStore = create<MigrationState>((set) => ({
    ...initialState,

    setStep: (step) => set({ step }),
    setRepoDetails: (repoDetails) => set({ repoDetails }),
    setSession: (response) => set({
        sessionId: response.session_id,
        step: 3
    }),
    setLoading: (isLoading) => set({ isLoading }),
    setError: (error) => set({ error }),
    reset: () => set(initialState)
}))
