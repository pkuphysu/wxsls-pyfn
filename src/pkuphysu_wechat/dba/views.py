from logging import getLogger

from flask import Blueprint, request
from sqlalchemy import inspect
from sqlalchemy.sql.expression import insert

from pkuphysu_wechat import db
from pkuphysu_wechat.auth.utils import master_required
from pkuphysu_wechat.utils import respond_error, respond_success

bp = Blueprint("dba", __name__)
bp.before_request(master_required)

logger = getLogger(__name__)


@bp.route("/db-tables/create-all", methods=["POST"])
def create_all():
    db.create_all()
    logger.info("Tables created")
    return respond_success()


@bp.route("/db-tables", methods=["GET"])
def index():
    tables = db.Model.metadata.tables.keys()
    inspector = inspect(db.engine)
    return respond_success(tables={name: inspector.has_table(name) for name in tables})


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
