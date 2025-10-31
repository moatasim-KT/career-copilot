# Celery Configuration
broker_url = "redis://localhost:6379/0"
result_backend = "redis://localhost:6379/0"

# Task Routing
task_routes = {
	"app.tasks.process_jobs": {"queue": "jobs"},
	"app.tasks.analyze_skills": {"queue": "analysis"},
	"app.tasks.update_recommendations": {"queue": "recommendations"},
}

# Task Settings
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "UTC"
enable_utc = True

# Queue Settings
task_queues = {
	"jobs": {
		"exchange": "jobs",
		"routing_key": "jobs.process",
	},
	"analysis": {
		"exchange": "analysis",
		"routing_key": "analysis.tasks",
	},
	"recommendations": {
		"exchange": "recommendations",
		"routing_key": "recommendations.update",
	},
}

# Worker Settings
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 1000

# Task Execution Settings
task_time_limit = 3600  # 1 hour
task_soft_time_limit = 3300  # 55 minutes

# Retry Settings
task_retry_delay_start = 3
task_max_retries = 3
task_default_rate_limit = "100/m"

# Monitoring Settings
worker_send_task_events = True
task_send_sent_event = True
task_track_started = True

# Schedule Settings
beat_schedule = {
	"process-jobs-periodic": {
		"task": "app.tasks.process_jobs",
		"schedule": 10800,  # Every 3 hours
		"options": {"queue": "jobs"},
	},
	"analyze-skills-weekly": {
		"task": "app.tasks.analyze_skills",
		"schedule": 604800,  # Weekly
		"options": {"queue": "analysis"},
	},
	"update-recommendations-daily": {
		"task": "app.tasks.update_recommendations",
		"schedule": 86400,  # Daily
		"options": {"queue": "recommendations"},
	},
}
