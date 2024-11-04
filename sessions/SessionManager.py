import time
import uuid
from threading import Lock
from datetime import datetime, timedelta

class Session:
    def __init__(self, user_id):
        self.session_id = str(uuid.uuid4())
        self.user_id = user_id
        self.created_at = datetime.utcnow()
        self.last_active = datetime.utcnow()
        self.is_active = True
        self.expires_at = self.created_at + timedelta(hours=2)  # Session timeout after 2 hours

    def refresh(self):
        """Refreshes the last active timestamp and extends the session expiration."""
        self.last_active = datetime.utcnow()
        self.expires_at = self.last_active + timedelta(hours=2)

    def is_expired(self):
        """Checks if the session has expired."""
        return datetime.utcnow() > self.expires_at

class SessionManager:
    def __init__(self):
        self.sessions = {}  # Keyed by session_id
        self.user_sessions = {}  # Keyed by user_id
        self.lock = Lock()  # To prevent race conditions during session operations

    def create_session(self, user_id):
        """Creates a new session for a user."""
        with self.lock:
            session = Session(user_id)
            self.sessions[session.session_id] = session
            self.user_sessions[user_id] = session.session_id
            return session

    def get_session(self, session_id):
        """Retrieves a session by session_id."""
        with self.lock:
            session = self.sessions.get(session_id)
            if session and not session.is_expired():
                return session
            return None

    def get_session_by_user(self, user_id):
        """Retrieves a session by user_id."""
        with self.lock:
            session_id = self.user_sessions.get(user_id)
            if session_id:
                return self.get_session(session_id)
            return None

    def refresh_session(self, session_id):
        """Refreshes an active session."""
        with self.lock:
            session = self.get_session(session_id)
            if session and not session.is_expired():
                session.refresh()
                return session
            return None

    def terminate_session(self, session_id):
        """Terminates a session by session_id."""
        with self.lock:
            session = self.sessions.pop(session_id, None)
            if session:
                session.is_active = False
                self.user_sessions.pop(session.user_id, None)
                return True
            return False

    def terminate_session_by_user(self, user_id):
        """Terminates a session by user_id."""
        with self.lock:
            session_id = self.user_sessions.get(user_id)
            if session_id:
                return self.terminate_session(session_id)
            return False

    def clean_expired_sessions(self):
        """Cleans up expired sessions from the session store."""
        with self.lock:
            expired_sessions = [sid for sid, session in self.sessions.items() if session.is_expired()]
            for sid in expired_sessions:
                self.terminate_session(sid)

    def is_user_active(self, user_id):
        """Checks if a user has an active session."""
        session = self.get_session_by_user(user_id)
        return session is not None and session.is_active

    def list_active_sessions(self):
        """Lists all active sessions."""
        with self.lock:
            return [session for session in self.sessions.values() if session.is_active]

class SessionCleaner:
    def __init__(self, session_manager, interval=300):
        """
        Automatically cleans up expired sessions every 'interval' seconds.
        :param session_manager: An instance of SessionManager to manage sessions.
        :param interval: Time interval (in seconds) for session cleanup.
        """
        self.session_manager = session_manager
        self.interval = interval
        self.stop_cleaner = False

    def start(self):
        """Starts the session cleaner in a background thread."""
        while not self.stop_cleaner:
            time.sleep(self.interval)
            self.session_manager.clean_expired_sessions()

    def stop(self):
        """Stops the session cleaner."""
        self.stop_cleaner = True

# Usage
if __name__ == "__main__":
    session_manager = SessionManager()

    # Create a new session for a user
    user_id = "user_123"
    session = session_manager.create_session(user_id)
    print(f"Session created for {user_id}: {session.session_id}")

    # Get the session by session_id
    fetched_session = session_manager.get_session(session.session_id)
    print(f"Fetched session: {fetched_session.session_id}")

    # Refresh the session to extend its expiration
    session_manager.refresh_session(session.session_id)
    print(f"Session {session.session_id} refreshed.")

    # Check if user has an active session
    is_active = session_manager.is_user_active(user_id)
    print(f"User {user_id} is active: {is_active}")

    # Terminate the session
    session_manager.terminate_session(session.session_id)
    print(f"Session {session.session_id} terminated.")

    # Clean up expired sessions (this will run in the background)
    cleaner = SessionCleaner(session_manager)
    cleaner.start()