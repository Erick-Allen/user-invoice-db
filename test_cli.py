import re
import pytest
from typer.testing import CliRunner

from cli import app

USER_ID_REGEX = re.compile(r"id=(\d+)")
INVOICE_ID_REGEX = re.compile(r"Invoice\s+(\d+)")

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def temp_db(runner, tmp_path):
    db_path = tmp_path / "test.db"
    result = runner.invoke(app, ["db", "init", "--db", str(db_path)])
    assert result.exit_code == 0, result.stdout
    return str(db_path)

@pytest.fixture
def user_john(runner, temp_db):
    result = runner.invoke(app, ["users", "create", "--name", "John", "--email", "john@test.com", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    match = USER_ID_REGEX.search(result.stdout)
    assert match, f"Could not parse user id from output: {result.stdout}"
    return int(match.group(1))

@pytest.fixture
def user_alice(runner, temp_db):
    result = runner.invoke(app, ["users", "create", "--name", "Alice", "--email", "alice@test.com", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    match = USER_ID_REGEX.search(result.stdout)
    assert match, f"Could not parse user id from output: {result.stdout}"
    return int(match.group(1))

@pytest.fixture
def invoice_john(runner, temp_db, user_john):
    result = runner.invoke(app, ["invoices", "create", "--id", str(user_john), "--total", "1234", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    match = INVOICE_ID_REGEX.search(result.stdout)
    assert match, f"Could not parse invoice id from output: {result.stdout}"
    return int(match.group(1))

@pytest.fixture
def invoice_alice(runner, temp_db, user_alice):
    result = runner.invoke(app, ["invoices", "create", "--id", str(user_alice), "--total", "9999", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    match = INVOICE_ID_REGEX.search(result.stdout)
    assert match, f"Could not parse invoice id from output: {result.stdout}"
    return int(match.group(1))

# Interface Tests
def test_cli_help_commands(runner):
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    expected_commands = ["--version", "users", "invoices", "db"]
    for cmd in expected_commands:
        assert cmd in result.stdout

def test_users_help_commands(runner):
    result = runner.invoke(app, ["users", "--help"])
    assert result.exit_code == 0
    expected_commands = ["create", "delete", "get", "list", "update"]
    for cmd in expected_commands:
        assert cmd in result.stdout

def test_invoices_help_commands(runner):
    result = runner.invoke(app, ["invoices", "--help"])
    assert result.exit_code == 0
    expected_commands = ["create", "list", "get", "count", "update", "delete"]
    for cmd in expected_commands:
        assert cmd in result.stdout

def test_db_help_commands(runner):
    result = runner.invoke(app, ["db", "--help"])
    assert result.exit_code == 0
    expected_commands = ["init", "drop", "delete"]
    for cmd in expected_commands:
        assert cmd in result.stdout

# Behavorial (Integration) Tests

# User
def test_create_and_get_user(user_john, runner, temp_db):
    result = runner.invoke(app, ["users", "get", "--email", "john@test.com", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert "John" in result.stdout

def test_user_update(user_john, runner, temp_db):
    result = runner.invoke(app, ["users", "update", "--email", "john@test.com", "--name", "Tommy", "--new-email", "tommy@gmail.com", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    result = runner.invoke(app, ["users", "get", "--email", "tommy@gmail.com", "--db", temp_db])
    assert "Tommy" in result.stdout
    assert "tommy@gmail.com" in result.stdout

    result = runner.invoke(app, ["users", "get", "--email", "john@test.com", "--db", temp_db])
    assert "User not found" in result.stdout

def test_user_list(user_john, user_alice, runner, temp_db):
    result = runner.invoke(app, ["users", "list", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert "John" in result.stdout
    assert "Alice" in result.stdout

def test_user_delete(user_john, runner, temp_db):
    result = runner.invoke(app, ["users", "delete", "--id", str(user_john), "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    result = runner.invoke(app, ["users", "get", "--email", "john@test.com", "--db", temp_db])
    assert "User not found" in result.stdout

#Invoice
def test_create_and_get_invoice(user_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "get", "--id", str(invoice_john), "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert f"Invoice {invoice_john}" in result.stdout

def test_invoice_update(user_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "update", "--id", str(invoice_john), "--total", "9876", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    result = runner.invoke(app, ["invoices", "get", "--id", str(invoice_john), "--db", temp_db])
    assert f"Invoice {invoice_john}" in result.stdout
    assert "Total $9876" in result.stdout

def test_invoice_list_all(user_john, invoice_john, user_alice, invoice_alice, runner, temp_db):
    result = runner.invoke(app, ["invoices", "list", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert f"Invoice: {invoice_john}" in result.stdout
    assert f"Invoice: {invoice_alice}" in result.stdout

def test_invoice_list_one_user(user_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "create", "--id", str(user_john), "--total", "777", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    result = runner.invoke(app, ["invoices", "list", "--user-id", str(user_john), "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert "Total: $1234" in result.stdout, result.stdout
    assert "Total: $777" in result.stdout, result.stdout

def test_invoice_count_all(user_john, invoice_john, user_alice, invoice_alice, runner, temp_db):
    result = runner.invoke(app, ["invoices", "count", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert "number of invoices: 2" in result.stdout

def test_invoice_count_one_user(user_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "count", "--user-id", str(user_john), "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert "number of invoices: 1" in result.stdout

def test_invoice_delete(user_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "delete", "--id", str(invoice_john), "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    result = runner.invoke(app, ["invoices", "get", "--id", str(invoice_john), "--db", temp_db])
    assert "Invoice not found" in result.stdout

# Negative Tests

# User
def test_create_user_duplicate_email_fails(user_john, runner, temp_db):
    result = runner.invoke(app, ["users", "create", "--name", "Johnny", "--email", "john@test.com", "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "already exists" in result.stdout

def test_user_get_invalid_id_fails(user_john, runner, temp_db):
    result = runner.invoke(app, ["users", "get", "--id", "-9999", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert "User not found" in result.stdout


def test_user_update_no_fields_fails(user_john, runner, temp_db):
    result = runner.invoke(app, ["users", "update", "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "provide either --id or --email" in result.stdout

def test_user_update_invalid_id_fails(user_john, runner, temp_db):
    result = runner.invoke(app, ["users", "update", "--id", "-9999", "--name", "tommy", "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "User not found" in result.stdout

def test_user_delete_invalid_id_fails(user_john, runner, temp_db):
    result = runner.invoke(app, ["users", "delete", "--id", "-9999", "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "User not found" in result.stdout

# Invoice
def test_create_invoice_invalid_user_fails(user_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "create", "--id", "-9999", "--total", "1234", "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "User not found" in result.stdout

def test_get_invoice_invalid_id_fails(user_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "get", "--id", "-9999", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert "Invoice not found" in result.stdout

def test_update_invoice_no_fields_fails(user_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "update", "--id", str(invoice_john), "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "Please enter one" in result.stdout

def test_update_invalid_invoice_id_fails(user_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "update", "--id", "-9999", "--total", "1234", "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "Invoice not found" in result.stdout

def test_delete_invoice_invalid_fails(user_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "delete", "--id", "-9999", "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "Invoice not found" in result.stdout