from werkzeug.wrappers import Request, Response

from sls_wsgi import encode_query_string, handle_request


def test_encode_query_string_preserves_multiple_values():
    event = {
        "multiValueQueryStringParameters": {
            "tag": ["alpha", "beta"],
            "query": ["中文"],
        }
    }

    assert encode_query_string(event) == ("tag=alpha&tag=beta&query=%E4%B8%AD%E6%96%87")


def test_handle_request_builds_wsgi_environ_and_alb_response():
    captured = {}

    @Request.application
    def application(request):
        captured["path"] = request.path
        captured["tags"] = request.args.getlist("tag")
        captured["body"] = request.get_data(as_text=True)
        return Response("created", status=201, content_type="text/plain")

    event = {
        "headers": {
            "Content-Type": "text/plain; charset=utf-8",
            "Host": "example.com",
            "X-Forwarded-Proto": "https",
        },
        "path": "/caf%C3%A9",
        "body": "你好",
        "isBase64Encoded": False,
        "multiValueQueryStringParameters": {"tag": ["alpha", "beta"]},
        "httpMethod": "POST",
        "requestContext": {
            "identity": {"sourceIp": "127.0.0.1"},
            "authorizer": {},
            "elb": {"targetGroupArn": "test"},
        },
    }

    result = handle_request(application, event)

    assert captured == {
        "path": "/café",
        "tags": ["alpha", "beta"],
        "body": "你好",
    }
    assert result["statusCode"] == 201
    assert result["statusDescription"] == "201 Created"
    assert result["body"] == "created"
    assert result["isBase64Encoded"] is False
