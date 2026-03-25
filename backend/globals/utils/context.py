from contextvars import ContextVar
from typing import Dict, Any

logs_context: ContextVar[Dict[str, Any]] = ContextVar("logs_context", default={})


async def set_log_context(**kwargs: Any) -> None:
    """Set key-value pairs in the logging context."""
    try:
        context = logs_context.get().copy()
        context.update(kwargs)
        logs_context.set(context)
    except Exception as e:
        print(f"Error setting log context: {str(e)}")


def get_log_context():
    """Retrieve the current logging context."""
    try:
        return logs_context.get()
    except Exception as e:
        print(f"Error getting log context: {str(e)}")
        return {}

async def clear_log_context():
    """Clear the logging context after each request."""
    try:
        logs_context.set({})
    except Exception as e:
        print(f"Error clearing log context: {str(e)}")
