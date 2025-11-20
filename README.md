# user-invoice-db

A relational database project built with **SQLite** and **Python**. It manages users and their invoices with full **CRUD operations**, data validation, triggers, and summary views.

As of **v0.4.0**, the project includes complete **Command Line Interface (CLI)** support for: 
- Database initialization, resetting and deletion
- User management
- Invoice management

The CLI is built with [Typer](https://typer.tiangolo.com/)

### Built With
- SQLite 3
- Python 3
- Typer

---

# Installation

Clone the repository and install dependencies:

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

**Invoice commands**
- `python cli.py invoices create`
- `python cli.py invoices list`
- `python cli.py invoices get`
- `python cli.py invoices count`
- `python cli.py invoices update`
- `python cli.py invoices delete`

**Other**
- `python cli.py --version`

# Version History
## [v0.4.0]
### Added
- Full invoice CRUD support in the CLI

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

# Roadmap

## [v0.4.1] (Patch)
- Add full automated CLI test suite

## [v0.5.0] (Minor)
- Add Rich-based colored and formatted CLI output