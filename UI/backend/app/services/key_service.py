"""API-key handling. The database is the single source of truth (S2 fix).

Values are pushed into os.environ so the ragtime package / litellm can read
them. User keys are NO LONGER written into the .env file; deletions still
unset there so a removed secret cannot resurrect from disk on restart.

Because gunicorn runs several worker processes, a save on one worker leaves
the others with stale env vars — call ensure_fresh() at the points that
consume keys (job start, generation endpoints) to re-apply DB -> env in the
current process. It is one cheap SQLite query, unlike the removed
before_request hook that reloaded .env + DB on every request (B4 fix).
"""
import os

from dotenv import unset_key

from app.infra.storage import FILES_FOLDER
from app.models import APIKey, db

_ENV_PATH = str(FILES_FOLDER.parent / '.env')

# Names this process pushed into os.environ from the DB, so a key deleted
# from the DB can also be unset here on the next refresh.
_applied_names = set()


def apply_to_env():
    """Sync DB keys into os.environ for the current process (requires an
    app context). Unsets names previously applied but no longer stored."""
    keys = APIKey.query.filter_by(user_id='default').all()
    current = {key.name for key in keys}
    for name in _applied_names - current:
        os.environ.pop(name, None)
    for key in keys:
        os.environ[key.name] = key.value
    _applied_names.clear()
    _applied_names.update(current)
    return keys


def ensure_fresh():
    """Re-apply DB keys to the environment right before they are consumed."""
    apply_to_env()


MASK_MARKER = "\u2022" * 8  # ••••••••


def mask(value):
    """Return a display-safe version of a secret: first 3 and last 4 chars."""
    if not value:
        return ""
    if len(value) <= 8:
        return MASK_MARKER
    return f"{value[:3]}{MASK_MARKER}{value[-4:]}"


def is_masked(value):
    return isinstance(value, str) and MASK_MARKER in value


def list_keys():
    return APIKey.query.all()


def list_keys_masked():
    """Keys with masked values, for any response leaving the server.
    Plaintext secrets must never be sent to the client: the settings page
    only needs to know a key EXISTS, and re-posts the mask unchanged when
    saving (save_keys resolves it back to the stored value)."""
    return [{"name": k.name, "value": mask(k.value)} for k in APIKey.query.all()]


def save_keys(new_keys, deleted_keys):
    """Replace the stored keys with `new_keys` and remove `deleted_keys`.
    Mirrors the former routes.py behavior minus writing values to .env."""
    existing = {k.name: k.value for k in APIKey.query.filter_by(user_id='default').all()}

    resolved = []
    for key in new_keys:
        name, value = key.get('name'), key.get('value')
        if not name or value in (None, ''):
            continue
        if is_masked(value):
            # The settings page re-posts what it loaded (a mask). Resolve it
            # back to the real secret instead of overwriting the key with
            # bullet characters.
            value = existing.get(name) or os.environ.get(name)
            if not value:
                continue
        resolved.append((name, value))

    APIKey.query.filter_by(user_id='default').delete()
    for name, value in resolved:
        db.session.add(APIKey(name=name, value=value, user_id='default'))
    db.session.commit()

    # Remove deleted keys from the current process env, and from the .env
    # file if one exists (so old secrets written by previous versions of the
    # app do not come back after a restart).
    for key_name in deleted_keys:
        if os.path.exists(_ENV_PATH):
            try:
                unset_key(_ENV_PATH, key_name)
            except Exception:
                pass  # a malformed .env line must not block key deletion
        os.environ.pop(key_name, None)

    apply_to_env()
