from datasette.app import Datasette
import pytest
import sqlite3


@pytest.mark.asyncio
async def test_open_csv_files(tmpdir):
    datasette = Datasette([], memory=True, pdb=True)
    await datasette.invoke_startup()
    path = str(tmpdir / "demo.csv")
    open(path, "w").write("id,name\n123,Hello")
    response = await datasette.client.post(
        "/-/open-csv-file",
        json={"path": path},
        headers={"Authorization": "Bearer fake-token"},
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True, "path": "/temporary/demo", "rows": 1}
    response2 = await datasette.client.get("/temporary/demo.json?_shape=array")
    assert response2.json() == [{"rowid": 1, "id": "123", "name": "Hello"}]


@pytest.mark.asyncio
async def test_open_csv_files_invalid_csv(tmpdir):
    datasette = Datasette([], memory=True)
    await datasette.invoke_startup()
    path = str(tmpdir / "bad.csv")
    open(path, "wb").write(
        b"date,name,latitude,longitude\n" b"2020-03-04,S\xe3o Paulo,-23.561,-46.645\n"
    )
    response = await datasette.client.post(
        "/-/open-csv-file",
        json={"path": path},
        headers={"Authorization": "Bearer fake-token"},
    )
    assert response.status_code == 500
    assert response.json() == {
        "ok": False,
        "error": "'utf-8' codec can't decode byte 0xe3 in position 41: invalid continuation byte",
    }


@pytest.mark.asyncio
async def test_import_csv_files(tmpdir):
    db_path = str(tmpdir / "data.db")
    sqlite3.connect(db_path).execute("vacuum")
    datasette = Datasette([db_path], memory=True, pdb=True)
    await datasette.invoke_startup()
    path = str(tmpdir / "demo.csv")
    open(path, "w").write("id,name\n123,Hello")
    response = await datasette.client.post(
        "/-/import-csv-file",
        json={"path": path, "database": "data"},
        headers={"Authorization": "Bearer fake-token"},
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True, "path": "/data/demo", "rows": 1}
    response2 = await datasette.client.get("/data/demo.json?_shape=array")
    assert response2.json() == [{"rowid": 1, "id": "123", "name": "Hello"}]
