import asyncio
from pathlib import Path
import typer
from mssql_to_pg_app.config import load_config
from mssql_to_pg_app.inventory import generate
from mssql_to_pg_app.main import runtime
app = typer.Typer(no_args_is_help=True)

async def _run_all(config_dir: Path):
    config, objects, _ = load_config(config_dir)
    async with runtime(config) as runner:
        await runner.run_all(objects)

async def _run_one(name: str, config_dir: Path):
    config, objects, _ = load_config(config_dir)
    obj = next((item for item in objects if item.name == name), None)
    if not obj:
        raise typer.BadParameter(f"Unknown or disabled object: {name}")
    async with runtime(config) as runner:
        await runner.run_one(obj)

@app.command("run-all")
def run_all(config_dir: Path = Path("config")):
    asyncio.run(_run_all(config_dir))

@app.command("run")
def run(name: str, config_dir: Path = Path("config")):
    asyncio.run(_run_one(name, config_dir))

@app.command("inventory")
def inventory(output: Path = Path("config/objects/generated.yaml")):
    generate(output); typer.echo(f"Generated {output}")
