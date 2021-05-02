from logging import getLogger

from flask import Blueprint, request
from sqlalchemy import inspect
from sqlalchemy.sql.expression import insert

from pkuphysu_wechat import db
from pkuphysu_wechat.auth.utils import master_before_request
from pkuphysu_wechat.utils import respond_error, respond_success

bp = Blueprint("dba", __name__)
bp.before_request(master_before_request)

logger = getLogger(__name__)


@bp.route("/db-tables/create-all", methods=["POST"])
def create_all():
    db.create_all()
    logger.info("Tables created")
    return respond_success()


@bp.route("/db-tables", methods=["GET"])
def index():
    inspector = inspect(db.engine)
    tables_info = dict()
    for table_name, table in db.Model.metadata.tables.items():
        table_exists = inspector.has_table(table_name)
        table_rows = 0
        if table_exists:
            table_rows = db.session.query(table).count()
        tables_info[table_name] = dict(exists=table_exists, rows=table_rows)
    return respond_success(tables=tables_info)


@bp.route("/db-tables/<table_name>", methods=["GET", "DELETE", "PUT", "PATCH"])
def manage_table(table_name):
    table = db.Model.metadata.tables.get(table_name)
    columns = table.columns.keys()

    if request.method == "GET":
        return respond_success(
            count=db.session.query(table).count(),
            data=[
                {column: getattr(record, column) for column in columns}
                for record in db.session.query(table).limit(200).all()
            ],
        )
    if request.method == "DELETE":
        db.session.query(table).delete(synchronize_session=False)
        db.session.commit()
        logger.info("Table %s deleted", table_name)
        return respond_success()
    # Else in ["PUT", "PATCH"], verify data first
    records = request.get_json(force=True).get("data")
    if not isinstance(records, list):
        return respond_error(400, "DBADataMalformed")
    if len(records) == 0:
        return respond_error(400, "DBAUpdateNoData")
    for record in records:
        if not isinstance(record, dict) or set(record.keys()) != set(columns):
            return respond_error(400, "DBADataBadStructure")
    if request.method == "PUT":
        db.session.query(table).delete(synchronize_session=False)
    result = db.session.execute(insert(table), records)
    logger.info("Insert into %s result: %s", table_name, str(result))
    db.session.commit()
    return respond_success(rows=result.rowcount)


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
    return respond_success()
