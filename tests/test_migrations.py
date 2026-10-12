from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from flask_migrate import upgrade

from enferno.extensions import db

MIGRATIONS = Path(__file__).parents[1] / "migrations"


def test_single_migration_head():
    heads = ScriptDirectory(str(MIGRATIONS)).get_heads()
    assert len(heads) == 1, f"multiple heads, merge them: {heads}"


def test_migrations_match_models(app):
    with app.app_context():
        db.drop_all()
        upgrade(directory=str(MIGRATIONS))
        # Flask-Session creates its own table at startup, outside migrations.
        own_table = app.config["SESSION_SQLALCHEMY_TABLE"]
        opts = {"include_object": lambda obj, name, *_: name != own_table}
        with db.engine.connect() as connection:
            context = MigrationContext.configure(connection, opts=opts)
            diff = compare_metadata(context, db.metadata)
        db.session.execute(db.text("DROP TABLE alembic_version"))
        db.session.commit()
    assert not diff, f"models changed without a migration, run flask db migrate: {diff}"
