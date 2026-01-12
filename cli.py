#!/usr/bin/env python3
import typer, sqlite3, database
from datetime import date
from typing import Optional
from contextlib import contextmanager

def user_not_found(user_id: int | None = None):
    if user_id is not None:
        typer.echo(f"User not found (id={user_id})")
    else:
        typer.echo("User not found")

def invoice_not_found(invoice_id: int | None = None):
    if invoice_id is not None:
        typer.echo(f"Invoice not found (id={invoice_id})")
    else:
        typer.echo("Invoice not found")

__version__ = "0.4.1"
app = typer.Typer(help="Command Line Interface for the User_Invoice_Database.\n\n"
                  "Use '--help' after any command for more details.\n\n"
                  "Example: python cli.py db --help")
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
        typer.echo(f"user_invoice_db CLI version {__version__}")
        raise typer.Exit()
        
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()
    
    
    
@contextmanager
def get_connection(db_path="mydatabase.db"):
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
        db_path: str = typer.Option("mydatabase.db", "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        database.create_user_schema(cursor)
        database.create_invoice_schema(cursor)
        connect.commit()
    typer.echo("Initialized database")

@db.command("drop", help="Drop all database tables (does not delete file).")
def drop_db_command(
        db_path: str = typer.Option("mydatabase.db", "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        cursor.execute("DROP TABLE IF EXISTS invoices;")
        cursor.execute("DROP TABLE IF EXISTS users;")
        connect.commit()
    typer.echo(f"Dropped all tables from {db_path}")

@db.command("delete", help="Permanently delete the database file from disk.")
def delete_db_file(
    db_path: str = typer.Option("mydatabase.db", "--db", help="Path to SQLite DB.")
):
    import os  # Used only for safe local file operations (e.g., deleting DB)
    if not os.path.exists(db_path):
        typer.echo(f"No database found at {db_path}")
        raise typer.Exit(code=1)
    
    confirm = typer.confirm(f"Are you sure you want to permanently delete '{db_path}'?")
    if not confirm:
        typer.echo(f"Deletion cancelled")
        raise typer.Exit(code=0)
    
    os.remove(db_path)
    typer.echo(f"Database file '{db_path}' deleted successfully")

# ----- USER COMMANDS ------ 
@users.command("create", help="Create and add a new user to the database.")
def create_user(
    user_name: str = typer.Option(..., "-n", "--name", help="Name of the user."),
    email: str = typer.Option(..., "-e", "--email", help="Email of the user."),
    db_path: str = typer.Option("mydatabase.db", "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        try:
            user_id = database.create_user(cursor, user_name, email)
            connect.commit()
            typer.echo(f"Created user {user_name} <{email}> (id={user_id})")
        except ValueError as ve:
            typer.echo(f"{ve}")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:  
            typer.echo(f"Database error: {e}")
            raise typer.Exit(code=1)
        
@users.command("get", help="Get user by id or email.")
def get_user(
    id: Optional[int] = typer.Option(None, "-i", "--id", help="ID of the user"),
    email_selector: Optional[str] = typer.Option(None, "-e", "--email", help="Email of the user"),
    db_path: str = typer.Option("mydatabase.db", "--db", help="Path to SQLite DB")

):
    if id is None and email_selector is None:
        typer.echo("Please provide either --id or --email")
        raise typer.Exit(code=1)
    
    if id and email_selector:
        typer.echo("Please provide only one of --id or --email (not both)")
        raise typer.Exit(code=1)
    
    with get_connection(db_path) as (connect, cursor):
        try: 
            if id:
                user = database.get_user_by_id(cursor, id)
            else:
                user = database.get_user_by_email(cursor, email_selector)
        except sqlite3.Error as e:
            typer.echo(f"Database error: {e}")
            raise typer.Exit(code=1)
        
    if user:
        typer.echo(f"Found user: {user['name']} ({user['email']})")
    else:
        user_not_found(id)

@users.command("list", help="List all users in the database.")
def list_users(
        db_path: str = typer.Option("mydatabase.db", "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        try:
            users = database.get_users(cursor)
            if not users:
                typer.echo("No users found")
                return
            typer.echo("{:^8} {:^26} {:^17}\n".format("User_ID", "Name", "Email"))
            for u in users:
                typer.echo("{:^7} {:^28} {}".format(u['id'], u['name'], u['email']))
        except sqlite3.Error as e:
            typer.echo(f"Database error: {e}")
            raise typer.Exit(code=1)
        
@users.command("update", help="Update the user's name or email.")
def update_user(
    id: Optional[int] = typer.Option(None, "-i", "--id", help="ID of the user."),
    email_selector: Optional[str] = typer.Option(None, "-e", "--email", help="Email of the user."),
    new_name: Optional[str] = typer.Option(None, "--name", help="Name to update user with."),
    new_email: Optional[str] = typer.Option(None,  "--new-email", help="Email to update user with."),
    db_path: str = typer.Option("mydatabase.db", "--db", help="Path to SQLite DB.")
):
    

    if id is None and email_selector is None:
        typer.echo("Please provide either --id or --email to select a user")
        raise typer.Exit(code=1)
    if id is not None and email_selector is not None:
        typer.echo("Please provide only one of --id or --email (not both)")
        raise typer.Exit(code=1)
    if new_name is None and new_email is None:
        typer.echo("Please provide --name and/or --new-email")
        raise typer.Exit(code=1)
    
    with get_connection(db_path) as (connect, cursor):
        try:
            user = (
                database.get_user_by_id(cursor, id)
                if id is not None
                else database.get_user_by_email(cursor, email_selector)
            )
            if not user:
                selected = f"id={id}" if id is not None else f"email={email_selector}"
                typer.echo(f"User not found ({selected})")
                raise typer.Exit(code=1)
            no_name_change = new_name is None or new_name == user['name']
            no_email_change = new_email is None or new_email == user['email']
            if no_name_change and no_email_change:
                typer.echo("No changes were applied")
                raise typer.Exit(code=1)
            updated = database.update_user(cursor, user['id'], new_name, new_email)
            if not updated:
                typer.echo("No changes were applied")
                raise typer.Exit(code=1)
            connect.commit()
            updated_user = database.get_user_by_id(cursor, user['id'])
            typer.echo(f"Updated: {updated_user['id']}  {updated_user['name']}  {updated_user['email']}")
        except ValueError as ve:
            typer.echo(f"{ve}")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:
            typer.echo(f"Database error: {e}")
            raise typer.Exit(code=1)

@users.command("delete", help="Deletes a single user in the database.")
def delete_user_by_id(
    user_id: int = typer.Option(..., "-i", "--id", help="ID of the user."),
    db_path: str = typer.Option("mydatabase.db", "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        try:
            user_to_delete = database.get_user_by_id(cursor, user_id)
            if not user_to_delete:
                user_not_found(user_id)
                raise typer.Exit(code=1)
            
            was_deleted = database.delete_user(cursor, user_id)
            if not was_deleted:
                typer.echo(f"Nothing deleted for ID {user_id}")
                raise typer.Exit(code=1)
            
            connect.commit()
            typer.echo(f"Deleted user: {user_id}")
        except sqlite3.Error as e:  
            typer.echo(f"Database error: {e}")
            raise typer.Exit(code=1)
        
    

# ----- INVOICES COMMANDS ------ 
@invoices.command("create", help="Create an invoice for a user.")
def create_invoice(
    user_id: int = typer.Option(..., "-i", "--id", help="The user to assign this invoice to."),
    total: float = typer.Option(..., "-t", "--total", help="Invoice total amount."),
    date_issued: Optional[str] = typer.Option(None, "--date-issued", help="Date invoice was issued."),
    date_due: Optional[str] = typer.Option(None, "--date-due", help="Date invoice is due."),
    db_path: str = typer.Option("mydatabase.db", "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        try:
            user = database.get_user_by_id(cursor, user_id)
            if not user:
                user_not_found(user_id)
                raise typer.Exit(code=1)
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
            typer.echo(f"Invoice {invoice_id} created for user {user_id} (total: {total})")

        except sqlite3.Error as e:
            typer.echo(f"Database error: {e}")
            raise typer.Exit(code=1)
        
@invoices.command("list", help="List all invoices and their respective user.")
def list_invoices(
    user_id: Optional[int] = typer.Option(None, "-u", "--user-id", help="Filter by user ID."),
    db_path: str = typer.Option("mydatabase.db", "--db", help="Path to SQLite DB.")):
    with get_connection(db_path) as (connect, cursor):
        try:
            if user_id is not None:

                invoices = database.get_invoices_by_user_id(cursor=cursor, user_id=user_id)
                user = database.get_user_by_id(cursor=cursor, user_id=user_id)

                if not user:
                    user_not_found(user_id)
                    raise typer.Exit(code=1)
                typer.echo(f"\nUser {user['id']}: {user['name']} <{user['email']}>")
                typer.echo("-" * 50)

                if not invoices:
                    typer.echo("No invoices")
                    return
                
                for i in invoices:
                    typer.echo(f"Invoice: {i['invoice_id']} | Total: {database.fmt_dollars(i['total'])} | Issued: {i['date_issued']} | Due: {i['date_due']}")
                return
 
            users = database.get_users(cursor)
            if not users:
                typer.echo("No users found")
                return
            
            for u in users:
                typer.echo(f"\nUser {u['id']}: {u['name']} <{u['email']}>")
                typer.echo("-" * 50)

                invoices = database.get_invoices_by_user_id(cursor=cursor, user_id=u['id'])
                if not invoices:
                    typer.echo("No invoices")
                    continue

                for i in invoices:
                    typer.echo(f"Invoice: {i['invoice_id']} | Total: {database.fmt_dollars(i['total'])} | Issued: {i['date_issued']} | Due: {i['date_due']}")

        except sqlite3.Error as e:
            typer.echo(f"Database error: {e}")
            raise typer.Exit(code=1)


@invoices.command("get", help="Get invoice by its ID.")
def get_invoice(
    invoice_id: int = typer.Option(..., "-i", "--id", help="ID of invoice to get."),
    db_path: str = typer.Option("mydatabase.db", "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        try:
            invoice = database.get_invoice_by_id(cursor=cursor, invoice_id=invoice_id)
            if not invoice:
                invoice_not_found(invoice_id)
                return
            
            typer.echo(
                f"Invoice {invoice['invoice_id']} | "
                f"Total {database.fmt_dollars(invoice['total'])} | "
                f"Issued: {invoice['date_issued']} | "
                f"Due: {invoice['date_due']}"
                )
        except sqlite3.Error as e:
            typer.echo(f"Database error: {e}")
            raise typer.Exit(code=1)
        
@invoices.command("count", help="Count number of invoices.")
def count_invoices(
    user_id: Optional[int] = typer.Option(None, "-u", "--user-id", help="Filter by user ID."),
    db_path: str = typer.Option("mydatabase.db", "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        try:
            if user_id is not None:
                user = database.get_user_by_id(cursor=cursor, user_id=user_id)
                if not user:
                    user_not_found(user_id)
                    raise typer.Exit(code=1)
                count = database.count_invoices_by_user(cursor=cursor, user_id=user_id)
                typer.echo(f"User: {user['name']}\n"
                           f"Total number of invoices: {count}")
                return

            count = database.count_invoices(cursor=cursor)
            typer.echo(f"Total number of invoices: {count}")
        except sqlite3.Error as e:
            typer.echo(f"Database error: {e}")
            raise typer.Exit(code=1)
        
@invoices.command("update", help="Update an invoice's: date_issued, date_due, total, or user.")
def update_invoice(
    invoice_id: int = typer.Option(..., "-i", "--id", help="Invoice id to select."),
    new_date_issued: Optional[str] = typer.Option(None, "--date-issued", help="Date to update date issued."),
    new_date_due: Optional[str] = typer.Option(None, "--date-due", help="Date to update due date."),
    new_total: Optional[float] = typer.Option(None, "--total", help="New total for the invoice."),
    new_user: Optional[int] = typer.Option(None, "--user", help="User to append the invoice to."),
    db_path: str = typer.Option("mydatabase.db", "--db", help="Path to SQLite DB.")
):
    if (
        new_date_issued is None 
        and new_date_due is None 
        and new_total is None 
        and new_user is None
    ):
        typer.echo("Please enter one value to update the invoice with (refer to --help)")
        raise typer.Exit(code=1)

    with get_connection(db_path) as (connect, cursor):
        try:
            invoice = database.get_invoice_by_id(cursor, invoice_id=invoice_id)
            if not invoice:
                invoice_not_found(invoice_id)
                raise typer.Exit(code=1)
            no_new_date_issued = new_date_issued is None or database.to_iso(new_date_issued) == invoice['date_issued']
            no_new_date_due = new_date_due is None or database.to_iso(new_date_due) == invoice['date_due']
            no_new_total = new_total is None or database.to_cents(new_total) == invoice['total']
            no_new_user = new_user is None or new_user == invoice['user_id']
            if no_new_date_issued and no_new_date_due and no_new_total and no_new_user:
                typer.echo("No changes were applied")
                raise typer.Exit(code=1)
            
            updated = database.update_invoice(
                cursor=cursor,
                invoice_id=invoice_id,
                date_issued=new_date_issued,
                date_due=new_date_due,
                total=new_total,
                user_id=new_user
                )
            if not updated:
                typer.echo(f"No changes were applied")
                raise typer.Exit(code=1)

            connect.commit()
            updated_invoice = database.get_invoice_by_id(cursor, invoice_id=invoice_id)
            typer.echo(
                f"Updated Invoice {updated_invoice['invoice_id']} "
                f"user_id={updated_invoice['user_id']}, "
                f"total={database.fmt_dollars(updated_invoice['total'])}, "
                f"date_issued={updated_invoice['date_issued']}, "
                f"date_due={updated_invoice['date_due']}"
            )
        except ValueError as ve:
            typer.echo(f"{ve}")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:
            typer.echo(f"Database error: {e}")
            raise typer.Exit(code=1)
        
@invoices.command("delete", help="Deletes a single invoice from the database.")
def delete_invoice(
    invoice_id: int = typer.Option(..., "-i", "--id", help="ID of the invoice."),
    db_path: str = typer.Option("mydatabase.db", "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        try:
            invoice = database.get_invoice_by_id(cursor=cursor, invoice_id=invoice_id)
            if not invoice:
                invoice_not_found(invoice_id)
                raise typer.Exit(code=1)
            deleted = database.delete_invoice(cursor=cursor, invoice_id=invoice_id)
            if not deleted:
                typer.echo(f"Nothing deleted for invoice {invoice_id}")
                raise typer.Exit(code=1)
            connect.commit()
            typer.echo(f"Deleted invoice {invoice_id}")
        except sqlite3.Error as e:
            typer.echo(f"Database error: {e}")
            raise typer.Exit(code=1)

if __name__ == "__main__":
    app()