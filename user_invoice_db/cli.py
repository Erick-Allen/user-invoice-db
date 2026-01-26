import typer, sqlite3 
from . import database
from datetime import date
from typing import Optional
from contextlib import contextmanager
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from rich.theme import Theme

THEME = Theme({
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "danger": "bold red",
    "accent": "magenta",
    "highlight": "cyan",
    "muted": "dim",
    "title": "bold",
})

console = Console(highlight=False, theme=THEME)

#HELPERS

###USERS
def require_user(cursor, user_id: int | None = None, email: str | None = None) -> dict:
    if user_id is None and email is None:
        raise ValueError("require_user needs user_id or email")
    elif user_id is not None:
        user = database.get_user_by_id(cursor, user_id)
    elif email is not None:
        user = database.get_user_by_email(cursor, email)

    if user:
        return user
    else:
        user_not_found(user_id, email)
        raise typer.Exit(code=1)
    
def user_not_found(user_id: int | None = None, email: str | None = None) -> None:
    if user_id is not None:
        console.print(f"User not found (id={user_id})", style="warning")
    elif email is not None:
        console.print(f"User not found (email={email})", style="warning")
    else:
        console.print("User not found", style="warning")    
    
def no_users_found() -> None:
    console.print("No users found", style="warning")

def print_user_summary(user: dict) -> None:
    console.print("[title]ID   NAME     EMAIL[/title]")
    console.print(
        f"{user['id']:<4} "
        f"{user['name']:<8} "
        f"{user['email']}\n"
    )

def print_users_table(users) -> None:
    table = Table(title="Users")
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Email")

    for u in users:
        table.add_row(str(u['id']), u['name'], u['email'])
    console.print(table)

def ensure_user_has_changes(user, new_name, new_email) -> None:
    no_name_change = new_name is None or new_name == user['name']
    no_email_change = new_email is None or new_email == user['email']
    if no_name_change and no_email_change:
        console.print("No changes were applied", style="warning")
        raise typer.Exit(code=1)

def delete_user_record(cursor, user_id) -> None:
    deleted = database.delete_user(cursor, user_id)
    if not deleted:
        console.print(f"Nothing deleted for ID {user_id}", style="error")
        raise typer.Exit(code=1)

###INVOICES    
def require_invoice(cursor, invoice_id: int) -> dict:
    invoice = database.get_invoice_by_id(cursor=cursor, invoice_id=invoice_id)
    if invoice:
        return invoice
    else:
        invoice_not_found(invoice_id)
        raise typer.Exit(code=1)

def invoice_not_found(invoice_id: int | None = None) -> None:
    if invoice_id is not None:
        console.print(f"Invoice not found (id={invoice_id})", style ="warning")
    else:
        console.print("Invoice not found", style="warning")

def no_invoices_found() -> None:
    console.print("No invoices found", style="warning")

def print_invoice_table(invoice) -> None:
    table = Table(title=f"Invoice (id={invoice['invoice_id']})")
    table.add_column("ID", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("Issued", justify="center")
    table.add_column("Due", justify="center")

    due = database.fmt_optional(invoice["date_due"])
    if due == "-":
            due = "[muted]-[/muted]"
    table.add_row(str(invoice['invoice_id']), str(database.fmt_dollars(invoice['total'])), str(invoice['date_issued']), due)
    console.print(table)

def print_invoices_table(user, invoices) -> None:
    table = Table(title=f"[title]{user} Invoices[/title]")
    table.add_column("ID", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("Issued", justify="center", style="muted")
    table.add_column("Due", justify="center")

    for i in invoices:
        due = database.fmt_optional(i["date_due"])
        if due == "-":
            due = "[muted]-[/muted]"
        table.add_row(str(i['invoice_id']), str(database.fmt_dollars(i['total'])), str(i['date_issued']), due)
    console.print(table)

def print_invoice_count(count, user) -> None:
    if user:
        console.print(f"Invoices [accent]for[/accent] {user['name']}: [highlight]{count}[/highlight]")
    else:
        console.print(f"Total number of invoices: [highlight]{count}[/highlight]")

def display_user_and_invoices(user, invoices) -> None:
    print_user_summary(user)
    if invoices:
        print_invoices_table(user['name'], invoices)
    else:
        no_invoices_found()
        print()

def delete_invoice_record(cursor, invoice_id) -> None:
    deleted = database.delete_invoice(cursor=cursor, invoice_id=invoice_id)
    if not deleted:
        console.print(f"Nothing deleted for invoice {invoice_id}", style="error")
        raise typer.Exit(code=1)

###ERRORS
def db_error(e: Exception) -> None:
    console.print(f"Database error: {e}", style="error")
    raise typer.Exit(code=1)

def ensure_invoice_has_changes(invoice, new_date_due, new_date_issued, new_total, new_user) -> None:
    no_new_date_issued = new_date_issued is None or database.to_iso(new_date_issued) == invoice['date_issued']
    no_new_date_due = new_date_due is None or database.to_iso(new_date_due) == invoice['date_due']
    no_new_total = new_total is None or database.to_cents(new_total) == invoice['total']
    no_new_user = new_user is None or new_user == invoice['user_id']

    if no_new_date_issued and no_new_date_due and no_new_total and no_new_user:
        console.print("No changes were applied", style="warning")
        raise typer.Exit(code=1)

#CLI APP
__version__ = "0.5.0"
app = typer.Typer(help="Command Line Interface for the User_Invoice_Database.\n\n"
                  "Use '--help' after any command for more details.\n\n"
                  "Example: userdb db --help")
db = typer.Typer(help="Database commands.")
users = typer.Typer(help="User commands.")
invoices = typer.Typer(help="Invoice commands.")
app.add_typer(db, name="db")
app.add_typer(users, name="users")
app.add_typer(invoices, name="invoices")

@app.callback(invoke_without_command=True)
def main(
        ctx: typer.Context,
        version: bool = typer.Option(None, "--version", "-v", 
        help="Show the CLI version and exit.", is_eager=True
    )
):
    if version:
        console.print(f"user_invoice_db CLI version [highlight]{__version__}[/highlight]")
        raise typer.Exit()
        
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit()
    
    
    
@contextmanager
def get_connection(db_path=database.DB_PATH):
    connect = sqlite3.connect(db_path)
    connect.row_factory = sqlite3.Row
    cursor = connect.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    try:
        yield connect, cursor
    finally:
        connect.close()

# ----- DATABASE COMMANDS ------ 
@db.command("init", help="Initialize a new database with all tables and schema.")
def init_db_command(
        db_path: str = typer.Option(database.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        database.create_user_schema(cursor)
        database.create_invoice_schema(cursor)
        connect.commit()
    console.print("Initialized database", style="success")

@db.command("drop", help="Drop all database tables (does not delete file).")
def drop_db_command(
        db_path: str = typer.Option(database.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        cursor.execute("DROP TABLE IF EXISTS invoices;")
        cursor.execute("DROP TABLE IF EXISTS users;")
        connect.commit()
    console.print(f"Dropped all tables from {db_path}", style="success")

@db.command("delete", help="Permanently delete the database file from disk.")
def delete_db_file(
    db_path: str = typer.Option(database.DB_PATH, "--db", help="Path to SQLite DB.")
):
    import os  # Used only for safe local file operations (e.g., deleting DB)
    if not os.path.exists(db_path):
        console.print(f"No database found at {db_path}", style="error")
        raise typer.Exit(code=1)
    
    confirm = Confirm.ask(f"[danger]Are you sure you want to permanently delete '{db_path}'?[/danger]")
    if not confirm:
        console.print(f"Deletion cancelled", style="warning")
        raise typer.Exit(code=0)
    
    os.remove(db_path)
    console.print(f"Database file '{db_path}' deleted successfully", style="success")

# ----- USER COMMANDS ------ 
@users.command("create", help="Create and add a new user to the database.")
def create_user(
    user_name: str = typer.Option(..., "-n", "--name", help="Name of the user."),
    email: str = typer.Option(..., "-e", "--email", help="Email of the user."),
    db_path: str = typer.Option(database.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        try:
            user_id = database.create_user(cursor, user_name, email)
            connect.commit()

            user = database.get_user_by_id(cursor, user_id)

        except ValueError as ve:
            console.print(f"{ve}", style="error")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:  
            db_error(e)
        
    console.print(f"Created user {user['name']} <{user['email']}> (id={user['id']})", style="success")
        
@users.command("get", help="Get user by id or email.")
def get_user(
    id: Optional[int] = typer.Option(None, "-i", "--id", help="ID of the user"),
    email_selector: Optional[str] = typer.Option(None, "-e", "--email", help="Email of the user"),
    db_path: str = typer.Option(database.DB_PATH, "--db", help="Path to SQLite DB")

):
    if id is None and email_selector is None:
        console.print("Please provide either --id or --email", style="warning")
        raise typer.Exit(code=1)
    
    if id and email_selector:
        console.print("Please provide only one of --id or --email (not both)", style="warning")
        raise typer.Exit(code=1)
    
    with get_connection(db_path) as (connect, cursor):
        try: 
            if id:
                user = database.get_user_by_id(cursor, id)
            else:
                user = database.get_user_by_email(cursor, email_selector)

        except sqlite3.Error as e:
            db_error(e)
        
    if user:
        print_user_summary(user)
    else:
        user_not_found(id)

@users.command("list", help="List all users in the database.")
def list_users(
        db_path: str = typer.Option(database.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        try:
            users = database.get_users(cursor)
            
        except sqlite3.Error as e:
            db_error(e)

    if users:
        print_users_table(users)
    else:
        console.print("No users found", style="warning")
        

@users.command("update", help="Update the user's name or email.")
def update_user(
    id: Optional[int] = typer.Option(None, "-i", "--id", help="ID of the user."),
    email_selector: Optional[str] = typer.Option(None, "-e", "--email", help="Email of the user."),
    new_name: Optional[str] = typer.Option(None, "--name", help="Name to update user with."),
    new_email: Optional[str] = typer.Option(None,  "--new-email", help="Email to update user with."),
    db_path: str = typer.Option(database.DB_PATH, "--db", help="Path to SQLite DB.")
):
    updated_user = None

    if id is None and email_selector is None:
        console.print("Please provide either --id or --email to select a user", style="warning")
        raise typer.Exit(code=1)
    if id is not None and email_selector is not None:
        console.print("Please provide only one of --id or --email (not both)", style="warning")
        raise typer.Exit(code=1)
    if new_name is None and new_email is None:
        console.print("Please provide --name and/or --new-email", style="warning")
        raise typer.Exit(code=1)
    
    with get_connection(db_path) as (connect, cursor):
        try:
            user = require_user(cursor, id, email_selector)
            
            ensure_user_has_changes(user, new_name, new_email)
            
            updated = database.update_user(cursor, user['id'], new_name, new_email)
                
            connect.commit()
            updated_user = database.get_user_by_id(cursor, user['id'])

        except ValueError as ve:
            console.print(f"{ve}", style="error")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:
            db_error(e)

    if updated_user:
        print_user_summary(updated_user)
    else:
        console.print("Updated user, but failed to reload record.", style="error")
        raise typer.Exit(code=1)
    


@users.command("delete", help="Deletes a single user in the database.")
def delete_user_by_id(
    user_id: int = typer.Option(..., "-i", "--id", help="ID of the user."),
    db_path: str = typer.Option(database.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        try:
            require_user(cursor, user_id)

            delete_user_record(cursor, user_id)

            connect.commit()
            console.print(f"Deleted user: (id={user_id})", style="success")

        except sqlite3.Error as e:  
            db_error(e)
        
    

# ----- INVOICES COMMANDS ------ 
@invoices.command("create", help="Create an invoice for a user.")
def create_invoice(
    user_id: int = typer.Option(..., "-i", "--id", help="The user to assign this invoice to."),
    total: float = typer.Option(..., "-t", "--total", help="Invoice total amount."),
    date_issued: Optional[str] = typer.Option(None, "--date-issued", help="Date invoice was issued."),
    date_due: Optional[str] = typer.Option(None, "--date-due", help="Date invoice is due."),
    db_path: str = typer.Option(database.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        try:
            require_user(cursor, user_id)
            
            if date_issued is None:
                date_issued = date.today().isoformat()

            invoice_id = database.add_invoice_to_user(
                cursor, 
                user_id=user_id, 
                total=total,
                date_issued=date_issued, 
                date_due=date_due
                )
            connect.commit()

        except sqlite3.Error as e:
            db_error(e)

    console.print(f"Invoice {invoice_id} created for user {user_id} (total: {total})", style="success")


@invoices.command("list", help="List all invoices and their respective user.")
def list_invoices(
    user_id: Optional[int] = typer.Option(None, "-u", "--user-id", help="Filter by user ID."),
    db_path: str = typer.Option(database.DB_PATH, "--db", help="Path to SQLite DB.")):
    
    user = None
    users = None
    user_invoices = None
    users_with_invoices: list[tuple[dict, list]] = []

    with get_connection(db_path) as (connect, cursor):
        try:
            if user_id is not None:
                user = database.get_user_by_id(cursor=cursor, user_id=user_id)
                user_invoices = database.get_invoices_by_user_id(cursor=cursor, user_id=user_id)
            else:
                users = database.get_users(cursor)
                for u in users:
                    invs = database.get_invoices_by_user_id(cursor, u['id'])
                    users_with_invoices.append((u, invs))
        except sqlite3.Error as e:
            db_error(e)

    if user_id is not None:
        if user:
            display_user_and_invoices(user, user_invoices)
        else:
            user_not_found(user_id)
        return
    
    if users:
        for user, invs in (users_with_invoices):
            display_user_and_invoices(user, invs)
    else:
        no_users_found()
            

@invoices.command("get", help="Get invoice by its ID.")
def get_invoice(
    invoice_id: int = typer.Option(..., "-i", "--id", help="ID of invoice to get."),
    db_path: str = typer.Option(database.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        try:
            invoice = database.get_invoice_by_id(cursor, invoice_id)

        except sqlite3.Error as e:
            db_error(e)

        if invoice:
            print_invoice_table(invoice)
        else:
            invoice_not_found(invoice_id)
            
        
@invoices.command("count", help="Count number of invoices.")
def count_invoices(
    user_id: Optional[int] = typer.Option(None, "-u", "--user-id", help="Filter by user ID."),
    db_path: str = typer.Option(database.DB_PATH, "--db", help="Path to SQLite DB.")
):
    user = None
    count = 0
    
    with get_connection(db_path) as (_, cursor):
        try:
            if user_id is not None:
                user = database.get_user_by_id(cursor, user_id)
                if user:
                    count = database.count_invoices_by_user(cursor=cursor, user_id=user_id)
            else:
                count = database.count_invoices(cursor)      

        except sqlite3.Error as e:
            db_error(e)

    if user_id is not None and user is None:
        user_not_found(user_id)
        return
    print_invoice_count(count, user)
    
        
@invoices.command("update", help="Update an invoice's: date_issued, date_due, total, or user.")
def update_invoice(
    invoice_id: int = typer.Option(..., "-i", "--id", help="Invoice id to select."),
    new_date_issued: Optional[str] = typer.Option(None, "--date-issued", help="Date to update date issued."),
    new_date_due: Optional[str] = typer.Option(None, "--date-due", help="Date to update due date."),
    new_total: Optional[float] = typer.Option(None, "--total", help="New total for the invoice."),
    new_user: Optional[int] = typer.Option(None, "--user", help="User to append the invoice to."),
    db_path: str = typer.Option(database.DB_PATH, "--db", help="Path to SQLite DB.")
):
    updated_invoice = None

    if (
        new_date_issued is None 
        and new_date_due is None 
        and new_total is None 
        and new_user is None
    ):
        console.print("Please enter one value to update the invoice with (refer to --help)", style="warning")
        raise typer.Exit(code=1)

    with get_connection(db_path) as (connect, cursor):
        try:
            invoice = require_invoice(cursor, invoice_id)
            ensure_invoice_has_changes(invoice, new_date_due, new_date_issued, new_total, new_user)
            
            updated = database.update_invoice(
                cursor=cursor,
                invoice_id=invoice_id,
                date_issued=new_date_issued,
                date_due=new_date_due,
                total=new_total,
                user_id=new_user
                )
            
            if not updated:
                 console.print("No changes were applied", style="warning")
                 raise typer.Exit(code=1)
            
            connect.commit()
            updated_invoice = database.get_invoice_by_id(cursor, invoice_id=invoice_id)
            
        except ValueError as ve:
            console.print(f"{ve}", style="error")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:
            db_error(e)

    if updated_invoice:
        console.print("Update Successful", style="success")
        print_invoice_table(updated_invoice)
    else:
        console.print("Updated invoice, but failed to reload record.", style="error")
        raise typer.Exit(code=1)


        
@invoices.command("delete", help="Deletes a single invoice from the database.")
def delete_invoice(
    invoice_id: int = typer.Option(..., "-i", "--id", help="ID of the invoice."),
    db_path: str = typer.Option(database.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        try:
            require_invoice(cursor, invoice_id)
            
            delete_invoice_record(cursor, invoice_id)
            connect.commit()
            
        except sqlite3.Error as e:
            db_error(e)

    console.print(f"Deleted invoice {invoice_id}", style="success")