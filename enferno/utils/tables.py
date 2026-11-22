from flask import request
from sqlalchemy import or_

from enferno.extensions import db

PER_PAGE = 25


def table_response(query, sortable=None, searchable=(), serialize=None):
    """One page of a data table, in the shape every admin list returns.

    Reads ?page, per_page, sort_by, sort_desc and q from the request. sort_by is
    only honoured for columns named in `sortable` ({"name": Model.column}), and q
    matches any `searchable` column, case-insensitively. `serialize` turns the
    page's rows into dicts; it defaults to each row's to_dict().
    """
    args = request.args
    if (q := args.get("q", "").strip()) and searchable:
        query = query.where(or_(*(column.ilike(f"%{q}%") for column in searchable)))
    if (column := (sortable or {}).get(args.get("sort_by"))) is not None:
        order = column.desc() if args.get("sort_desc") == "true" else column.asc()
        query = query.order_by(None).order_by(order)

    pagination = db.paginate(
        query,
        page=args.get("page", 1, type=int),
        per_page=args.get("per_page", PER_PAGE, type=int),
        max_per_page=100,
    )
    rows = pagination.items
    return {
        "items": serialize(rows) if serialize else [row.to_dict() for row in rows],
        "total": pagination.total,
        "perPage": pagination.per_page,
    }
