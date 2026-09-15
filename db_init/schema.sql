CREATE TABLE datasets (
    dataset_id CHAR(36) PRIMARY KEY,
    name TEXT NOT NULL,
    instance TEXT NOT NULL,
    UNIQUE (name, instance)
);
CREATE TABLE customers (
    dataset_id CHAR(36) NOT NULL REFERENCES datasets(dataset_id) ON DELETE CASCADE,
    cust_no INTEGER NOT NULL,
    xcoord INTEGER NOT NULL,
    ycoord INTEGER NOT NULL,
    demand INTEGER NOT NULL,
    ready_time INTEGER NOT NULL,
    due_date INTEGER NOT NULL,
    service_time INTEGER NOT NULL,
    PRIMARY KEY (dataset_id, cust_no)
);
CREATE TABLE runs (
    run_id CHAR(36) PRIMARY KEY,
    dataset_id CHAR(36) NOT NULL REFERENCES datasets(dataset_id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    status TEXT NOT NULL,
    max_trucks INTEGER NOT NULL,
    truck_capacity INTEGER NOT NULL,
    max_time_in_seconds INTEGER,
    random_seed INTEGER,
    total_trucks INTEGER,
    total_distance DOUBLE PRECISION,
    runtime_seconds DOUBLE PRECISION
);
CREATE TABLE arcs (
    run_id CHAR(36) NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    truck_id INTEGER NOT NULL,
    sequence INTEGER NOT NULL,
    cust_no_from INTEGER NOT NULL,
    cust_no_to INTEGER NOT NULL,
    PRIMARY KEY (run_id, cust_no_from, cust_no_to)
);
CREATE INDEX idx_runs_dataset_id ON runs(dataset_id);
CREATE INDEX idx_arcs_run_id ON arcs(run_id);