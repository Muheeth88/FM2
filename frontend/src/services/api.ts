import axios from 'axios'
import type { MigrationSession, FeatureEntity } from '../types'

const API_URL = 'http://localhost:8000'

export const api = {
    createSession: async (data: { source_repo: string; target_repo: string; source_framework: string; target_framework: string }): Promise<MigrationSession> => {
        const response = await axios.post(`${API_URL}/session/create`, data)
        return response.data
    },
    getSession: async (id: string): Promise<MigrationSession> => {
        const response = await axios.get(`${API_URL}/session/${id}`)
        return response.data
    },
    getFeatures: async (id: string): Promise<FeatureEntity[]> => {
        const response = await axios.get(`${API_URL}/session/${id}/features`)
        return response.data
    },
    startMigration: async (id: string, featureIds: string[]) => {
        const response = await axios.post(`${API_URL}/session/${id}/migrate`, featureIds)
        return response.data
    }
}
