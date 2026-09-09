-- Continuity: Production Memory Schema for ClickHouse
-- Designed for high-cardinality analytical queries + agent memory

CREATE DATABASE IF NOT EXISTS production_memory;

-- Core production entity
CREATE TABLE IF NOT EXISTS production_memory.productions (
    production_id String,
    title String,
    type Enum8('feature' = 1, 'series' = 2, 'commercial' = 3, 'documentary' = 4),
    status Enum8('pre_prod' = 1, 'principal' = 2, 'post' = 3, 'delivery' = 4, 'released' = 5),
    start_date Date,
    target_delivery Date,
    budget_usd Float64,
    created_at DateTime64(3) DEFAULT now64(3)
) ENGINE = MergeTree()
ORDER BY (production_id);

-- Shots / scenes (the atomic unit of continuity)
CREATE TABLE IF NOT EXISTS production_memory.shots (
    shot_id String,
    production_id String,
    scene_number String,
    shot_number String,
    description String,
    location String,
    int_ext Enum8('INT' = 1, 'EXT' = 2, 'INT/EXT' = 3),
    time_of_day Enum8('DAY' = 1, 'NIGHT' = 2, 'DAWN' = 3, 'DUSK' = 4),
    status Enum8('not_started' = 1, 'in_progress' = 2, 'completed' = 3, 'needs_pickup' = 4, 'omitted' = 5),
    planned_duration_sec UInt32,
    actual_duration_sec Nullable(UInt32),
    principal_date Nullable(Date),
    created_at DateTime64(3) DEFAULT now64(3),
    updated_at DateTime64(3) DEFAULT now64(3)
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (production_id, scene_number, shot_number);

-- Assets (wardrobe, props, VFX plates, etc.) with versioning
CREATE TABLE IF NOT EXISTS production_memory.assets (
    asset_id String,
    production_id String,
    asset_type Enum8('wardrobe' = 1, 'prop' = 2, 'set' = 3, 'vfx' = 4, 'makeup' = 5, 'vehicle' = 6, 'other' = 7),
    name String,
    description String,
    current_version UInt16,
    status Enum8('available' = 1, 'in_use' = 2, 'damaged' = 3, 'lost' = 4, 'retired' = 5),
    location String,
    last_seen_shot_id Nullable(String),
    created_at DateTime64(3) DEFAULT now64(3),
    updated_at DateTime64(3) DEFAULT now64(3)
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (production_id, asset_type, asset_id);

-- Continuity notes (the heart of the system)
CREATE TABLE IF NOT EXISTS production_memory.continuity_notes (
    note_id String,
    production_id String,
    shot_id String,
    note_type Enum8('wardrobe' = 1, 'prop' = 2, 'makeup' = 3, 'action' = 4, 'dialogue' = 5, 'geography' = 6, 'timeline' = 7, 'other' = 8),
    severity Enum8('info' = 1, 'warning' = 2, 'critical' = 3),
    description String,
    related_asset_id Nullable(String),
    reported_by String,
    resolved UInt8 DEFAULT 0,
    resolution_note Nullable(String),
    created_at DateTime64(3) DEFAULT now64(3),
    resolved_at Nullable(DateTime64(3))
) ENGINE = MergeTree()
ORDER BY (production_id, shot_id, created_at);

-- Schedule / call sheet events
CREATE TABLE IF NOT EXISTS production_memory.schedule_events (
    event_id String,
    production_id String,
    event_type Enum8('shoot' = 1, 'rehearsal' = 2, 'tech_scout' = 3, 'pickup' = 4, 'meeting' = 5, 'other' = 6),
    title String,
    location String,
    start_time DateTime64(3),
    end_time DateTime64(3),
    unit String DEFAULT '1st Unit',
    status Enum8('scheduled' = 1, 'in_progress' = 2, 'completed' = 3, 'cancelled' = 4, 'delayed' = 5),
    notes String,
    created_at DateTime64(3) DEFAULT now64(3)
) ENGINE = MergeTree()
ORDER BY (production_id, start_time);

-- Cost / budget events (for risk analysis)
CREATE TABLE IF NOT EXISTS production_memory.cost_events (
    event_id String,
    production_id String,
    category Enum8('vfx' = 1, 'talent' = 2, 'locations' = 3, 'crew' = 4, 'equipment' = 5, 'post' = 6, 'other' = 7),
    amount_usd Float64,
    description String,
    related_shot_id Nullable(String),
    incurred_at DateTime64(3),
    created_at DateTime64(3) DEFAULT now64(3)
) ENGINE = MergeTree()
ORDER BY (production_id, incurred_at);

-- Agent decision / recommendation audit trail (agent memory)
CREATE TABLE IF NOT EXISTS production_memory.agent_actions (
    action_id String,
    production_id String,
    agent_name String,
    action_type Enum8('query' = 1, 'recommendation' = 2, 'alert' = 3, 'update' = 4, 'summary' = 5),
    input_context String,
    output_summary String,
    confidence Float32,
    related_entities Array(String),
    created_at DateTime64(3) DEFAULT now64(3)
) ENGINE = MergeTree()
ORDER BY (production_id, created_at);

-- Materialized view style helper for open critical issues
-- (agents can query this for quick situational awareness)
CREATE TABLE IF NOT EXISTS production_memory.open_critical_issues
(
    production_id String,
    note_id String,
    shot_id String,
    note_type String,
    description String,
    created_at DateTime64(3)
) ENGINE = MergeTree()
ORDER BY (production_id, created_at);
