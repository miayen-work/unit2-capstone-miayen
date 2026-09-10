DROP TABLE IF EXISTS subscriptions;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS revenue_by_month;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS code_review_tickets;
DROP TABLE IF EXISTS expense_requests;

CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    company TEXT NOT NULL,
    region TEXT NOT NULL CHECK (region IN ('NA', 'EMEA', 'APAC')),
    signup_date TEXT NOT NULL
);

CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    plan TEXT NOT NULL CHECK (plan IN ('Basic', 'Pro', 'Enterprise')),
    monthly_amount REAL NOT NULL,
    start_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'cancelled')),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE revenue_by_month (
    id INTEGER PRIMARY KEY,
    month TEXT NOT NULL,
    region TEXT NOT NULL CHECK (region IN ('NA', 'EMEA', 'APAC')),
    revenue REAL NOT NULL
);

CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    satisfaction_score REAL NOT NULL,
    survey_date TEXT NOT NULL
);

CREATE TABLE code_review_tickets (
    id INTEGER PRIMARY KEY,
    opened_at TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    turnaround_hours REAL NOT NULL
);

CREATE TABLE expense_requests (
    id INTEGER PRIMARY KEY,
    employee_name TEXT NOT NULL,
    amount REAL NOT NULL,
    request_date TEXT NOT NULL
);

INSERT INTO customers (id, name, company, region, signup_date) VALUES
    (1, 'Amara Okafor', 'Northwind Traders', 'NA', '2025-01-12'),
    (2, 'Liam Chen', 'Globex Corp', 'APAC', '2025-02-03'),
    (3, 'Priya Sharma', 'Initech', 'APAC', '2025-02-20'),
    (4, 'Diego Fernandez', 'Umbrella Retail', 'NA', '2025-03-05'),
    (5, 'Sofia Rossi', 'Wayne Logistics', 'EMEA', '2025-03-18'),
    (6, 'Noah Kim', 'Acme Studios', 'APAC', '2025-04-02'),
    (7, 'Emma Johansson', 'Stark Analytics', 'EMEA', '2025-04-22'),
    (8, 'Yusuf Demir', 'Hooli Software', 'EMEA', '2025-05-10'),
    (9, 'Grace Mwangi', 'Northwind Traders', 'NA', '2025-05-28'),
    (10, 'Ethan Walker', 'Vandelay Industries', 'NA', '2025-06-14');

INSERT INTO subscriptions (id, customer_id, plan, monthly_amount, start_date, status) VALUES
    (1, 1, 'Pro', 49.00, '2025-01-12', 'active'),
    (2, 2, 'Enterprise', 199.00, '2025-02-03', 'active'),
    (3, 3, 'Basic', 15.00, '2025-02-20', 'cancelled'),
    (4, 4, 'Pro', 49.00, '2025-03-05', 'active'),
    (5, 5, 'Enterprise', 199.00, '2025-03-18', 'active'),
    (6, 6, 'Basic', 15.00, '2025-04-02', 'active'),
    (7, 7, 'Pro', 49.00, '2025-04-22', 'cancelled'),
    (8, 8, 'Enterprise', 199.00, '2025-05-10', 'active'),
    (9, 9, 'Pro', 49.00, '2025-05-28', 'active'),
    (10, 10, 'Basic', 15.00, '2025-06-14', 'active'),
    (11, 1, 'Pro', 49.00, '2026-01-12', 'active'),
    (12, 4, 'Enterprise', 199.00, '2026-03-05', 'active');

INSERT INTO revenue_by_month (id, month, region, revenue) VALUES
    (1, '2025-01', 'NA', 4200.00),  (2, '2025-01', 'EMEA', 2100.00),  (3, '2025-01', 'APAC', 1800.00),
    (4, '2025-02', 'NA', 4500.00),  (5, '2025-02', 'EMEA', 2300.00),  (6, '2025-02', 'APAC', 2450.00),
    (7, '2025-03', 'NA', 4650.00),  (8, '2025-03', 'EMEA', 2600.00),  (9, '2025-03', 'APAC', 2500.00),
    (10, '2025-04', 'NA', 4800.00), (11, '2025-04', 'EMEA', 2750.00), (12, '2025-04', 'APAC', 2700.00),
    (13, '2025-05', 'NA', 5100.00), (14, '2025-05', 'EMEA', 2900.00), (15, '2025-05', 'APAC', 2850.00),
    (16, '2025-06', 'NA', 5300.00), (17, '2025-06', 'EMEA', 3050.00), (18, '2025-06', 'APAC', 3000.00),
    (19, '2025-07', 'NA', 5450.00), (20, '2025-07', 'EMEA', 3100.00), (21, '2025-07', 'APAC', 3100.00),
    (22, '2025-08', 'NA', 5600.00), (23, '2025-08', 'EMEA', 3200.00), (24, '2025-08', 'APAC', 3250.00),
    (25, '2025-09', 'NA', 5750.00), (26, '2025-09', 'EMEA', 3350.00), (27, '2025-09', 'APAC', 3300.00),
    (28, '2025-10', 'NA', 6000.00), (29, '2025-10', 'EMEA', 3500.00), (30, '2025-10', 'APAC', 3400.00),
    (31, '2025-11', 'NA', 6200.00), (32, '2025-11', 'EMEA', 3600.00), (33, '2025-11', 'APAC', 3500.00),
    (34, '2025-12', 'NA', 6450.00), (35, '2025-12', 'EMEA', 3750.00), (36, '2025-12', 'APAC', 3650.00);

INSERT INTO employees (id, name, department, satisfaction_score, survey_date) VALUES
    (1, 'Jordan Blake', 'Engineering', 7.8, '2026-06-01'),
    (2, 'Casey Nguyen', 'Engineering', 6.9, '2026-06-01'),
    (3, 'Riley Patel', 'Engineering', 7.2, '2026-06-01'),
    (4, 'Morgan Lee', 'Sales', 7.5, '2026-06-01'),
    (5, 'Alex Rivera', 'Sales', 6.5, '2026-06-01'),
    (6, 'Sam Osei', 'Support', 6.8, '2026-06-01'),
    (7, 'Taylor Brooks', 'Support', 7.0, '2026-06-01'),
    (8, 'Jamie Chowdhury', 'HR', 7.9, '2026-06-01'),
    (9, 'Drew Martinez', 'Marketing', 7.3, '2026-06-01'),
    (10, 'Robin Alvi', 'Marketing', 6.7, '2026-06-01');

INSERT INTO code_review_tickets (id, opened_at, reviewed_at, turnaround_hours) VALUES
    (1, '2026-07-01 09:00', '2026-07-02 10:00', 25.0),
    (2, '2026-07-03 14:00', '2026-07-04 09:00', 19.0),
    (3, '2026-07-05 08:00', '2026-07-08 12:00', 76.0),
    (4, '2026-07-08 11:00', '2026-07-09 15:00', 28.0),
    (5, '2026-07-10 10:00', '2026-07-13 09:00', 71.0),
    (6, '2026-07-14 09:30', '2026-07-15 09:00', 23.5),
    (7, '2026-07-16 13:00', '2026-07-17 16:00', 27.0),
    (8, '2026-07-18 09:00', '2026-07-21 10:00', 73.0),
    (9, '2026-07-21 15:00', '2026-07-22 12:00', 21.0),
    (10, '2026-07-22 09:00', '2026-07-23 08:00', 23.0),
    (11, '2026-07-24 10:00', '2026-07-28 09:00', 95.0),
    (12, '2026-07-25 09:00', '2026-07-26 09:00', 24.0),
    (13, '2026-07-28 14:00', '2026-07-29 16:00', 26.0),
    (14, '2026-07-29 09:00', '2026-07-30 08:00', 23.0),
    (15, '2026-07-30 11:00', '2026-08-02 09:00', 70.0);

INSERT INTO expense_requests (id, employee_name, amount, request_date) VALUES
    (1, 'Jordan Blake', 120.00, '2026-01-15'),
    (2, 'Casey Nguyen', 650.00, '2026-02-10'),
    (3, 'Morgan Lee', 300.00, '2026-03-05'),
    (4, 'Alex Rivera', 5200.00, '2026-03-20'),
    (5, 'Sam Osei', 80.00, '2026-04-03'),
    (6, 'Taylor Brooks', 720.00, '2026-04-18'),
    (7, 'Jamie Chowdhury', 450.00, '2026-05-02'),
    (8, 'Drew Martinez', 900.00, '2026-05-21'),
    (9, 'Robin Alvi', 60.00, '2026-06-05'),
    (10, 'Jordan Blake', 1100.00, '2026-06-19'),
    (11, 'Casey Nguyen', 250.00, '2026-06-28'),
    (12, 'Morgan Lee', 530.00, '2026-07-08'),
    (13, 'Alex Rivera', 90.00, '2026-07-22'),
    (14, 'Sam Osei', 6100.00, '2026-08-01'),
    (15, 'Taylor Brooks', 410.00, '2026-08-14'),
    (16, 'Jamie Chowdhury', 700.00, '2026-08-30'),
    (17, 'Drew Martinez', 150.00, '2026-09-02');
