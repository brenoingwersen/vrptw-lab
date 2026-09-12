CREATE TABLE datasets (
    dataset_id CHAR(64) PRIMARY KEY,
    name TEXT NOT NULL,
    instance TEXT NOT NULL,
    UNIQUE (name, instance)
);
CREATE TABLE instances (
    dataset_id CHAR(64) NOT NULL REFERENCES datasets(dataset_id) ON DELETE CASCADE,
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
    run_id CHAR(64) PRIMARY KEY,
    dataset_id CHAR(64) NOT NULL REFERENCES datasets(dataset_id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    status TEXT NOT NULL,
    max_trucks INTEGER NOT NULL,
    truck_capacity INTEGER NOT NULL,
    total_trucks INTEGER,
    total_distance DOUBLE PRECISION,
    UNIQUE (dataset_id, created_at)
);
CREATE TABLE stops (
    run_id CHAR(64) NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    truck_id INTEGER NOT NULL,
    cust_no INTEGER NOT NULL,
    sequence INTEGER NOT NULL,
    PRIMARY KEY (run_id, truck_id, sequence),
);