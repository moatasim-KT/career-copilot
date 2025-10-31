"""CLI tool for Career Copilot management"""

import click
from .tasks.scheduled_tasks import ingest_jobs, send_morning_briefing, send_evening_summary
from .scripts.migrate_blueprint import migrate


@click.group()
def cli():
	"""Career Copilot CLI"""
	pass


@cli.command()
def run_ingestion():
	"""Manually run job ingestion"""
	click.echo("🔄 Running job ingestion...")
	ingest_jobs()
	click.echo("✅ Job ingestion completed")


@cli.command()
def send_briefing():
	"""Manually send morning briefing"""
	click.echo("📧 Sending morning briefings...")
	send_morning_briefing()
	click.echo("✅ Briefings sent")


@cli.command()
def send_summary():
	"""Manually send evening summary"""
	click.echo("📊 Sending evening summaries...")
	send_evening_summary()
	click.echo("✅ Summaries sent")


@cli.command()
def migrate_db():
	"""Run database migration for blueprint features"""
	click.echo("🔄 Running database migration...")
	migrate()
	click.echo("✅ Migration completed")


if __name__ == "__main__":
	cli()
