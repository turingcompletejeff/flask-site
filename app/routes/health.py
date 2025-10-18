from flask import Blueprint, jsonify
from sqlalchemy import text
from datetime import datetime, timezone
from app import db, __version__
import time

health_bp = Blueprint('health', __name__)

# Cache for database health check (30 second TTL)
_db_health_cache = {
    'result': None,
    'timestamp': None,
    'ttl_seconds': 30
}

def check_database():
    """
    Check database connectivity with caching.
    Returns cached result if < 30 seconds old.
    """
    now = time.time()

    # Return cached result if still valid
    if (_db_health_cache['result'] is not None and
        _db_health_cache['timestamp'] is not None and
        now - _db_health_cache['timestamp'] < _db_health_cache['ttl_seconds']):

        result = _db_health_cache['result'].copy()
        result['cached'] = True
        return result

    # Perform fresh check
    try:
        start_time = time.time()
        db.session.execute(text('SELECT 1'))
        response_time = (time.time() - start_time) * 1000  # ms

        result = {
            "status": "up",
            "message": "Database connected",
            "response_time_ms": round(response_time, 2),
            "cached": False
        }

        # Cache the successful result
        _db_health_cache['result'] = result.copy()
        _db_health_cache['timestamp'] = now

        return result

    except Exception as e:
        result = {
            "status": "down",
            "message": f"Database connection failed: {str(e)}",
            "response_time_ms": None,
            "cached": False
        }

        # Don't cache failures - try again next time
        _db_health_cache['result'] = None
        _db_health_cache['timestamp'] = None

        return result

@health_bp.route('/health')
def health_check():
    """
    Health check endpoint for monitoring and container orchestration.
    Returns 200 if healthy, 503 if any check fails.
    """
    # Always healthy - app is running if we got here
    app_check = {
        "status": "up",
        "message": "Application running"
    }

    # Check database with caching
    db_check = check_database()

    # Determine overall health
    all_healthy = (app_check["status"] == "up" and
                   db_check["status"] == "up")

    response = {
        "status": "healthy" if all_healthy else "unhealthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": __version__,
        "checks": {
            "app": app_check,
            "database": db_check
        }
    }

    # Return appropriate HTTP status
    status_code = 200 if all_healthy else 503
    return jsonify(response), status_code