from mssql_to_pg_app.models import ObjectConfig
from mssql_to_pg_app.sql import source_select

def test_incremental_select():
    obj = ObjectConfig.model_validate({
        "name":"x", "source":{"schema":"dbo","object":"X","columns":["Id"]},
        "target":{"schema":"public","object":"x","mode":"upsert","primary_key":["id"]},
        "processor":{"type":"id_incremental","watermark_column":"Id","initial_value":0}})
    sql, params = source_select(obj, 10)
    assert "[Id] > ?" in sql
    assert params == [10]