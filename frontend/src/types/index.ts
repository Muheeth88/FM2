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

export interface FeatureSummary {
    feature_id: string;
    feature_name: string;
    status: 'MIGRATED' | 'NEEDS_UPDATE' | 'CONFLICTED' | 'NOT_MIGRATED';
    dependent_file_count: number;
    config_dependency_count: number;
    shared_module_count: number;
    last_migrated_commit: string | null;
}

export interface FeatureDetail {
    feature_id: string;
    feature_name: string;
    file_path: string;
    status: string;
    framework: string;
    language: string;
    last_migrated_commit: string | null;
    tests: TestMethod[];
    dependency_files: string[];
    shared_modules: string[];
    config_dependencies: string[];
    hooks: string[];
}

export interface JavaFileDependency {
    imports: string[];
    package: string | null;
    type: string;
    class_name?: string;
}

export interface AnalysisResponse {
    session_id: string;
    status: string;
    repo_meta?: {
        repo_root: string;
        language: string;
        framework: string;
        build_system: string;
    };
    dependency_graph?: Record<string, JavaFileDependency>;
    shared_modules?: string[];
}




export interface WSProgressMessage {
    type: 'progress' | 'log' | 'error' | 'complete';
    session_id: string;
    step?: string;
    progress?: number;
    message?: string;
    error?: string;
    trace?: string;
}

