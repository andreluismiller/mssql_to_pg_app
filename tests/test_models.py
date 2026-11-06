import pytest
from mssql_to_pg_app.models import ProcessorConfig, TargetObject

def test_incremental_requires_watermark():
    with pytest.raises(ValueError):
        ProcessorConfig(type="id_incremental")

def test_upsert_requires_key():
    with pytest.raises(ValueError):
        TargetObject(schema="public", object="x", mode="upsert")