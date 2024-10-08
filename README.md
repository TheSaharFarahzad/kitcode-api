# Kitcode API

This is a Django-based e-commerce platform for educational content.


## 1. <a name='CloneRepository'></a>Clone the Repository

To clone the repository initially:

```bash
git clone https://github.com/TheSaharFarahzad/kitcode.git
```

If you have already cloned the repository and want to update it, use the following command:

```bash
git pull origin master
```


## 2. System Requirements

You'll need Python 3, PostgreSQL to be installed on your machine:

On Linux, via apt:

```bash
sudo apt-get update
sudo apt-get install python3 python3-pip postgresql
```

Install Python on Windows:

1. Download the latest version of Python from [python.org](https://www.python.org/downloads/).
2. Run the installer and ensure to select "Add Python to PATH" during installation to add Python to your system's PATH for use in Command Prompt.

Install PostgreSQL on Windows:

1. Visit the official PostgreSQL website: [PostgreSQL Downloads](https://www.postgresql.org/download/).
2. Download the Windows installer (.exe file).
3. Run the downloaded installer file.
4. Follow the installation steps to select components (like PostgreSQL server and pgAdmin), choose an installation directory, configure the database server, and set passwords.
6. Complete the installation process as guided by the installer.


## 3. <a name='PostgreSQL'></a>PostgreSQL

If your database is not set up, you'll need to configure it. You can use your favorite PostgreSQL admin tool or the command line interface (CLI):

Windows:
Open Command Prompt or PowerShell as administrator. Navigate to the PostgreSQL bin directory:
```bash
psql -U postgres
```

Linux:
Open the terminal. Switch to the PostgreSQL superuser and open PostgreSQL CLI:
```bash
sudo -u postgres psql
```

After accessing the PostgreSQL command line, use the following SQL commands to create a user, set passwords, configure the database, and manage privileges:

```sql

-- Create a new PostgreSQL user with a secure password:
-- Replace DATABASE_USER and DATABASE_PASSWORD with username and password in .env file.
CREATE USER DATABASE_USER WITH PASSWORD 'DATABASE_PASSWORD';

-- Create a new database and assign ownership to the new user:
-- Replace DATABASE_NAME with the name of your database.
CREATE DATABASE DATABASE_NAME OWNER DATABASE_USER;

-- Exit PostgreSQL:
\q

```

## 4. Environment Variables Setup

To manage sensitive information like database credentials, create a `.env` file in the root directory of your project and add your database credentials.

**NOTE**: Ensure this file is kept private and not tracked by Git.


## 5. <a name='Setup'></a>Setup

In this section we explain how you can set up the project.

### 5.2.1 Python Environment

For maintaining a clean development environment, it's recommended to use a virtual environment for installing application-specific packages. There are various methods to create virtual environments, such as using Pipenv. Below is an example demonstrating how to set up a virtual environment using native tools:

Windows:
```bash
cd kitcode
python -m venv venv
```

Linux:
```bash
cd kitcode
python3 -m venv .venv
```

**NOTE**: Ensure you add your virtual environment directory to .gitignore to avoid committing unnecessary files to your repository.

Then, install the requirements in your virtual environment. But first, you need to activate the environment:

Windows:
```bash
venv\Scripts\activate
```

Linux:
```bash
source .venv/bin/activate
```

To install all requirements for local development, run the following command:

```bash
pip install -r requirements/local.txt
```

To deactivate the virtual environment you just need to run the following commands:

```bash
deactivate
```


### 5.2.2 Run Server

If you want to run the app locally, you need to execute the `migrate` command to create your database tables. Make sure you have set up your local database as described in the PostgreSQL section:

```bash
python manage.py migrate
```

Then run the following command:

```bash
python manage.py runserver
```

You can see the application in a browser, at [http://localhost:8000](http://localhost:8000).

