from src.validation.sql_validator import validate_sql


def test_allows_simple_select():
    result = validate_sql("SELECT * FROM sales")
    assert result["valid"] is True


def test_allows_select_with_where_clause():
    result = validate_sql("SELECT name, total FROM sales WHERE total > 100")
    assert result["valid"] is True


def test_blocks_drop():
    result = validate_sql("DROP TABLE sales")
    assert result["valid"] is False
    assert "DROP" in result["reason"]


def test_blocks_delete():
    result = validate_sql("DELETE FROM sales WHERE id = 1")
    assert result["valid"] is False
    assert "DELETE" in result["reason"]


def test_blocks_update():
    result = validate_sql("UPDATE sales SET total = 0 WHERE id = 1")
    assert result["valid"] is False
    assert "UPDATE" in result["reason"]


def test_blocks_insert():
    result = validate_sql("INSERT INTO sales VALUES (1, 'x', 100)")
    assert result["valid"] is False
    assert "INSERT" in result["reason"]


def test_blocks_non_select_statement():
    result = validate_sql("CREATE TABLE sales (id INT)")
    assert result["valid"] is False
    assert result["reason"] == "Only SELECT queries are permitted"


def test_blocked_keyword_inside_subquery_is_still_caught():
    result = validate_sql("SELECT * FROM sales WHERE id IN (DELETE FROM logs)")
    assert result["valid"] is False
    assert "DELETE" in result["reason"]
