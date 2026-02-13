import axios from 'axios'
import type {
    MigrationSession,
    FeatureEntity,
    VerifyRepoResponse,
    CreateSessionResponse,
    CreateSessionRequest
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
    getFeatures: async (id: string): Promise<FeatureEntity[]> => {
        const response = await apiInstance.get(`/api/session/${id}/features`)
        return response.data
    },
    startMigration: async (id: string, featureIds: string[]) => {
        const response = await apiInstance.post(`/api/session/${id}/migrate`, featureIds)
        return response.data
    }
}
