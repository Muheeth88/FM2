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

export interface TestMethod {
    name: string;
    annotations: string[];
}

export interface Feature {
    feature_name: string;
    file_path: string;
    tests: TestMethod[];
    lifecycle_hooks: string[];
    framework: string;
    language: string;
    status: 'MIGRATED' | 'NEEDS_UPDATE' | 'CONFLICTED' | 'NOT_MIGRATED';
}

export interface JavaFileDependency {
    package: string | null;
    imports: string[];
    class_name: string | null;
    type: string;
}

export interface AnalysisResponse {
    session_id: string;
    dependency_graph: Record<string, JavaFileDependency>;
    features: Feature[];
}

