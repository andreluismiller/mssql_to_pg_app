from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator

class AppSettings(BaseModel):
    fetch_size: int = 10_000
    max_concurrent_objects: int = 4
    queue_max_batches: int = 3
    postgres_pool_min_size: int = 2
    postgres_pool_max_size: int = 8
    postgres_command_timeout_seconds: int = 1800
    state_schema: str = "etl_control"
    state_table: str = "object_watermarks"
    fail_fast: bool = False

class SourceSettings(BaseModel):
    command_timeout_seconds: int = 1800

class TargetSettings(BaseModel):
    staging_schema: str = "etl_stage"

class SourceObject(BaseModel):
    schema_name: str = Field(alias="schema")
    object: str
    kind: Literal["table", "view"] = "table"
    columns: list[str] = Field(default_factory=lambda: ["*"])
    predicate: str | None = None

class TargetObject(BaseModel):
    schema_name: str = Field(alias="schema")
    object: str
    mode: Literal["append", "upsert", "replace"] = "upsert"
    primary_key: list[str] = Field(default_factory=list)
    column_map: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_upsert_key(self):
        if self.mode == "upsert" and not self.primary_key:
            raise ValueError("target.primary_key is required for upsert")
        return self

class ProcessorConfig(BaseModel):
    type: Literal["full_reload", "id_incremental", "timestamp_incremental"]
    watermark_column: str | None = None
    initial_value: Any = None
    overlap_seconds: int = 0

    @model_validator(mode="after")
    def validate_incremental(self):
        if self.type != "full_reload" and not self.watermark_column:
            raise ValueError("watermark_column is required for incremental processors")
        return self

class ObjectConfig(BaseModel):
    name: str
    enabled: bool = True
    source: SourceObject
    target: TargetObject
    processor: ProcessorConfig

class RootConfig(BaseModel):
    app: AppSettings
    source: SourceSettings
    target: TargetSettings
