from .celery_app import celery_app

# Import task modules to ensure they are registered when the package is loaded.
from . import tasks  # noqa: F401

__all__ = ("celery_app",)