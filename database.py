import sqlite3
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from contextlib import contextmanager
import re

EMAIL_RE = re.compile(r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$")
NAME_RE = re.compile(r"^[A-Za-z][A-Z-a-z' -]*[A-Za-z]$")

# PRINT FUNCTIONS
def format_user(u) -> str:
    return f"{u['id']} {u['name']} {u['email']}"

def print_user(u):
    print(format_user(u))

def print_users(rows):
    if not rows:
        print("No users found.")
        return
    for u in rows:
        print_user(u)

def format_invoice(i) -> str:
    due = f" | Due: {i['due_date']}" if i['due_date'] else ""
    return f"Invoice #{i['invoice_id']} | {i['date_issued']}{due} | ${fmt_dollars(i['total'])}"

def print_invoice(i):
    print(format_invoice(i))

def print_invoices(rows):
    if not rows:
        print("No invoices found.")
        return
    for i in rows:
        print_invoice(i)

def format_user_summary(row) -> str:
    return (
        f"User #{row['user_id']} | {row['name']:<15} | "
        f"Invoices: {row['invoice_count']} | Total: {fmt_dollars(row['total_cents'])}"                                          
        )

def print_user_summary(rows):
    if not rows:
        print("No summaries found.")
        return
    print("User Invoice Summary".center(60, "-"))
    for r in rows:
        print(format_user_summary(r))

# HELPERS
def open_db(db_file="mydatabase.db"):
    connect = sqlite3.connect(db_file)
    connect.execute("PRAGMA foreign_keys = ON;")
    connect.execute("PRAGMA recursive_triggers = OFF;")
    connect.row_factory = sqlite3.Row
    return connect

@contextmanager
def db_session(db_file="mydatabase.db"):
    connect = open_db(db_file)
    try:
        yield connect, connect.cursor()
        connect.commit()
    except Exception:
        connect.rollback()
        raise
    finally:
        connect.close()

def normalize_name(name: str) -> str:
    if not name or not isinstance(name, str):
        raise ValueError("Name cannot be empty.")
    name = " ".join(name.strip().split()).title()
    if not NAME_RE.match(name):
        raise ValueError("Invalid name format: only letters, spaces, apostrophes, and hyphens are allowed.")
    return name

def normalize_email(email: str) -> str:
    if not email or not isinstance(email, str):
        raise ValueError("Email cannot be empty.")
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        raise ValueError("Invalid email format")
    return email

def assert_user_exists(cursor, user_id: int) -> None:
    row = cursor.execute("SELECT 1 FROM users WHERE id=?", (user_id,)).fetchone()
    if not row:
        raise ValueError (f"User not found (id={user_id})")
    
def assert_email_unique(cursor, email: str, exclude_user_id: int | None = None) -> None:
    email = email.strip().lower()
    row = cursor.execute(
        "SELECT id FROM users WHERE lower(email) = lower(?)", (email,)
    ).fetchone()
    if row and (exclude_user_id is None or row['id'] != exclude_user_id):
        raise ValueError(f"Email '{(email)}' already exists.")

def validate_total(amount):
    if amount is None:
        raise ValueError("Invoice total is required.")
    if amount < 0:
        raise ValueError("Invoice total cannot be negative.")
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ValueError("Invoice total must be a valid number")
    
    return amount

def to_cents(amount) -> int:
    """Coerce 12.34 / '12.34' -> 1234 (int cents)."""
    return int((Decimal(str(amount)) * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

def fmt_dollars(cents: int) -> str:
    """Convert integer cents (e.g. 35025) → formatted string '$350.25'."""
    return f"${(Decimal(cents) / Decimal(100)).quantize(Decimal('0.01'))}"

def to_iso(date_str: str) -> str:
    """Coerce 'MM-DD-YYYY' / 'MM/DD/YYYY' / 'YYYY-MM-DD' → 'YYYY-MM-DD'."""
    if not date_str:
        return None
    
    formats = ("%m-%d-%Y", "%m/%d/%Y", "%Y-%m-%d")

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    raise ValueError(f"Invalid date format: {date_str} (expected MM-DD-YYYY or MM/DD/YYYY, or YYYY-MM-DD)")

def create_triggers(cursor):
    cursor.executescript("""
    CREATE TRIGGER IF NOT EXISTS trigger_users_updated
    AFTER UPDATE ON users
    BEGIN
        UPDATE users
        SET updated_at = datetime('now', 'localtime')
        WHERE id = NEW.id;
    END;
                         
    CREATE TRIGGER IF NOT EXISTS trigger_invoices_updated
    AFTER UPDATE ON invoices
    BEGIN
        UPDATE invoices
        SET updated_at = datetime('now', 'localtime')
        WHERE invoice_id = NEW.invoice_id;
    END;
    """)

# TABLE CREATION
def create_user_schema(cursor):
    cursor.executescript("""
    -- Users table: stores basic account information.                       
    CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL CHECK (length(trim(name)) > 0),
    email       TEXT    NOT NULL CHECK (length(trim(email)) > 0 ),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
    );
    
    -- Enforce case-insensitive unique emails & index user names.
    CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_nocase ON users(lower(email));
    CREATE INDEX IF NOT EXISTS idx_users_name ON users(name);
    """)

def create_invoice_schema(cursor):
    cursor.executescript("""
    -- Invoices table: records all invoices linked to a user.
    CREATE TABLE IF NOT EXISTS invoices (
    invoice_id      INTEGER PRIMARY KEY,
    user_id         INTEGER NOT NULL,
    date_issued     TEXT    NOT NULL,
    due_date        TEXT,
    total           INTEGER NOT NULL DEFAULT 0 
                    CHECK (total >= 0 AND total = CAST(total AS INTEGER)),
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE -- deletes invoices when user removed
    );
                         
    -- Index frequent queries and filtering patterns.
    CREATE INDEX IF NOT EXISTS idx_invoices_user_id ON invoices(user_id);                         
    CREATE INDEX IF NOT EXISTS idx_invoices_date_issued ON invoices(date_issued);
    CREATE INDEX IF NOT EXISTS idx_invoices_due_date ON invoices(due_date);
    CREATE INDEX IF NOT EXISTS idx_invoices_user_date ON invoices(user_id, date_issued);
    """)

def create_user_summary_view(cursor):
    cursor.executescript("""
    CREATE VIEW IF NOT EXISTS user_invoice_summary AS
    SELECT
        u.id AS user_id,
        u.name, 
        u.email,
        COUNT(i.invoice_id) AS invoice_count,
        COALESCE(SUM(i.total), 0) AS total_cents
    FROM users u
    LEFT JOIN invoices i ON i.user_id = u.id
    GROUP BY u.id, u.name, u.email;
    """)

# ----- REPORT / ANALYTICS -----#
def get_user_invoice_summary(cursor):
    """Return a list of users with their invoice counts and total from view user_invoice_summary"""
    cursor.execute("SELECT * FROM user_invoice_summary ORDER BY user_id")
    return cursor.fetchall()


# ---- User CRUD -----#

# Create
def create_user(cursor, name, email):
    name = normalize_name(name)
    email = normalize_email(email)
    assert_email_unique(cursor, email)
    try:
        cursor.execute("""
            INSERT INTO users (name, email) 
            VALUES (?, ?)
        """, (name, email))
        return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        raise ValueError("Email already exists") from e

# Read
def get_user_by_id(cursor, user_id):
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()

def get_user_by_email(cursor, email):
    cursor.execute("SELECT * FROM users WHERE lower(email) = lower(?)", (email,))
    return cursor.fetchone()

def get_user_id_by_email(cursor, email):
    row = get_user_by_email(cursor, email)
    return row['id'] if row else None

def get_users(cursor, min_total_dollars=0):
    min_cents = to_cents(min_total_dollars)
    cursor.execute("""
        SELECT 
            u.id, 
            u.name, 
            u.email, 
            COALESCE(SUM(i.total), 0) AS total
        FROM users u
        LEFT JOIN invoices i ON i.user_id = u.id
        GROUP BY u.id, u.name, u.email
        HAVING COALESCE(SUM(i.total), 0) >= ?
        ORDER BY u.id
    """, (min_cents,))
    return cursor.fetchall()

# Update
def update_user(cursor, user_id, name=None, email=None):
    updates, params = [], []

    if name:
        updates.append("name = ?")
        params.append(normalize_name(name))
    if email:
        assert_email_unique(cursor, email, exclude_user_id=user_id)
        updates.append("email = ?")
        params.append(normalize_email(email))

    if not updates:
        return False # nothing to update
    
    params.append(user_id)
    query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, tuple(params))
    return cursor.rowcount > 0

# Delete
def delete_user(cursor, user_id):
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    return cursor.rowcount > 0
   
# ---- Invoice CRUD -----#

# Create
def add_invoice_to_user(cursor, user_id, date_issued, total, due_date=None):
    """Attach a new invoice to an existing user with user_id."""
    assert_user_exists(cursor, user_id)
    validate_total(total)
    date_issued = to_iso(date_issued)
    due_date = to_iso(due_date)
    total = to_cents(total)

    cursor.execute("""
        INSERT INTO invoices (user_id, date_issued, due_date, total)
        VALUES (?, ?, ?, ?)
    """, (user_id, date_issued, due_date, total))
    return cursor.lastrowid

# READ
def get_invoice_by_id(cursor, invoice_id):
    cursor.execute("SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id,))
    return cursor.fetchone()

def get_invoices_by_email(cursor, email):
    """Fetch all invoices belonging to a user identified by their email"""
    user_id = get_user_id_by_email(cursor, email)
    if user_id is None:
        return []
    return get_invoices_by_user_id(cursor, user_id)

def get_invoices_by_user_id(cursor, user_id):
    cursor.execute("""
    SELECT invoice_id, user_id, date_issued, due_date, total, created_at, updated_at
    FROM invoices
    WHERE user_id = ?
    ORDER BY date_issued DESC, invoice_id DESC
    """, (user_id,))
    return cursor.fetchall()

def get_invoices_by_user_and_range(cursor, user_id, start_date, end_date):
    start_date = to_iso(start_date)
    end_date = to_iso(end_date)
    cursor.execute("""
    SELECT invoice_id, user_id, date_issued, due_date, total, created_at, updated_at
    FROM invoices
    WHERE user_id = ? AND date_issued BETWEEN ? AND ?
    ORDER BY date_issued DESC, invoice_id DESC
    """, (user_id, start_date, end_date,))
    return cursor.fetchall()

def count_invoices(cursor):
    cursor.execute("SELECT COUNT(*) AS invoice_count FROM invoices")
    return cursor.fetchone()['invoice_count']

def list_invoices(cursor, limit=100, offset=0):
    cursor.execute("""
    SELECT invoice_id, user_id, date_issued, due_date, total, created_at, updated_at
    FROM invoices
    ORDER BY date_issued DESC, invoice_id DESC
    LIMIT ? OFFSET ?
    """, (limit, offset))
    return cursor.fetchall()

def sum_invoices_by_user(cursor, user_id):
    cursor.execute("""
        SELECT COALESCE(SUM(total), 0) AS total_sum
        FROM invoices
        WHERE user_id = ?
    """, (user_id,))
    return cursor.fetchone()['total_sum']

# UPDATE
def update_invoice(cursor, invoice_id, *, date_issued=None, due_date=None, total=None, user_id=None):
    updates, params = [], []
    
    if date_issued:
        updates.append("date_issued = ?")
        params.append(to_iso(date_issued))
    if due_date:
        updates.append("due_date = ?")
        params.append(to_iso(due_date))
    if total:
        validate_total(total)
        updates.append("total = ?")
        params.append(to_cents(total))
    if user_id:
        assert_user_exists(cursor, user_id)
        updates.append("user_id = ?")
        params.append(user_id)

    if not updates:
        return False
    
    params.append(invoice_id)
    query = f"UPDATE invoices SET {', '.join(updates)} WHERE invoice_id = ?"
    cursor.execute(query, tuple(params))
    return cursor.rowcount > 0

# DELETE
def delete_invoice(cursor, invoice_id):
    cursor.execute("DELETE FROM invoices WHERE invoice_id= ?", (invoice_id,))
    return cursor.rowcount > 0


if __name__ == "__main__":

    #----- Database Connection -----#
    with db_session("mydatabase.db") as (connect, cursor):

        # Clear previous table
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS invoices")
        cursor.execute("DROP VIEW IF EXISTS user_invoice_summary")

        # Create new table
        create_user_schema(cursor)
        create_invoice_schema(cursor)
        create_triggers(cursor)
        create_user_summary_view(cursor)

        #----- USER CRUD TEST -----#

        # CREATE
        print("CREATE functions:\n")
        uid = create_user(cursor, "John", "john@example.com")
        print("Created user:", uid)

        # READ
        print("\nREAD functions:\n")
        print("All users:") 
        print_users(get_users(cursor))
        print("Find by email:")
        print_user(get_user_by_email(cursor, "john@example.com"))

        # UPDATE
        print("\nUPDATE functions:\n")
        print("Original user:")
        print_user(get_user_by_id(cursor, uid))
        update_user(cursor, uid, "Alice")
        print("Updated user name:")
        print_user(get_user_by_id(cursor, uid))
        update_user(cursor, uid, email="alice@example.com")
        print("Updated user email:")
        print_user(get_user_by_id(cursor, uid))

        # DELETE
        print("\nDELETE functions:\n")
        print(delete_user(cursor, uid))
        print("After Deletion try getuserid:", get_user_by_id(cursor, uid))
        print("After Deletion try getallusers:", get_users(cursor))

        # ---- INVOICE CRUD TEST -----#

        #CREATE 
        print("\nCREATE functions:\n")
        uid = create_user(cursor, "Jack", "jack@example.com")
        add_invoice_to_user(cursor, uid, "01-20-2025", 200.10)
        add_invoice_to_user(cursor, uid, "03-17-2025", 350.20)

        # READ
        print("\nREAD functions:\n")
        print("Get invoices by user id")
        print_invoices(get_invoices_by_user_id(cursor, uid))
        print("\nGet invoices by email")
        print_invoices(get_invoices_by_email(cursor, "jack@example.com"))
        print("Get user summary from view")
        print_user_summary(get_user_invoice_summary(cursor))

        print(count_invoices(cursor))
        print(fmt_dollars(sum_invoices_by_user(cursor, uid)))

        # UPDATE
        print("\nUPDATE functions:")
        update_invoice(cursor, 1, total = 100.20)
        print("Updated invoice")
        print_invoice(get_invoice_by_id(cursor, 1))

        # DELETE
        print("\nDELETE functions:")
        print(delete_invoice(cursor, 2))
        print_invoices(get_invoices_by_user_id(cursor, uid))
        print(datetime.now().date())