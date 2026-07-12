-- Statements service schema.
-- NOTE: .claude/settings.json denies writes to ./migrations/** — schema changes
-- go through a reviewed migration, not an ad-hoc agent edit.

CREATE TABLE IF NOT EXISTS customers (
    id    INTEGER PRIMARY KEY,
    name  TEXT NOT NULL,
    email TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS accounts (
    id             INTEGER PRIMARY KEY,
    account_number TEXT NOT NULL,
    customer_id    INTEGER NOT NULL REFERENCES customers(id),
    kind           TEXT NOT NULL DEFAULT 'checking'
);

CREATE TABLE IF NOT EXISTS transactions (
    id          INTEGER PRIMARY KEY,
    account_id  INTEGER NOT NULL REFERENCES accounts(id),
    posted_date TEXT NOT NULL,        -- ISO date
    amount_cents INTEGER NOT NULL,    -- money as integer cents
    merchant    TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS statement_exports (
    id          INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    account_id  INTEGER NOT NULL,
    exported_at TEXT NOT NULL
);
