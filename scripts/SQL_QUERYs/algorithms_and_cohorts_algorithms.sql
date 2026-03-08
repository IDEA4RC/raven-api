DROP TABLE IF EXISTS cohort_algorithms;
DROP TABLE IF EXISTS algorithms;

CREATE TABLE algorithms (
    id SERIAL PRIMARY KEY,
    method_name VARCHAR,
    description TEXT,
    creation_date TIMESTAMPTZ DEFAULT NOW(),
    version_date TIMESTAMPTZ,
    input TEXT,
    output TEXT,
    new_dataframe_vantage_id INTEGER,
    task_id INTEGER
);

CREATE TABLE cohort_algorithms (
    cohort_id INTEGER REFERENCES cohorts(id) ON DELETE CASCADE,
    algorithm_id INTEGER REFERENCES algorithms(id) ON DELETE CASCADE,
    PRIMARY KEY (cohort_id, algorithm_id)
);