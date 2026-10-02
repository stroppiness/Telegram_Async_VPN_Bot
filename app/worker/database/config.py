TORTOISE_ORM = {
    "connections": {
        "default": "sqlite://db.sqlite3",
    },
    "apps": {
        "models": {
            "models": ["app.worker.database.models"],
            "default_connection": "default",
            "migrations": "app.worker.database.migrations",
        },
    },
}
