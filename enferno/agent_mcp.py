"""Read-only MCP server that shows coding agents the live app: routes, schema,
migration state and the audit log. Run with `uv run flask mcp` (stdio)."""

from typing import Annotated, Any

from alembic.migration import MigrationContext
from mcp.server import MCPServer
from mcp.types import ToolAnnotations
from pydantic import Field

from enferno.extensions import db
from enferno.user.models import Activity

READ_ONLY = ToolAnnotations(readOnlyHint=True)


def build_server(app):
    server = MCPServer(
        "enferno",
        instructions="Live, read-only view of this Enferno app. Conventions are in AGENTS.md.",
    )

    @server.tool(annotations=READ_ONLY)
    def routes() -> list[dict]:
        """Every URL rule with its endpoint and HTTP methods."""
        return [
            {
                "rule": rule.rule,
                "endpoint": rule.endpoint,
                "methods": sorted(rule.methods - {"HEAD", "OPTIONS"}),
            }
            for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
        ]

    @server.tool(annotations=READ_ONLY)
    def schema() -> dict[str, Any]:
        """Model tables with columns and row counts, plus the migration revision."""
        with app.app_context():
            existing = set(db.inspect(db.engine).get_table_names())
            tables = {
                name: {
                    "columns": [
                        {
                            "name": column.name,
                            "type": str(column.type),
                            "nullable": column.nullable,
                            "primary_key": column.primary_key,
                        }
                        for column in table.columns
                    ],
                    "rows": db.session.scalar(
                        db.select(db.func.count()).select_from(table)
                    )
                    if name in existing
                    else None,
                }
                for name, table in sorted(db.metadata.tables.items())
            }
            with db.engine.connect() as connection:
                revision = MigrationContext.configure(connection).get_current_revision()
        return {"tables": tables, "migration_revision": revision}

    @server.tool(annotations=READ_ONLY)
    def recent_activity(limit: Annotated[int, Field(ge=1, le=100)] = 20) -> list[dict]:
        """Latest audit log entries, newest first."""
        with app.app_context():
            query = (
                db.select(Activity).order_by(Activity.created_at.desc()).limit(limit)
            )
            return [
                {
                    "user_id": activity.user_id,
                    "action": activity.action,
                    "data": activity.data,
                    "created_at": activity.created_at.isoformat(),
                }
                for activity in db.session.execute(query).scalars()
            ]

    return server
