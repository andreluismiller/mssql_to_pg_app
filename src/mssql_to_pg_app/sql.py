def ms_quote(name: str) -> str:
    return "[" + name.replace("]", "]]" ) + "]"

def pg_quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

def source_select(obj, watermark=None) -> tuple[str, list]:
    columns = "*" if obj.source.columns == ["*"] else ", ".join(ms_quote(x) for x in obj.source.columns)
    clauses: list[str] = []
    params: list = []
    if obj.source.predicate:
        clauses.append(f"({obj.source.predicate})")
    if obj.processor.type != "full_reload":
        clauses.append(f"{ms_quote(obj.processor.watermark_column)} > ?")
        params.append(watermark)
    sql = f"SELECT {columns} FROM {ms_quote(obj.source.schema_name)}.{ms_quote(obj.source.object)}"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    if obj.processor.type != "full_reload":
        sql += f" ORDER BY {ms_quote(obj.processor.watermark_column)}"
    return sql, params
