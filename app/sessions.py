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
        self._in_turn: set[str] = set()  # sessions with a turn being judged now
        # Forget idle sessions on a timer, not only when someone else arrives.
        sweeper = threading.Thread(target=self._sweep_forever, daemon=True)
        sweeper.start()

    def _sweep_forever(self) -> None:
        while True:
            time.sleep(60)
            with self._lock:
                self._forget_old()

    def begin_turn(self, session_id: str) -> bool:
        """False if this session already has a turn in progress."""
        with self._lock:
            if session_id in self._in_turn:
                return False
            self._in_turn.add(session_id)
            return True

    def end_turn(self, session_id: str) -> None:
        with self._lock:
            self._in_turn.discard(session_id)

    def forget_words(self, session: Session) -> None:
        """Once the summary is shown, drop everything the learner said and
        the copy kept for undo. Only the summary itself remains."""
        with self._lock:
            session.history.clear()
            session.notes.clear()
            session.first_words = ""
            session.topic_text = ""
            self._before.pop(session.id, None)

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
            self._forget_old()
            ordered = sorted(self._sessions.values(), key=lambda entry: entry[0], reverse=True)
            return [session for _, session in ordered[:limit]]

    def __len__(self) -> int:
        return len(self._sessions)
