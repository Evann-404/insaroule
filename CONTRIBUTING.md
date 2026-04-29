# How to contribute to the project
Fork the repository under your namespace (by clicking the fork button on the top right). Clone your forked repository to your local machine using the following command:

```bash
git clone <your_forked_repository_url>
```

Then `cd` into the project directory:

```bash
cd insaroule
```

## Setup your environment
This project is using `uv` to manage dependencies and run the application. To get started, you [need to install `uv`](https://docs.astral.sh/uv/#installation). Once you have `uv` installed, run the following command that will create a virtual environment and install the dependencies (including development dependencies) in it:

```bash
uv sync --dev
```

## Setup pre-commit hooks
This project uses pre-commit hooks to ensure code quality and consistency. Pre-commit hooks are scripts that run automatically before you commit your changes to the repository. They can help catch common mistakes and enforce coding standards. To setup pre-commit hooks, you need to run the following command:

```bash
uv run pre-commit install
```

## Setup the PostgreSQL database
This project relies on PostgreSQL with PostGIS for spatial data handling. You need to have PostgreSQL and PostGIS installed on your machine. To do so, you need to install the following packages using your package manager:

**On Debian/Ubuntu:**
```bash
sudo apt install \                                                 
    postgresql-16 \        
    postgresql-16-postgis-3 \
    postgresql-server-dev-16
```

**On Fedora/Red Hat:**
 
```bash
sudo dnf install postgresql-server postgresql-contrib postgis
sudo postgresql-setup --initdb
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

Log into the PostgreSQL database as the `postgres` user and create a new database `insaroule`: 

**On Debian/Ubuntu:**
 
```bash
sudo -i -u postgres
createdb insaroule
```
 
**On Fedora/Red Hat:**
 
```bash
sudo -u postgres createdb insaroule
sudo -u postgres psql
```
While you are logged in as the `postgres` user, you will also create a user `insaroule_user` with password `insaroule_password` to access the database. You can do this by running the following commands in the PostgreSQL shell (by running `psql` command):

```sql
CREATE USER insaroule_user WITH PASSWORD 'insaroule_pass';
GRANT ALL PRIVILEGES ON DATABASE insaroule TO insaroule_user;
```

Connect to the `insaroule` database as the `postgres` user and grant the necessary privileges to the `insaroule_user` user:

```sql
\c insaroule
GRANT CREATE ON SCHEMA public TO insaroule_user;
```

While you are at it, you can also create a PostGIS extension for the `insaroule` database by running the following command in the PostgreSQL shell:

```sql
CREATE EXTENSION postgis;
```

**On local development environment only**, you will also need to add SUPERUSER permissions to your database user for units tests to run.

```sql
ALTER USER insaroule_user SUPERUSER
```

You can now quit the PostgreSQL shell by running the following command:

```sql
\q
```

and exit the `postgres` user by running:

```bash
exit
```

You will also need to do the database migration to bring the database up to date with the current schema by running the following command:

```bash
uv run poe migrate
```

> [!IMPORTANT]
> When an update involves database modifications, you may need to run this command again to apply those changes.

## Setup Redis
This project uses Redis to handle background tasks and chat messages. You need to have Redis installed and running on your machine.

You can install Redis using your package manager. For example, on Ubuntu, you can run the following commands:

**On Debian/Ubuntu:**
```bash
sudo apt-get install lsb-release curl gpg
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
sudo chmod 644 /usr/share/keyrings/redis-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list
sudo apt-get update
sudo apt-get install redis
sudo systemctl enable redis-server
sudo systemctl start redis-server
```
 
**On Fedora/Red Hat:**
 
```bash
sudo dnf install redis
sudo systemctl enable redis
sudo systemctl start redis
```
 
> **Note Fedora/Red Hat:** The package may be provided as `valkey-compat-redis` depending on your Fedora version. In all cases, the systemd service is called `redis` (not `redis-server` as on Ubuntu).

Redis will start automatically, and it should restart at boot time. If Redis doesn't start across reboots, you may need to manually enable it:

```bash
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

Sources: [Redis on Linux documentation](https://redis.io/docs/latest/operate/oss_and_stack/install/archive/install-redis/install-redis-on-linux/)

## Setup the application
Before running the application, you need to configure it. To do so, you need to copy or rename the `.env.dist` file to `.env`
You can then open the file to edit its property as needed. In particular, you will need to change this line setting `DJANGO_DEBUG` to `True`:

```dotenv
DJANGO_DEBUG=True
```

You will then be able to create your first superuser by running the following command: 

```bash
uv run poe createsuperuser
```

## Static files
To make static files works (likes images, CSS and Javascript) you need to gather it by running the following command:

```bash
uv run poe collectstatic
```

> [!NOTE]
> When editing or creating a file in the `project/static` folder, the previous command needs to be run again.

## Run the background tasks worker
As it was mentioned above, this project uses Redis to handle background tasks. To run the background tasks worker, you need to run the following command:

```bash
uv run poe celery-worker
```

> [!IMPORTANT]
> This command need to run when the `uvicorn` server is running, so you can open a new terminal window and run this command in parallel with the `uvicorn` server.

> [!NOTE]
> In a production environment, this background worker should be managed by a systemd daemon rather than run manually.



## Run the application
As the project is an asynchronous Django application, you can run it using the `uvicorn` development server. To do this, run the following command:

```bash
uv run poe uvicorn
```

## Run the tests
This project uses Django's built-in testing framework to run tests. Try to write and run tests for your changes to ensure that everything works as expected. You can run the tests by running the following command inside the `project` directory:

```bash
uv run poe test
```

**Tests need to be run before each commits**, as they ensure nothing breaks, especially when refactoring or cleaning code.

To have an overview of untested code portions, you can use the commands 
following:

```bash
uv run poe coverage-test
uv run poe coverage-report
uv run poe coverage-html
```

While code coverage does not guarantee that every case is tested, it provides a clear overview and objectives to understand which parts of the codebase are covered and which are not.

Beyond unit tests, the application can be tested using multi-user scenarios that simulate real-world usage and validate behavior as seen by end users.


## Run the GitHub Actions locally
It may be useful to run the GitHub Actions locally to ensure that everything works as expected before pushing your changes to the repository. You need first to install the `act` tool (see https://github.com/nektos/act). 
Once installed you can run the following command in the root directory of the project to run the GitHub Actions locally:

```bash
~/bin/act 
```

NB: To run `act` you need to have Docker installed and running on your machine. `act` will use Docker to run the GitHub Actions workflows in isolated containers.

## Translations
You need first to install GNU gettext tools to work with translations. You can install it using your package manager. For example, on Ubuntu, you can run the following command:

**On Debian/Ubuntu:**
 
```bash
sudo apt-get install gettext
```
 
**On Fedora/Red Hat:**
 
```bash
sudo dnf install gettext
```

You can update the translation files by running the following command:

```bash
uv run poe makemessages -l <language_code>
```

Replace `<language_code>` with the language code you are working on (e.g., `fr` for French, `en` for English, etc.). After making your changes to the translation files, if you want to see the changes reflected in the application, you can compile the translations by running:

```bash
uv run poe compilemessages
```

The compiled translations won't be committed to the repository, as they are generated files. If you want to have translations available in your local environment, you need to run the `compilemessages` command.



## Commit your changes
Commit your changes with a descriptive message (you could link the issue you are working on for example using `#<issue_number>` in the commit message). Then push your changes to your forked repository. 

Once you are done with your changes, you can create a pull request to the main repository. To do this, follow these steps:
* Go to the main repository and click on the "Pull requests" tab
* Click on the "New pull request" button
* Select the branch you want to merge into (usually `develop`)
* Select the branch you want to merge from (your forked repository)
* Add a title and description for your pull request
* Assign the pull request to the appropriate person (usually the maintainer of the repository)
* Add any relevant labels or milestones
* Click on the "Create pull request" button
* Wait for the maintainer to review your pull request and make any necessary changes
* Once the pull request is approved, it will be merged into the main repository

