"""Sessions live in memory only, and are forgotten after a while.

Nothing is written to disk. When a session expires, the learner's words
are gone. One process holds them all, which is why the app runs one worker.
"""

import copy
import threading
import time

from app.tutor.engine import new_session
from app.tutor.models import Session

MAX_SESSIONS = 2000


class SessionStore:
    def __init__(self, ttl_minutes: int = 30):
        self.ttl_seconds = ttl_minutes * 60
        self._sessions: dict[str, tuple[float, Session]] = {}
        self._before: dict[str, Session] = {}  # each session as it was one turn ago
        self._lock = threading.Lock()

    def create(self, voice: str = "male") -> Session:
        session = new_session(voice)
        with self._lock:
            self._forget_old()
            if len(self._sessions) >= MAX_SESSIONS:
                oldest = min(self._sessions, key=lambda key: self._sessions[key][0])
                del self._sessions[oldest]
                self._before.pop(oldest, None)
            self._sessions[session.id] = (time.monotonic(), session)
        return session

    def get(self, session_id: str) -> Session | None:
        """The session, or None if it never existed or has expired."""
        with self._lock:
            self._forget_old()
            entry = self._sessions.get(session_id)
            if entry is None:
                return None
            self._sessions[session_id] = (time.monotonic(), entry[1])
            return entry[1]

    def remember(self, session: Session) -> None:
        """Keeps a copy of the session as it stands, before a turn changes it."""
        with self._lock:
            self._before[session.id] = copy.deepcopy(session)

    def rewind(self, session: Session) -> None:
        """Undoes the last turn, so a misheard answer can be said again."""
        with self._lock:
            before = self._before.get(session.id)
            if before is not None:
                session.__dict__.update(copy.deepcopy(before).__dict__)

    def _forget_old(self) -> None:
        cutoff = time.monotonic() - self.ttl_seconds
        for key in [k for k, (seen, _) in self._sessions.items() if seen < cutoff]:
            del self._sessions[key]
            self._before.pop(key, None)

    def recent(self, limit: int = 10) -> list[Session]:
        """The most recently used sessions, newest first. For the developer's viewer."""
        with self._lock:
            ordered = sorted(self._sessions.values(), key=lambda entry: entry[0], reverse=True)
            return [session for _, session in ordered[:limit]]

    def __len__(self) -> int:
        return len(self._sessions)
