import click
import os
from app.services import license_service

@click.group()
def cli():
    pass

@cli.command()
def reset():
    if os.path.exists(license_service.LICENSE_DIR):
        for file in os.listdir(license_service.LICENSE_DIR):
            if file.endswith('.json'):
                os.remove(os.path.join(license_service.LICENSE_DIR, file))
    os.makedirs(license_service.LICENSE_DIR, exist_ok=True)
    click.echo("License storage reset successfully")

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.argument('category', type=click.Choice(['basic', 'pro', 'enterprise']))
def import_keys(file_path: str, category: str):
    try:
        with open(file_path, 'r') as f:
            keys = [line.strip() for line in f if line.strip()]
        
        license_service.import_keys(category, keys)
        click.echo(f"Imported {len(keys)} keys for category {category}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@cli.command()
@click.argument('category', type=click.Choice(['basic', 'pro', 'enterprise']))
def stock_count(category: str):
    try:
        count = license_service.get_available_count(category)
        click.echo(f"{category} licenses in stock: {count}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@cli.command()
@click.argument('category', type=click.Choice(['basic', 'pro', 'enterprise']))
def list_keys(category: str):
    try:
        keys = license_service.list_available_keys(category)
        if not keys:
            click.echo(f"No {category} licenses in stock")
            return
        for key in keys:
            click.echo(key)
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@cli.command()
@click.argument('key')
def remove(key: str):
    try:
        if license_service.remove_key(key):
            click.echo(f"Successfully removed key: {key}")
        else:
            click.echo(f"Key not found: {key}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

if __name__ == '__main__':
    cli()
