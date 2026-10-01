TORTOISE_ORM = {
    "connections": {
        "default": "sqlite://app/worker/db.sqlite3",
    },
    "apps": {
        "models": {
            "models": ["app.database.models"],
            "default_connection": "default",
            "migrations": "app.database.migrations",
        },
    },
}
