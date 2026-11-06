from pathlib import Path
import yaml
from etl_app.database.sqlserver import connect
QUERY = """SELECT s.name schema_name,o.name object_name,CASE o.type WHEN 'U' THEN 'table' ELSE 'view' END kind,
c.column_id,c.name column_name,t.name data_type,c.max_length,c.precision,c.scale,c.is_nullable,c.is_identity
FROM sys.objects o JOIN sys.schemas s ON s.schema_id=o.schema_id
JOIN sys.columns c ON c.object_id=o.object_id JOIN sys.types t ON t.user_type_id=c.user_type_id
WHERE o.type IN ('U','V') AND o.is_ms_shipped=0 ORDER BY s.name,o.name,c.column_id"""

def generate(output: Path) -> None:
    with connect() as connection:
        cursor = connection.cursor(); cursor.execute(QUERY)
        names = [item[0] for item in cursor.description]
        rows = [dict(zip(names, row)) for row in cursor.fetchall()]
    grouped = {}
    for row in rows:
        grouped.setdefault((row["schema_name"], row["object_name"], row["kind"]), []).append(row)
    objects = []
    for (schema, name, kind), columns in grouped.items():
        identity = next((x["column_name"] for x in columns if x["is_identity"]), None)
        objects.append({
            "name": f"{schema}_{name}".lower(), "enabled": False,
            "source": {"schema": schema, "object": name, "kind": kind,
                       "columns": [x["column_name"] for x in columns]},
            "target": {"schema": schema.lower(), "object": name.lower(),
                       "mode": "upsert" if identity else "replace",
                       "primary_key": [identity.lower()] if identity else [],
                       "column_map": {x["column_name"]: x["column_name"].lower() for x in columns}},
            "processor": ({"type": "id_incremental", "watermark_column": identity, "initial_value": 0}
                          if identity else {"type": "full_reload"})})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(yaml.safe_dump({"objects": objects}, sort_keys=False, allow_unicode=True), encoding="utf-8")
