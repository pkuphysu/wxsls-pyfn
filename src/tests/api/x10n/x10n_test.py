import json

import pytest

from pkuphysu_wechat.config import settings


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

    def test_get_and_post_questions(self, client):
        rv = client.open_with_token("/api/x10n", method="GET")
        assert rv.status_code == 200
        assert not rv.json["played"]
        assert rv.json["questions"]
        assert rv.json["questions"][0]["text"] == "xx 的数量级是？"
        assert rv.json["questions"][0]["choices"] == ["一个月", "半年"]
        assert (
            len(set([x["number"] for x in rv.json["questions"]]))
            == settings.x10n.PROBLEMS_NUMBER
        )
        probids = [x["number"] for x in rv.json["questions"]]
        # def test_post_result(self, client):
        # 这里为了传递受到的题目，把两个测试改成一个了，用probids传递题目的id，
        # 用此检验是否可以检验提交题目为发出题目
        rv = client.open_with_token(
            "/api/x10n",
            method="POST",
            json=dict(
                result=dict(
                    name="罗翔",
                    stuID="zhangsan",
                    questions=[dict(number=i, answer=int(i) % 2) for i in probids],
                )
            ),
        )
        # print(rv)
        print(probids)
        assert rv.status_code == 200
        assert rv.json["result"]["time"]
        assert rv.json["result"]["questions"] == [
            dict(number=i, answer=bool(int(i) % 2)) for i in probids
        ]

    def test_get_result(self, client):
        rv = client.open_with_token("/api/x10n", method="GET")
        assert rv.status_code == 200
        assert rv.json["played"]
        assert rv.json["result"]
        assert rv.json["result"]["questions"][0]["answer"] == bool(
            int(rv.json["result"]["questions"][0]["number"]) % 2
        )
