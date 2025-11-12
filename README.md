# user-invoice-db

A relational database project built with **SQLite** and **Python**. It manages users and their invoices with full **CRUD operations**, data validation, triggers, and summary views.

As of **v0.3.0**, the project includes a complete **Command Line Interface (CLI)** built with [Typer](https://typer.tiangolo.com/), enabling direct database interaction through the terminal.


### Built With
- SQLite 3
- Python 3

---

# Installation

Clone the repository and install dependices:

```bash
git clone https://github.com/Erick-Allen/user-invoice-db.git
cd user-invoice-db
pip install -r requirements.txt
```

# Usage

**Database commands**

- `python cli.py db init`
- `python cli.py db drop`
- `python cli.py db delete`

**User commands**
- `python cli.py users create`
- `python cli.py users list`
- `python cli.py users get`
- `python cli.py users update`
- `python cli.py users delete`

**Other**
- `python cli.py version`

## Version History
## [v0.3.0]
### Added
- Added Typer-based CLI for user CRUD and database management

## [v0.2.1]
### Added
- Added negative test cases and enhanced test coverage.

## [v0.2.0]
### Added
- Unit tests for all user and invoice CRUD functions.

## [v0.1.0]
### Added
- Initial database setup with schema creation and core CRUD logic.
