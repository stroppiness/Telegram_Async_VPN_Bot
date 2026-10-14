TORTOISE_ORM = {
    "connections": {
        "default": "sqlite://database/db.sqlite3",
    },
    "apps": {
        "models": {
            "models": ["worker.database.models"],
            "default_connection": "default",
            "migrations": "worker.database.migrations",
        },
    },
}
