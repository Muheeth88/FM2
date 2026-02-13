export interface MigrationSession {
    id: string;
    source_repo_url: string;
    source_framework: string;
    target_framework: string;
    base_branch: string;
    status: string;
}

export interface FeatureEntity {
    id: string;
    name: string;
    status: 'MIGRATED' | 'NOT_MIGRATED' | 'IN_PROGRESS' | 'FAILED';
    test_files: string[];
}

export interface VerifyRepoResponse {
    branches: string[];
    message: string;
}

export interface CreateSessionRequest {
    source_repo_url: string;
    source_framework: string;
    target_framework: string;
    base_branch: string;
    pat?: string;
}

export interface CreateSessionResponse {
    session_id: string;
    status: string;
}
