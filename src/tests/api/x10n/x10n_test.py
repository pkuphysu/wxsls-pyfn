import json

import pytest


@pytest.mark.incremental
class TestX10n:
    def test_upload_questions(self, client, master_access):
        rv = client.open_with_token(
            "/db-tables/x10nProbs",
            method="PUT",
            json=dict(
                data=[
                    dict(
                        probid=str(i),
                        text="xx 的数量级是？",
                        img="https://tuchuang...",
                        choices=json.dumps(["一个月", "半年"]),
                        answer="1",
                    )
                    for i in range(50)
                ]
            ),
        )
        assert rv.json["status"] == 200
        assert rv.json["rows"] == 50

    def test_get_questions(self, client):
        rv = client.open_with_token("/api/x10n", method="GET")
        assert rv.status_code == 200
        assert not rv.json["played"]
        assert rv.json["questions"]
        assert rv.json["questions"][0]["text"] == "xx 的数量级是？"
        assert rv.json["questions"][0]["choices"] == ["一个月", "半年"]

    def test_post_result(self, client):
        rv = client.open_with_token(
            "/api/x10n",
            method="POST",
            json=dict(
                result=dict(
                    name="罗翔",
                    wx="zhangsan",
                    questions=[
                        dict(number=str(i), answer=i % 2)
                        for i in range(30)  # NOTE: magic number! change it!
                    ],
                )
            ),
        )
        print(rv)
        assert rv.status_code == 200
        assert rv.json["result"]["time"]
        assert rv.json["result"]["questions"] == [
            dict(number=str(i), answer=bool(i % 2))
            for i in range(30)  # NOTE: magic number! change it!
        ]

    def test_get_result(self, client):
        rv = client.open_with_token("/api/x10n", method="GET")
        assert rv.status_code == 200
        assert rv.json["played"]
        assert rv.json["result"]
        assert not rv.json["result"]["questions"][0]["answer"]
