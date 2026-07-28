CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_name TEXT NOT NULL,
    cpf_cnpj TEXT UNIQUE NOT NULL,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS toll_categories(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL,
description TEXT,
base_price REAL NOT NULL,
vehicle_type TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS toll_gates(
id INTEGER PRIMARY KEY AUTOINCREMENT,
gate_code TEXT UNIQUE NOT NULL,
location TEXT NOT NULL,
highway TEXT NOT NULL,
direction TEXT NOT NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vehicles(
id INTEGER PRIMARY KEY AUTOINCREMENT,
plate TEXT UNIQUE NOT NULL,
brand TEXT,
model TEXT,
year INTEGER,
category_id INTEGER,
FOREIGN KEY (category_id) REFERENCES toll_categories(id)
);

CREATE TABLE IF NOT EXISTS obo_tags(
id INTEGER PRIMARY KEY AUTOINCREMENT,
tag_number TEXT UNIQUE NOT NULL,
account_id INTEGER NOT NULL,
vehicle_id INTEGER NOT NULL,
is_active BOOLEAN DEFAULT 1,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (account_id) REFERENCES accounts(id),
FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
);

CREATE TABLE IF NOT EXISTS transactions(
id INTEGER PRIMARY KEY AUTOINCREMENT,
timestamp TIMESTAMP NOT NULL,
gate_id INTEGER NOT NULL,
plate_read TEXT NOT NULL,
plate_confidence REAL,
vehicle_detected TEXT NOT NULL,
vehicle_confidence REAL,
category_id INTEGER,
toll_amount REAL,
obo_tag_id INTEGER,
status TEXT NOT NULL,
divergence_reason TEXT,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (gate_id) REFERENCES toll_gates(id),
FOREIGN KEY (category_id) REFERENCES toll_categories(id),
FOREIGN KEY (obo_tag_id) REFERENCES obo_tags(id)
);

CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_transactions_plate ON transactions(plate_read);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_vehicles_plate ON vehicles(plate);
CREATE INDEX IF NOT EXISTS idx_obo_tags_tag_number on obo_tags(tag_number);

