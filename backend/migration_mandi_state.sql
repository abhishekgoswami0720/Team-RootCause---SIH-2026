-- Run this against an already-existing database (one where schema.sql was
-- already applied) to add mandi_state without touching existing tables/data.
-- If you're running schema.sql fresh on a new DB, you don't need this file —
-- it's already included there.

CREATE TABLE IF NOT EXISTS mandi_state (
    id INT PRIMARY KEY DEFAULT 1,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    halted_reason VARCHAR(200),
    halted_at TIMESTAMP,
    resumed_at TIMESTAMP,
    CONSTRAINT single_row CHECK (id = 1)
);

INSERT INTO mandi_state (id, active)
VALUES (1, TRUE)
ON CONFLICT (id) DO NOTHING;
