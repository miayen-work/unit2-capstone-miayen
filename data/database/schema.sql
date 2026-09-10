DROP TABLE IF EXISTS subscriptions;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    company TEXT NOT NULL,
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

INSERT INTO customers (id, name, company, signup_date) VALUES
    (1, 'Amara Okafor', 'Northwind Traders', '2025-01-12'),
    (2, 'Liam Chen', 'Globex Corp', '2025-02-03'),
    (3, 'Priya Sharma', 'Initech', '2025-02-20'),
    (4, 'Diego Fernandez', 'Umbrella Retail', '2025-03-05'),
    (5, 'Sofia Rossi', 'Wayne Logistics', '2025-03-18'),
    (6, 'Noah Kim', 'Acme Studios', '2025-04-02'),
    (7, 'Emma Johansson', 'Stark Analytics', '2025-04-22'),
    (8, 'Yusuf Demir', 'Hooli Software', '2025-05-10'),
    (9, 'Grace Mwangi', 'Northwind Traders', '2025-05-28'),
    (10, 'Ethan Walker', 'Vandelay Industries', '2025-06-14');

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
