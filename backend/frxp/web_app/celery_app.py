from celery import Celery
# Celery app for local testing with localhost
celery_app = Celery('fractal_worker',
                     broker='redis://localhost:6379/0', 
                     backend='redis://localhost:6379/0',
                     include=['celery_worker'])
# Celery app for deployed web server with Docker Compose service
#celery_app = Celery('fractal_worker', broker='redis://redis:6379/0', backend='redis://redis:6379/0')

# Create the Celery application instance.
# This file serves as the single source for the Celery app configuration.
# Other files will import `celery_app` from here to avoid circular imports.