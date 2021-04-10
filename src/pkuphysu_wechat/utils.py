from logging import getLogger

from flask import Response, abort, jsonify
from flask_sqlalchemy import BaseQuery

logger = getLogger()


def respond_error(status_code: int, errid: str, message: str = None) -> Response:
    """Return an error json response

    :param status_code: Status code
    :type status_code: int
    :param errid: The id of error. Used by frontend.
        Should be action + short reason. e.g. AuthBadCode
    :type errid: str
    :param message: Error message, defaults to None
    :type message: str, optional
    :return: jsonified response
    :rtype: Response
    """
    logger.info(f"Respond error {errid}: {message}")
    response = jsonify(
        {
            "status": status_code,
            "errid": errid,
            "message": message,
        }
    )
    response.status_code = status_code
    return response


def respond_success(**kwargs) -> Response:
    """Receive kwargs and return jsonified response with status=200 added

    :return: jsonified response
    :rtype: Response
    """
    return jsonify(status=200, **kwargs)


class CustomBaseQuery(BaseQuery):
    def get_or_abort(self, ident, code: int, errid_empty: str, errid_notexist: str):
        if not ident:
            abort(respond_error(code, errid_empty))
        rv = self.get(ident)
        if not rv:
            abort(respond_error(code, errid_notexist))
        return rv
