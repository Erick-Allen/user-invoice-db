# user-invoice-db

A relational database project built with **SQLite** and **Python**. It manages users and their invoices with full **CRUD operations** through a **Command Line Interface (CLI)**.

As of **v0.5.0**, the **CLI** includes support for: 
- Database initialization, reset, and deletion
- User management
- Invoice management
- Rich terminal output
- Dockerized runtime with persistent storage

The CLI is built with [Typer](https://typer.tiangolo.com/)

### Built With
- SQLite 3
- Python 3
- Typer
- Rich
- Docker

---

# Installation (Local)

### Clone the repository and install dependencies:

```bash
git clone https://github.com/Erick-Allen/user-invoice-db.git
cd user-invoice-db
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Verify installation:
 
```bash
userdb --help
```

# Installation (Docker)

### Clone the repository and build the Docker image locally:

```bash
git clone https://github.com/Erick-Allen/user-invoice-db.git
cd user-invoice-db
docker build -t userdb .
```

### Docker Runner:

```bash
./run <command>
```

### Interactive Shell:

```bash
docker run --rm -it -v userdb_data:/data --entrypoint /bin/sh userdb
```

# Usage

**Database commands**

- `userdb db init`
- `userdb db drop`
- `userdb db delete`

**User commands**
- `userdb users create`
- `userdb users list`
- `userdb users get`
- `userdb users update`
- `userdb users delete`

**Invoice commands**
- `userdb invoices create`
- `userdb invoices list`
- `userdb invoices get`
- `userdb invoices count`
- `userdb invoices update`
- `userdb invoices delete`

**Other**
- `userdb --version`

# Demo & Development Scripts

The 'scripts/' folder contains helper scripts for:
- Resetting the database
- Seeding demo users and invoices
- Running a full demo workflow

The demo workflow runs against a dedicated `demo.sqlite` database in the project root and does not affect normal user data.

# Version History
## [v0.5.0]
### Added
- Rich-based terminal output
- Packaged CLI as a global console command (`userdb`)
- Docker support
- Demo automation scripts

## [v0.4.0]
### Added
- Full invoice CRUD support in the CLI

## [v0.3.0]
### Added
- Introduced Typer-based CLI for user and database management

## [v0.1.0]
### Added
- Initial SQLite schema and core CRUD functionality

# Roadmap

## [v0.6.0] (Minor)
- Invoice state, filtering and sorting
- Query usability improvements

## [v0.7.0] (Minor)
- Reporting and analytics commands