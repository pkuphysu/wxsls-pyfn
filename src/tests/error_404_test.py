def test_404(client):
    rv = client.get("/nobody-would-ever-use-this")
    assert rv.status_code == 404
    assert rv.json["status"] == 404
