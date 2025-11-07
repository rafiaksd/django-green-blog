from datetime import datetime

def current_time(request):
    """Adds the current time to the context."""
    return {'current_time': datetime.now()}
