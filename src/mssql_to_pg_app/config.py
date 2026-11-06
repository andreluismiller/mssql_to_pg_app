from pathlib import Path
import os
import yaml
from dotenv import load_dotenv
from .models import ObjectConfig, RootConfig

def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream) or {}

def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value

def load_config(config_dir: Path):
    load_dotenv()
    root = RootConfig.model_validate(load_yaml(config_dir / "app.yaml"))
    objects: list[ObjectConfig] = []
    for path in sorted((config_dir / "objects").glob("*.yaml")):
        objects.extend(ObjectConfig.model_validate(item) for item in load_yaml(path).get("objects", []))
    mappings = load_yaml(config_dir / "type_mappings.yaml").get("mappings", {})
    return root, [item for item in objects if item.enabled], mappings
