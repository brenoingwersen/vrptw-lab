CREATE TABLE datasets (
    id CHAR(64) PRIMARY KEY,
    name TEXT NOT NULL,
    instance TEXT NOT NULL,
    UNIQUE (name, instance)
);
CREATE TABLE instances (
    dataset_id CHAR(64) NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    cust_no INTEGER NOT NULL,
    xcoord INTEGER NOT NULL,
    ycoord INTEGER NOT NULL,
    demand INTEGER NOT NULL,
    ready_time INTEGER NOT NULL,
    due_date INTEGER NOT NULL,
    service_time INTEGER NOT NULL,
    UNIQUE (dataset_id, cust_no)
);