# Migration Assistant
An application developed for the purposes of the `Extending data repositories using a novel FDO framework` master thesis written by Bartosz Błachut at the TU Wien.

# Functionalities
1. Migrate metadata of existing records in an InvenioRDM-based research data repositories and represent them as FDOs in a Cordra backend
2. Expose a testing endpoint `/metadata/<record-id>` that exports the newly created metadata from Cordra and makes it available for assessment tools, such as FUJI.

# Prerequisites
1. A running InvenioRDM instance with some records that are not `metadata-only`. An account with access to these records is needed as it is necessary to provide an access token during tool configuration.
2. A running Cordra instance. The login and password to the admin account to this instance is needed. 
3. Python v3.13

# Set up
The application uses a folder called `instance` to save configuration data, a temporary settings database and log files. Before starting the application create the `instance` folder
```bash
mkdir instance
```
and copy the exemplary `config.py` file inside
```bash
cp config.py instance
```

You can uncomment the lines from the config.py file to change the settings. Set the `FLASK_LOG_LEVEL` to any value from the [Python Logging documentation](https://docs.python.org/3/library/logging.html#levels) (defaults to `WARNING`) and the `SQLALCHEMY_DATABASE_URI` to a valid database string (defaults to `sqlite:///app.db`, which creates a database file in your `instance` folder - you don't need to change anything).

Subsequently install python requirements:
```bash
pip install -r requirements.txt
```

and run the app:
```
flask --app migration_assistant run --port 9090
```

You can change the port, if necessary. After a successful start, your application is available in the browser under `http://localhost:9090`.