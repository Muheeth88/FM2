export interface FileRef {
    path: string;
    hash?: string;
}

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
    target_repo_mode: 'existing' | 'new';
    target_repo_name?: string;
    target_repo_owner?: string;
    target_repo_visibility?: 'public' | 'private';
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
    name: string;
    status: 'MIGRATED' | 'NEEDS_UPDATE' | 'CONFLICTED' | 'NOT_MIGRATED';
    dependent_count: number;
    config_count: number;
    shared_count: number;
    last_migrated: string | null;
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
    dependency_files: FileRef[];
    shared_modules: FileRef[];
    config_dependencies: FileRef[];
    hooks: string[];
}

export interface JavaFileDependency {
    imports: string[];
    package: string | null;
    type: string;
    class_name?: string;
}

export interface BuildDependency {
    name: string | null;
    version: string | null;
    type: string | null;
}

export interface DriverModel {
    driver_type: string | null;
    initialization_pattern: string | null;
    thread_model: string | null;
}

export interface AssertionModel {
    file_path: string;
    assertion_type: string;
    library: string;
}

export interface ConfigFileModel {
    file_path: string;
    type: string;
}

export interface AnalysisResponse {
    session_id: string;
    repo_root: string;
    language: string;
    framework: string;
    build_system: string;
    features: FeatureSummary[];
    dependency_graph: Record<string, JavaFileDependency>;
    build_dependencies: BuildDependency[];
    driver_model: DriverModel | null;
    assertions: AssertionModel[];
    config_files: ConfigFileModel[];
    shared_modules: string[];
    status?: string;
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

