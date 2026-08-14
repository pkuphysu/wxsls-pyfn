# pylint: disable=unused-argument
import pytest

from pkuphysu_wechat import db


@pytest.mark.incremental
class TestProcess:
    def test_get_info(self, client, master_access):
        global NewTable  # pylint: disable=invalid-name
        rv = client.open_with_token("/db-tables", method="GET")

        class NewTable(db.Model):
            # TODO: add DateTime support test with timezone=True
            index = db.Column(db.Integer(), primary_key=True)
            content = db.Column(db.String(32))

        rv = client.open_with_token("/db-tables", method="GET")
        assert rv.json["status"] == 200
        assert len(rv.json["tables"])
        assert not rv.json["tables"].pop("new_table")["exists"]
        assert all(
            info["exists"]
            for name, info in rv.json["tables"].items()
            if name != "new_table"
        )

    def test_create(self, client, master_access):
        rv = client.open_with_token("/db-tables/create-all", method="POST")
        assert rv.json["status"] == 200

    def test_after_create(self, client, master_access):
        rv = client.open_with_token("/db-tables", method="GET")
        assert rv.json["status"] == 200
        assert len(rv.json["tables"])
        assert all(info["exists"] for info in rv.json["tables"].values())

    def test_get_table(self, client, master_access):
        db.session.add(NewTable(content="Nothing"))
        db.session.commit()
        rv = client.open_with_token("/db-tables/new_table", method="GET")
        assert rv.json["status"] == 200
        assert rv.json["page"] == 1
        assert rv.json["page_size"] == 200
        assert rv.json["pages"] == 1
        assert rv.json["primary_key"] == ["index"]
        assert rv.json["columns"] == [
            {
                "name": "index",
                "type": "INTEGER",
                "nullable": False,
                "primary_key": True,
                "has_default": True,
                "kind": "scalar",
            },
            {
                "name": "content",
                "type": "VARCHAR(32)",
                "nullable": True,
                "primary_key": False,
                "has_default": False,
                "kind": "scalar",
            },
        ]
        assert len(rv.json["data"]) == 1
        assert rv.json["data"][0] == dict(index=1, content="Nothing")

    def test_get_table_bad_pagination(self, client, master_access):
        rv = client.open_with_token(
            "/db-tables/new_table?page=0&page_size=20", method="GET"
        )
        assert rv.status_code == 400
        assert rv.json["errid"] == "DBAPaginationInvalid"

        rv = client.open_with_token(
            "/db-tables/new_table?page=999&page_size=20", method="GET"
        )
        assert rv.json["page"] == 1
        assert len(rv.json["data"]) == 1

    def test_info_rows(self, client, master_access):
        rv = client.open_with_token("/db-tables", method="GET")
        assert rv.json["status"] == 200
        assert rv.json["tables"].pop("new_table")["rows"] == 1

    def test_info_can_skip_expensive_counts(self, client, master_access):
        rv = client.open_with_token("/db-tables?include_counts=0", method="GET")
        assert rv.json["status"] == 200
        assert rv.json["tables"]["new_table"]["rows"] == 0

    def test_patch(self, client, master_access):
        rv = client.open_with_token(
            "/db-tables/new_table",
            method="PATCH",
            json=dict(data=[dict(index=3, content="test")]),
        )
        assert rv.json["status"] == 200
        assert rv.json["rows"] == 1

    def test_patch_result(self, client, master_access):
        rv = client.open_with_token("/db-tables/new_table", method="GET")
        assert rv.json["count"] == 2
        assert rv.json["data"][-1] == dict(index=3, content="test")

    def test_get_table_pagination_search_and_sort(self, client, master_access):
        rv = client.open_with_token(
            "/db-tables/new_table?page=2&page_size=1&sort=index&order=asc",
            method="GET",
        )
        assert rv.json["status"] == 200
        assert rv.json["count"] == 2
        assert rv.json["pages"] == 2
        assert rv.json["data"] == [dict(index=3, content="test")]

        rv = client.open_with_token(
            "/db-tables/new_table?page=1&page_size=20&search=Nothing",
            method="GET",
        )
        assert rv.json["count"] == 1
        assert rv.json["data"] == [dict(index=1, content="Nothing")]

    def test_row_create_update_delete(self, client, master_access):
        rv = client.open_with_token(
            "/db-tables/new_table/rows",
            method="POST",
            json=dict(data=dict(index=4, content="created")),
        )
        assert rv.json["status"] == 200

        rv = client.open_with_token(
            "/db-tables/new_table/rows",
            method="PATCH",
            json=dict(key=dict(index=4), data=dict(content="updated")),
        )
        assert rv.json["status"] == 200
        assert rv.json["row"] == dict(index=4, content="updated")

        rv = client.open_with_token(
            "/db-tables/new_table/rows",
            method="DELETE",
            json=dict(key=dict(index=4)),
        )
        assert rv.json["status"] == 200

        rv = client.open_with_token("/db-tables/new_table?search=updated", method="GET")
        assert rv.json["count"] == 0

    def test_row_bad_key_and_unknown_table(self, client, master_access):
        rv = client.open_with_token(
            "/db-tables/new_table/rows",
            method="DELETE",
            json=dict(key=dict(content="Nothing")),
        )
        assert rv.status_code == 400
        assert rv.json["errid"] == "DBAPrimaryKeyMalformed"

        rv = client.open_with_token("/db-tables/not_a_table", method="GET")
        assert rv.status_code == 404
        assert rv.json["errid"] == "DBATableNotFound"

    def test_put(self, client, master_access):
        rv = client.open_with_token(
            "/db-tables/new_table",
            method="PUT",
            json=dict(data=[dict(index=5, content="tester")]),
        )
        assert rv.json["status"] == 200
        assert rv.json["rows"] == 1

    def test_put_result(self, client, master_access):
        rv = client.open_with_token("/db-tables/new_table", method="GET")
        assert rv.json["count"] == 1
        assert rv.json["data"][0] == dict(index=5, content="tester")

    def test_delete(self, client, master_access):
        rv = client.open_with_token("/db-tables/new_table", method="DELETE")
        assert rv.json["status"] == 200

    def test_delete_result(self, client, master_access):
        rv = client.open_with_token("/db-tables/new_table", method="GET")
        assert rv.json["count"] == 0

    def test_col_len_before_migration(self, client, master_access):
        rv = client.open_with_token(
            "/db-tables/new_table",
            method="PUT",
            json=dict(data=[dict(index=5, content="tester" * 10)]),
        )
        assert rv.json["status"] == 500

    def test_migration_preview(self, client, master_access):
        class BrandNewTable(db.Model):
            __tablename__ = "new_table"
            __table_args__ = dict(extend_existing=True)
            index = db.Column(db.Integer(), primary_key=True)
            content = db.Column(db.String(64))
            data = db.Column(db.String(32))

        rv = client.open_with_token("/db-tables/migrate", method="GET")
        assert rv.json["status"] == 200
        assert "add_column" in rv.json["migration"]
        assert "modify_type" in rv.json["migration"]

    def test_migration(self, client, master_access):
        rv = client.open_with_token("/db-tables/migrate", method="POST")
        assert rv.json["status"] == 200

    def test_migration_col_len(self, client, master_access):
        rv = client.open_with_token(
            "/db-tables/new_table",
            method="PUT",
            json=dict(data=[dict(index=5, content="tester" * 10, data="nothing")]),
        )
        assert rv.json["status"] == 200
        assert rv.json["rows"] == 1

    def test_migration_done(self, client, master_access):
        rv = client.open_with_token("/db-tables/migrate", method="GET")
        assert rv.json["status"] == 200
        assert rv.json["migration"] == "[]"
