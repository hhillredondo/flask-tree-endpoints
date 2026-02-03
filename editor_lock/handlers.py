from flask import jsonify, current_app

from auth.utils import get_current_user_id
from partition.middleware import get_current_tree_id
from .service import (
    acquire_editor_lock,
    get_editor_lock,
    release_editor_lock,
    force_release_editor_lock,
)


def get_lock_status():
    """Return the current editor lock status for a tree."""
    try:
        tree_id = get_current_tree_id()
        if not tree_id:
            return jsonify({
                "error": "Partition required",
                "message": "tree_id missing from partition context"
            }), 400

        lock = get_editor_lock(tree_id)
        return jsonify({
            "tree_id": tree_id,
            "locked": bool(lock),
            "lock": lock,
        }), 200
    except Exception as exc:
        current_app.logger.exception(f"Error getting editor lock: {exc}")
        return jsonify({"error": "Failed to fetch editor lock"}), 500


def acquire_lock():
    """Acquire editor lock for the current tree."""
    try:
        tree_id = get_current_tree_id()
        user_id = get_current_user_id()

        if not tree_id:
            return jsonify({
                "error": "Partition required",
                "message": "tree_id missing from partition context"
            }), 400

        if not user_id:
            return jsonify({
                "error": "Authentication required",
                "message": "User not authenticated"
            }), 401

        acquired, lock = acquire_editor_lock(tree_id, user_id)
        if not lock:
            return jsonify({
                "error": "Lock error",
                "message": (
                    "Unable to acquire editor lock. "
                    "Lock storage may be unavailable or misconfigured."
                ),
            }), 503

        if not acquired:
            return jsonify({
                "error": "Editor locked",
                "message": "Another user currently holds the editor lock",
                "lock": lock
            }), 409

        return jsonify({
            "message": "Editor lock acquired",
            "lock": lock
        }), 200
    except Exception as exc:
        current_app.logger.exception(f"Error acquiring editor lock: {exc}")
        return jsonify({"error": "Failed to acquire editor lock"}), 500


def release_lock():
    """Release editor lock for the current tree."""
    try:
        tree_id = get_current_tree_id()
        user_id = get_current_user_id()

        if not tree_id:
            return jsonify({
                "error": "Partition required",
                "message": "tree_id missing from partition context"
            }), 400

        if not user_id:
            return jsonify({
                "error": "Authentication required",
                "message": "User not authenticated"
            }), 401

        current_lock = get_editor_lock(tree_id)
        if not current_lock:
            return jsonify({
                "error": "No lock",
                "message": "No editor lock exists for this tree"
            }), 404

        released = release_editor_lock(tree_id, user_id)
        if not released:
            return jsonify({
                "error": "Editor locked",
                "message": "Only the lock owner can release the editor lock",
                "lock": current_lock
            }), 403

        return jsonify({
            "message": "Editor lock released",
            "tree_id": tree_id
        }), 200
    except Exception as exc:
        current_app.logger.exception(f"Error releasing editor lock: {exc}")
        return jsonify({"error": "Failed to release editor lock"}), 500


def force_release_lock():
    """Owner-only force release of editor lock for the current tree."""
    try:
        tree_id = get_current_tree_id()
        if not tree_id:
            return jsonify({
                "error": "Partition required",
                "message": "tree_id missing from partition context"
            }), 400

        current_lock = get_editor_lock(tree_id)
        if not current_lock:
            return jsonify({
                "error": "No lock",
                "message": "No editor lock exists for this tree"
            }), 404

        released = force_release_editor_lock(tree_id)
        if not released:
            return jsonify({
                "error": "Force unlock failed",
                "message": "Could not force release editor lock"
            }), 500

        return jsonify({
            "message": "Editor lock force-released",
            "tree_id": tree_id,
            "previous_lock": current_lock,
        }), 200
    except Exception as exc:
        current_app.logger.exception(f"Error force releasing editor lock: {exc}")
        return jsonify({"error": "Failed to force release editor lock"}), 500

