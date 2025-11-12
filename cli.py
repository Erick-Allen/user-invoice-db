#!/usr/bin/env python3
import typer, sqlite3, database
from typing import Optional
from contextlib import contextmanager

__version__ = "0.3.0"
app = typer.Typer(help="Command Line Interface for the User_Invoice_Database.\n\n"
                  "Use '--help' after any command for more details.\n\n"
                  "Example: python cli.py db --help")
db = typer.Typer(help="Database commands")
users = typer.Typer(help="User commands")
invoices = typer.Typer(help="Invoice commands")
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

@db.command("init", help="Initialize a new database with all tables and schema.")
def init_db_command(
        db_path: str = typer.Option("mydatabase.db", "--db", help="Path to SQLite DB")
):
    with get_connection(db_path) as (connect, cursor):
        database.create_user_schema(cursor)
        database.create_invoice_schema(cursor)
        connect.commit()
    typer.echo("Initialized database.")

@db.command("drop", help="Drop all database tables (does not delete file).")
def drop_db_command(
        db_path: str = typer.Option("mydatabase.db", "--db", help="Path to SQLite DB")
):
    with get_connection(db_path) as (connect, cursor):
        cursor.execute("DROP TABLE IF EXISTS invoices;")
        cursor.execute("DROP TABLE IF EXISTS users;")
        connect.commit()
    typer.echo(f"Dropped all tables from {db_path}")

@db.command("delete", help="Permanently delete the database file from disk.")
def delete_db_file(
    db_path: str = typer.Option("mydatabase.db", "--db", help="Path to SQLite DB")
):
    import os  # Used only for safe local file operations (e.g., deleting DB)
    if not os.path.exists(db_path):
        typer.echo(f"No database found at {db_path}")
        raise typer.Exit(code=1)
    
    confirm = typer.confirm(f"Are you sure you want to permanently delete '{db_path}'?")
    if not confirm:
        typer.echo(f"Deletion cancelled.")
        raise typer.Exit(code=0)
    
    os.remove(db_path)
    typer.echo(f"Database file '{db_path}' deleted successfully.")

# ----- USER COMMANDS ------ 
@users.command("create", help="Create and add a new user to the database.")
def create_user(
    user_name: str = typer.Option(..., "-n", "--name", help="Name of the user"),
    email: str = typer.Option(..., "-e", "--email", help="Email of the user"),
    db_path: str = typer.Option("mydatabase.db", "--db", help="Path to SQLite DB")
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
        
@users.command("get", help="Get user by id or email")
def get_user(
    id: Optional[int] = typer.Option(None, "-i", "--id", help="ID of the user"),
    email_selector: Optional[str] = typer.Option(None, "-e", "--email", help="Email of the user"),
    db_path: str = typer.Option("mydatabase.db", "--db", help="Path to SQLite DB")

):
    if not id and not email_selector:
        typer.echo("Please provide either --id or --email")
        raise typer.Exit(code=1)
    
    if id and email_selector:
        typer.echo("Please provide only one of --id or --email (not both).")
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
        typer.echo("User not found.")

@users.command("list", help="List all users in the database.")
def list_users(
        db_path: str = typer.Option("mydatabase.db", "--db", help="Path to SQLite DB")
):
    with get_connection(db_path) as (connect, cursor):
        try:
            users = database.get_users(cursor)
            if not users:
                typer.echo("No users found.")
                return
            typer.echo("{:^8} {:^26} {:^17}\n".format("User_ID", "Name", "Email"))
            for u in users:
                typer.echo("{:^7} {:^28} {}".format(u['id'], u['name'], u['email']))
        except sqlite3.Error as e:
            typer.echo(f"Database error: {e}")
            raise typer.Exit(code=1)
        
@users.command("update", help="Update the users name or email.")
def update_user(
    id: Optional[int] = typer.Option(None, "-i", "--id", help="ID of the user"),
    email_selector: Optional[str] = typer.Option(None, "-e", "--email", help="Email of the user"),
    new_name: Optional[str] = typer.Option(None, "--name", help="Name to update user with"),
    new_email: Optional[str] = typer.Option(None,  "--new-email", help="Email to update user with"),
    db_path: str = typer.Option("mydatabase.db", "--db", help="Path to SQLite DB")
):
    

    if not id and not email_selector:
        typer.echo("Please provide either --id or --email to select a user.")
        raise typer.Exit(code=1)
    if id and email_selector:
        typer.echo("Please provide only one of --id or --email (not both).")
        raise typer.Exit(code=1)
    if not new_name and not new_email:
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
                typer.echo("No changes were applied.")
                raise typer.Exit(code=1)
            updated = database.update_user(cursor, user['id'], new_name, new_email)
            if not updated:
                typer.echo("No changes were applied.")
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
    user_id: int = typer.Option(..., "-i", "--id", help="ID of the user"),
    db_path: str = typer.Option("mydatabase.db", "--db", help="Path to SQLite DB")
):
    with get_connection(db_path) as (connect, cursor):
        try:
            user_to_delete = database.get_user_by_id(cursor, user_id)
            if not user_to_delete:
                typer.echo(f"No user found with ID {user_id}")
                raise typer.Exit(code=1)
            
            was_deleted = database.delete_user(cursor, user_id)
            if not was_deleted:
                typer.echo(f"Nothing deleted for ID {user_id}")
                raise typer.Exit(code=1)
            
            connect.commit()
            typer.echo(f"Deleted user: {user_id}")
        except sqlite3.Error as e:  
            typer.echo(f"Database error {e}")
            raise typer.Exit(code=1)
        
@invoices.command("info")
def invoices_info():
    typer.echo("Invoice commands will be available in later version.")


if __name__ == "__main__":
    app()