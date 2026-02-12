export const MigrationStatus = {
    ACTIVE: "ACTIVE",
    PAUSED: "PAUSED",
    COMPLETED: "COMPLETED"
} as const;

export type MigrationStatus = typeof MigrationStatus[keyof typeof MigrationStatus];

export const FeatureStatus = {
    NOT_MIGRATED: "NOT_MIGRATED",
    SELECTED: "SELECTED",
    MIGRATING: "MIGRATING",
    MIGRATED: "MIGRATED",
    FAILED: "FAILED",
    PARTIALLY_MIGRATED: "PARTIALLY_MIGRATED",
    NEEDS_UPDATE: "NEEDS_UPDATE"
} as const;

export type FeatureStatus = typeof FeatureStatus[keyof typeof FeatureStatus];

export interface MigrationSession {
    session_id: string;
    source_repo: string;
    target_repo: string;
    source_framework: string;
    target_framework: string;
    status: MigrationStatus;
    created_at: string;
}

export interface FeatureEntity {
    feature_id: string;
    feature_name: string;
    source_files: string[];
    status: FeatureStatus;
    last_migrated_commit?: string;
    error_log?: string;
}
