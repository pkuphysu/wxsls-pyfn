from base64 import b64decode, b64encode
from binascii import Error as Base64Error
from datetime import date, datetime, time
from decimal import Decimal
from logging import getLogger
from math import ceil

from flask import Blueprint, request
from sqlalchemy import (
    Date,
    DateTime,
    LargeBinary,
    String,
    Time,
    cast,
    delete,
    inspect,
    or_,
    select,
    update,
)
from sqlalchemy.exc import DataError, SQLAlchemyError
from sqlalchemy.sql.expression import insert

from pkuphysu_wechat import db
from pkuphysu_wechat.auth.utils import master_before_request
from pkuphysu_wechat.utils import respond_error, respond_success

bp = Blueprint("dba", __name__)
bp.before_request(master_before_request)

logger = getLogger(__name__)

MAX_PAGE_SIZE = 200


def get_table(table_name):
    return db.Model.metadata.tables.get(table_name)


def serialize_value(value):
    if isinstance(value, bytes):
        return {"$binary": b64encode(value).decode("ascii")}
    if isinstance(value, (date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def serialize_row(row, columns):
    return {
        column.name: serialize_value(getattr(row, column.name)) for column in columns
    }


def deserialize_value(column, value):
    if value is None:
        return None
    if isinstance(column.type, LargeBinary):
        if not isinstance(value, dict) or set(value) != {"$binary"}:
            raise ValueError
        return b64decode(value["$binary"], validate=True)
    if isinstance(column.type, DateTime) and isinstance(value, str):
        return datetime.fromisoformat(value)
    if isinstance(column.type, Date) and isinstance(value, str):
        return date.fromisoformat(value)
    if isinstance(column.type, Time) and isinstance(value, str):
        return time.fromisoformat(value)
    return value


def deserialize_record(table, record):
    try:
        return {
            name: deserialize_value(table.columns[name], value)
            for name, value in record.items()
        }
    except (Base64Error, KeyError, TypeError, ValueError):
        raise ValueError from None


def column_schema(column):
    has_default = (
        column.default is not None
        or column.server_default is not None
        or (column is column.table._autoincrement_column)
    )
    if isinstance(column.type, LargeBinary):
        kind = "binary"
    elif isinstance(column.type, DateTime):
        kind = "datetime"
    elif isinstance(column.type, Date):
        kind = "date"
    elif isinstance(column.type, Time):
        kind = "time"
    else:
        kind = "scalar"
    return {
        "name": column.name,
        "type": str(column.type),
        "nullable": column.nullable,
        "primary_key": column.primary_key,
        "has_default": has_default,
        "kind": kind,
    }


def parse_positive_arg(name, default):
    raw_value = request.args.get(name)
    if raw_value is None:
        return default
    value = int(raw_value)
    if value < 1:
        raise ValueError
    return value


def primary_key_conditions(table, key):
    primary_key = list(table.primary_key.columns)
    if not primary_key:
        return None
    if not isinstance(key, dict) or set(key) != {column.name for column in primary_key}:
        raise ValueError
    return [column == key[column.name] for column in primary_key]


def validate_record(table, record, allow_partial):
    if not isinstance(record, dict) or not record:
        return False
    column_names = {column.name for column in table.columns}
    if not set(record).issubset(column_names):
        return False
    return allow_partial or set(record) == column_names


@bp.route("/db-tables/create-all", methods=["POST"])
def create_all():
    # Release any read transaction before DDL changes table definitions.
    db.session.remove()
    db.create_all()
    db.session.remove()
    logger.info("Tables created")
    return respond_success()


@bp.route("/db-tables", methods=["GET"])
def index():
    inspector = inspect(db.engine)
    include_counts = request.args.get("include_counts", "1") != "0"
    tables_info = dict()
    for table_name, table in db.Model.metadata.tables.items():
        table_exists = inspector.has_table(table_name)
        table_rows = 0
        if table_exists and include_counts:
            table_rows = db.session.query(table).count()
        tables_info[table_name] = dict(exists=table_exists, rows=table_rows)
    return respond_success(tables=tables_info)


@bp.route("/db-tables/<table_name>", methods=["GET", "DELETE", "PUT", "PATCH"])
def manage_table(table_name):
    table = get_table(table_name)
    if table is None:
        return respond_error(404, "DBATableNotFound")
    if not inspect(db.engine).has_table(table_name):
        return respond_error(404, "DBATableNotCreated")
    if request.method == "GET":
        try:
            page = parse_positive_arg("page", 1)
            page_size = parse_positive_arg("page_size", MAX_PAGE_SIZE)
        except (TypeError, ValueError):
            return respond_error(400, "DBAPaginationInvalid")
        if page_size > MAX_PAGE_SIZE:
            return respond_error(400, "DBAPaginationInvalid")

        column_objects = list(table.columns)
        column_names = {column.name for column in column_objects}
        sort_name = request.args.get("sort")
        if sort_name is not None and sort_name not in column_names:
            return respond_error(400, "DBASortInvalid")
        order = request.args.get("order", "asc")
        if order not in ("asc", "desc"):
            return respond_error(400, "DBASortInvalid")

        query = db.session.query(table)
        search = request.args.get("search", "").strip()
        if search:
            if len(search) > 200:
                return respond_error(400, "DBASearchInvalid")
            escaped = (
                search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            )
            query = query.filter(
                or_(
                    *[
                        cast(column, String).ilike(f"%{escaped}%", escape="\\")
                        for column in column_objects
                        if isinstance(column.type, String)
                    ]
                )
            )

        primary_key = list(table.primary_key.columns)
        sort_column = table.columns.get(sort_name) if sort_name else None
        order_columns = []
        if sort_column is not None:
            order_columns.append(sort_column)
        order_columns.extend(
            column for column in primary_key if column is not sort_column
        )
        if not order_columns:
            order_columns.append(column_objects[0])
        order_by = [
            column.asc() if order == "asc" else column.desc()
            for column in order_columns
        ]

        count = query.count()
        pages = max(1, ceil(count / page_size))
        page = min(page, pages)
        records = (
            query.order_by(*order_by)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return respond_success(
            count=count,
            page=page,
            page_size=page_size,
            pages=pages,
            columns=[column_schema(column) for column in column_objects],
            primary_key=[column.name for column in primary_key],
            data=[serialize_row(record, column_objects) for record in records],
        )
    if request.method == "DELETE":
        db.session.query(table).delete(synchronize_session=False)
        db.session.commit()
        logger.info("Table %s deleted", table_name)
        return respond_success()
    # Else in ["PUT", "PATCH"], verify data first
    payload = request.get_json(silent=True) or {}
    records = payload.get("data")
    if not isinstance(records, list):
        return respond_error(400, "DBADataMalformed")
    if len(records) == 0:
        return respond_error(400, "DBAUpdateNoData")
    for record in records:
        if not validate_record(table, record, allow_partial=False):
            return respond_error(400, "DBADataBadStructure")
    try:
        records = [deserialize_record(table, record) for record in records]
    except ValueError:
        return respond_error(400, "DBADataBadValue")
    if request.method == "PUT":
        db.session.query(table).delete(synchronize_session=False)
    try:
        result = db.session.execute(insert(table), records)
        logger.info("Insert into %s result: %s", table_name, str(result))
        db.session.commit()
        return respond_success(rows=result.rowcount)
    except DataError as e:
        logger.error(e)
        db.session.rollback()
        return respond_error(500, "DBADataInsertFail")


@bp.route("/db-tables/<table_name>/rows", methods=["POST", "PATCH", "DELETE"])
def manage_row(table_name):
    table = get_table(table_name)
    if table is None:
        return respond_error(404, "DBATableNotFound")
    if not inspect(db.engine).has_table(table_name):
        return respond_error(404, "DBATableNotCreated")

    payload = request.get_json(silent=True) or {}
    columns = list(table.columns)
    primary_key = list(table.primary_key.columns)
    if request.method != "POST" and not primary_key:
        return respond_error(409, "DBAIdentityUnavailable")

    if request.method == "POST":
        record = payload.get("data")
        if not validate_record(table, record, allow_partial=True):
            return respond_error(400, "DBADataBadStructure")
        try:
            record = deserialize_record(table, record)
        except ValueError:
            return respond_error(400, "DBADataBadValue")
        try:
            result = db.session.execute(insert(table).values(**record))
            inserted_key = dict(
                zip(
                    [column.name for column in primary_key],
                    result.inserted_primary_key,
                )
            )
            db.session.commit()
            row = None
            if primary_key and all(
                value is not None for value in inserted_key.values()
            ):
                conditions = primary_key_conditions(table, inserted_key)
                row = db.session.execute(select(table).where(*conditions)).first()
            return respond_success(
                row=serialize_row(row, columns) if row is not None else record
            )
        except SQLAlchemyError as e:
            logger.error(e)
            db.session.rollback()
            return respond_error(409, "DBADataInsertFail")

    try:
        conditions = primary_key_conditions(table, payload.get("key"))
    except ValueError:
        return respond_error(400, "DBAPrimaryKeyMalformed")

    try:
        existing = db.session.execute(select(table).where(*conditions)).first()
        if existing is None:
            return respond_error(404, "DBARowNotFound")
        if request.method == "DELETE":
            result = db.session.execute(delete(table).where(*conditions))
            if result.rowcount != 1:
                db.session.rollback()
                return respond_error(409, "DBARowWriteConflict")
            db.session.commit()
            return respond_success()

        changes = payload.get("data")
        if not validate_record(table, changes, allow_partial=True):
            return respond_error(400, "DBADataBadStructure")
        if any(column.name in changes for column in primary_key):
            return respond_error(400, "DBAPrimaryKeyImmutable")
        try:
            changes = deserialize_record(table, changes)
        except ValueError:
            return respond_error(400, "DBADataBadValue")
        result = db.session.execute(update(table).where(*conditions).values(**changes))
        if result.rowcount != 1:
            db.session.rollback()
            return respond_error(409, "DBARowWriteConflict")
        db.session.commit()
        row = db.session.execute(select(table).where(*conditions)).first()
        if row is None:
            return respond_error(409, "DBARowWriteConflict")
        return respond_success(row=serialize_row(row, columns))
    except SQLAlchemyError as e:
        logger.error(e)
        db.session.rollback()
        return respond_error(409, "DBADataWriteFail")


@bp.route("/db-tables/migrate", methods=["GET", "POST"])
def migrate():
    from alembic.runtime.migration import MigrationContext

    # use `db.session.connection()` instead of `db.engine.connect()`
    # to avoid lock hang
    context = MigrationContext.configure(
        db.session.connection(),
        opts={
            "compare_type": True,
        },
    )

    if request.method == "GET":
        import pprint

        from alembic.autogenerate import compare_metadata

        diff = compare_metadata(context, db.metadata)
        diff_str = pprint.pformat(diff, indent=2, width=20)
        logger.info("Migrate steps: %s", diff_str)
        return respond_success(migration=diff_str)

    from alembic.autogenerate import produce_migrations
    from alembic.operations import Operations
    from alembic.operations.ops import OpContainer

    migration = produce_migrations(context, db.metadata)
    operation = Operations(context)
    for outer_op in migration.upgrade_ops.ops:
        logger.info("Invoking %s", outer_op)
        if isinstance(outer_op, OpContainer):
            for inner_op in outer_op.ops:
                logger.info("Invoking %s", inner_op)
                operation.invoke(inner_op)
        else:
            operation.invoke(outer_op)
    db.session.commit()
    db.session.close()
    return respond_success()
