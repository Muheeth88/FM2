import axios from 'axios'
import type {
    MigrationSession,
    VerifyRepoResponse,
    CreateSessionResponse,
    CreateSessionRequest,
    AnalysisResponse,
    FeatureSummary,
    FeatureDetail
} from '../types'

const API_URL = 'http://localhost:8000'

const apiInstance = axios.create({
    baseURL: API_URL
})

export const api = {
    // Git Service
    verifyRepo: async (repoUrl: string, pat?: string): Promise<VerifyRepoResponse> => {
        const response = await apiInstance.post('/api/git/connect', { repo_url: repoUrl, pat })
        return response.data
    },

    // Session Service
    createSession: async (data: CreateSessionRequest): Promise<CreateSessionResponse> => {
        const response = await apiInstance.post('/api/session', data)
        return response.data
    },

    // Placeholder for future steps
    getSession: async (id: string): Promise<MigrationSession> => {
        const response = await apiInstance.get(`/api/session/${id}`)
        return response.data
    },

    startMigration: async (id: string, featureIds: string[]) => {
        const response = await apiInstance.post(`/api/session/${id}/migrate`, featureIds)
        return response.data
    },

    selectFeatures: async (sessionId: string, featureIds: string[]): Promise<{ status: string }> => {
        const response = await apiInstance.post('/api/session/select-features', {
            session_id: sessionId,
            feature_ids: featureIds
        })
        return response.data
    },

    createMigrationRun: async (sessionId: string): Promise<{ run_id: string, branch_name: string, target_repo_url: string, base_branch: string }> => {
        const response = await apiInstance.post('/api/session/create-run', {
            session_id: sessionId
        })
        return response.data
    },

    // Analysis Service
    runAnalysis: async (sessionId: string): Promise<AnalysisResponse> => {
        const response = await apiInstance.post(`/api/sessions/${sessionId}/analyze`)
        return response.data
    },

    getAnalysisStatus: async (sessionId: string): Promise<{ session_id: string, status: string }> => {
        const response = await apiInstance.get(`/api/sessions/${sessionId}/status`)
        return response.data
    },

    getFullAnalysis: async (sessionId: string): Promise<AnalysisResponse> => {
        const response = await apiInstance.get(`/api/sessions/${sessionId}/full-analysis`)
        return response.data
    },


    getFeatureSummaries: async (sessionId: string): Promise<FeatureSummary[]> => {
        const response = await apiInstance.get(`/api/sessions/${sessionId}/features`)
        return response.data
    },

    getFeatureDetail: async (sessionId: string, featureId: string): Promise<FeatureDetail> => {
        const response = await apiInstance.get(`/api/sessions/${sessionId}/features/${featureId}`)
        return response.data
    }
}
