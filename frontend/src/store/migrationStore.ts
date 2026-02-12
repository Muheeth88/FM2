import { create } from 'zustand'
import type { MigrationSession, FeatureEntity } from '../types'

interface MigrationState {
    activeSession: MigrationSession | null;
    features: FeatureEntity[];
    isLoading: boolean;
    logs: string[];

    setSession: (session: MigrationSession) => void;
    setFeatures: (features: FeatureEntity[]) => void;
    addLog: (log: string) => void;
    setLoading: (loading: boolean) => void;
}

export const useMigrationStore = create<MigrationState>((set) => ({
    activeSession: null,
    features: [],
    isLoading: false,
    logs: [],

    setSession: (session) => set({ activeSession: session }),
    setFeatures: (features) => set({ features }),
    addLog: (log) => set((state) => ({ logs: [...state.logs, log] })),
    setLoading: (isLoading) => set({ isLoading }),
}))
