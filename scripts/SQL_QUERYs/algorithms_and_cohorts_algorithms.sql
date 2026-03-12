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
    task_id INTEGER
);

CREATE TABLE cohort_algorithms (
    cohort_id INTEGER REFERENCES cohorts(id) ON DELETE CASCADE,
    algorithm_id INTEGER REFERENCES algorithms(id) ON DELETE CASCADE,
    PRIMARY KEY (cohort_id, algorithm_id)
    
);

ALTER TABLE algorithms
ADD COLUMN status_task TEXT;
ALTER TABLE algorithms
ADD COLUMN subtask_id INTEGER;

ALTER TABLE algorithms
ADD COLUMN status_subtask TEXT;

Alter TABLE public.algorithms
Drop COLUMN IF EXISTS new_dataframe_vantage_id;
ALTER TABLE public.algorithms
ADD COLUMN col_var TEXT;

ALTER TABLE public.algorithms
ADD COLUMN row_var_list TEXT;