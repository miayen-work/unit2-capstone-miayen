import pytest

from src.db import sql_store


@pytest.fixture
def conn():
    connection = sql_store.get_connection(db_path=":memory:")
    sql_store.initialize_database(connection)
    yield connection
    connection.close()


def test_initialize_database_seeds_customers(conn):
    rows = sql_store.run_query(conn, "SELECT COUNT(*) AS count FROM customers")
    assert rows[0]["count"] == 10


def test_initialize_database_seeds_subscriptions(conn):
    rows = sql_store.run_query(conn, "SELECT COUNT(*) AS count FROM subscriptions")
    assert rows[0]["count"] == 12


def test_run_query_returns_list_of_dicts_with_column_names(conn):
    rows = sql_store.run_query(conn, "SELECT name, company FROM customers WHERE id = 1")
    assert rows == [{"name": "Amara Okafor", "company": "Northwind Traders"}]


def test_subscriptions_join_to_valid_customers(conn):
    rows = sql_store.run_query(
        conn,
        """
        SELECT c.name, s.plan
        FROM subscriptions s
        JOIN customers c ON c.id = s.customer_id
        WHERE s.id = 2
        """,
    )
    assert rows == [{"name": "Liam Chen", "plan": "Enterprise"}]


def test_total_monthly_revenue_for_active_subscriptions(conn):
    rows = sql_store.run_query(
        conn, "SELECT SUM(monthly_amount) AS total FROM subscriptions WHERE status = 'active'"
    )
    assert rows[0]["total"] == pytest.approx(1022.00)


def test_count_active_subscriptions_by_plan(conn):
    rows = sql_store.run_query(
        conn,
        """
        SELECT plan, COUNT(*) AS count
        FROM subscriptions
        WHERE status = 'active'
        GROUP BY plan
        ORDER BY plan
        """,
    )
    assert rows == [
        {"plan": "Basic", "count": 2},
        {"plan": "Enterprise", "count": 4},
        {"plan": "Pro", "count": 4},
    ]


def test_revenue_by_month_seeds_a_full_year_of_regions(conn):
    rows = sql_store.run_query(conn, "SELECT COUNT(*) AS count FROM revenue_by_month")
    assert rows[0]["count"] == 36


def test_q4_2025_revenue_by_region(conn):
    rows = sql_store.run_query(
        conn,
        """
        SELECT region, SUM(revenue) AS total
        FROM revenue_by_month
        WHERE month IN ('2025-10', '2025-11', '2025-12')
        GROUP BY region
        ORDER BY region
        """,
    )
    assert rows == [
        {"region": "APAC", "total": pytest.approx(10550.00)},
        {"region": "EMEA", "total": pytest.approx(10850.00)},
        {"region": "NA", "total": pytest.approx(18650.00)},
    ]


def test_employees_seeded_with_satisfaction_scores(conn):
    rows = sql_store.run_query(conn, "SELECT COUNT(*) AS count, AVG(satisfaction_score) AS avg_score FROM employees")
    assert rows[0]["count"] == 10
    assert rows[0]["avg_score"] == pytest.approx(7.16)


def test_code_review_tickets_meeting_the_48_hour_sla(conn):
    rows = sql_store.run_query(
        conn, "SELECT COUNT(*) AS count FROM code_review_tickets WHERE turnaround_hours <= 48"
    )
    assert rows[0]["count"] == 10


def test_expense_requests_requiring_manager_signoff(conn):
    rows = sql_store.run_query(conn, "SELECT COUNT(*) AS count FROM expense_requests WHERE amount >= 500")
    assert rows[0]["count"] == 8
