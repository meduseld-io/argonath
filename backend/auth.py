"""
Argonath Authentication
Simple local auth with session cookies.
Modes: "local" (username/password), "none" (no auth).
"""

import functools
import logging

from flask import session, request, jsonify, redirect, url_for

from config import AUTH_MODE
from models import authenticate_user, create_user, user_count, get_user_by_id

logger = logging.getLogger(__name__)


def get_current_user():
    """Get the currently logged-in user from session"""
    if AUTH_MODE == "none":
        return {"id": 0, "username": "admin", "role": "admin"}

    user_id = session.get("user_id")
    if user_id:
        return get_user_by_id(user_id)
    return None


def require_auth(f):
    """Decorator: require authentication"""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if AUTH_MODE == "none":
            return f(*args, **kwargs)

        user = get_current_user()
        if not user:
            if request.is_json or request.headers.get("Accept") == "application/json":
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    """Decorator: require admin role"""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if AUTH_MODE == "none":
            return f(*args, **kwargs)

        user = get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        if user["role"] != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated


def login(username, password):
    """Attempt to log in. Returns user dict or None."""
    user = authenticate_user(username, password)
    if user:
        session["user_id"] = user["id"]
        session.permanent = True
        logger.info(f"User logged in: {username}")
        return user
    return None


def logout():
    """Log out the current user"""
    session.clear()


def register(username, password):
    """Register a new user. First user becomes admin."""
    # Determine role
    role = "admin" if user_count() == 0 else "viewer"

    user = create_user(username, password, role)
    if user:
        session["user_id"] = user["id"]
        session.permanent = True
        logger.info(f"User registered: {username} (role: {role})")
        return user
    return None
