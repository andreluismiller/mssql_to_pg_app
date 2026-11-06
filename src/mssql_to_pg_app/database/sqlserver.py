import pyodbc
from mssql_to_pg_app.config import required_env

def connection_string() -> str:
    return (
        f"DRIVER={{{required_env('SQLSERVER_DRIVER')}}};"
        f"SERVER={required_env('SQLSERVER_HOST')},{required_env('SQLSERVER_PORT')};"
        f"DATABASE={required_env('SQLSERVER_DATABASE')};"
        f"UID={required_env('SQLSERVER_USER')};PWD={required_env('SQLSERVER_PASSWORD')};"
        f"Encrypt={required_env('SQLSERVER_ENCRYPT')};"
        f"TrustServerCertificate={required_env('SQLSERVER_TRUST_CERTIFICATE')}"
    )

def connect(timeout_seconds: int = 30) -> pyodbc.Connection:
    return pyodbc.connect(connection_string(), timeout=timeout_seconds, autocommit=False)
