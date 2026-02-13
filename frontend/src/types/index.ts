export interface RepoDetails {
    repo_url: string;
    pat?: string;
}

export interface VerifyRepoRequest {
    repo_url: string;
    pat?: string;
}

export interface VerifyRepoResponse {
    branches: string[];
    message: string;
}

export interface MigrationSession {
    id: string;
    source_repo_url: string;
    target_repo_url?: string;
    source_framework: string;
    target_framework: string;
    base_branch: string;
    status: string;
    created_at: string;
}

export interface CreateSessionRequest {
    name: string;
    source_repo_url: string;
    target_repo_url?: string;
    source_framework: string;
    target_framework: string;
    base_branch: string;
    pat?: string;
}

export interface CreateSessionResponse {
    session_id: string;
    status: string;
}
