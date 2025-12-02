import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


logger = logging.getLogger(__name__)


@dataclass
class SessionEvent:
    timestamp: float
    event_type: str
    detail: Optional[str] = None
    error: Optional[str] = None


@dataclass
class SessionInfo:
    session_id: str
    user_id: str
    agent_name: str
    created_at: float = field(default_factory=time.time)
    last_event_at: float = field(default_factory=time.time)
    status: str = "created"
    message_count: int = 0
    error_count: int = 0
    events: List[SessionEvent] = field(default_factory=list)
    alerts: List[str] = field(default_factory=list)


class SessionMonitor:
    """Lightweight in-memory monitor for ADK sessions."""

    def __init__(self, max_events: int = 50):
        self.sessions: Dict[str, SessionInfo] = {}
        self.max_events = max_events

    def _get_or_create(self, session_id: str, user_id: str, agent_name: str) -> SessionInfo:
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionInfo(
                session_id=session_id,
                user_id=user_id,
                agent_name=agent_name,
            )
        return self.sessions[session_id]

    def log_event(
        self,
        session_id: str,
        user_id: str,
        agent_name: str,
        event_type: str,
        detail: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        session = self._get_or_create(session_id, user_id, agent_name)
        now = time.time()
        session.last_event_at = now
        if event_type.lower() in {"error", "failed"}:
            session.status = "error"
            session.error_count += 1
        elif event_type.lower() in {"completed", "ended", "finished"}:
            session.status = "completed"
        else:
            session.status = "active"

        event = SessionEvent(timestamp=now, event_type=event_type, detail=detail, error=error)
        session.events.append(event)
        if len(session.events) > self.max_events:
            session.events = session.events[-self.max_events :]

        # Add alert text for chat surfacing
        alert_parts = [f"Session {session_id}: {event_type}"]
        if detail:
            alert_parts.append(detail)
        if error:
            alert_parts.append(f"error={error}")
        session.alerts.append(" | ".join(alert_parts))

        logger.info(
            "session_event",
            extra={
                "session_id": session_id,
                "user_id": user_id,
                "agent_name": agent_name,
                "event_type": event_type,
                "detail": detail,
                "error": error,
                "status": session.status,
            },
        )

    def record_message(self, session_id: str, user_id: str, agent_name: str) -> None:
        session = self._get_or_create(session_id, user_id, agent_name)
        session.message_count += 1
        session.last_event_at = time.time()

    def pop_alerts(self, session_id: str) -> List[str]:
        session = self.sessions.get(session_id)
        if not session:
            return []
        alerts = list(session.alerts)
        session.alerts.clear()
        return alerts

    def get_summary(self) -> str:
        if not self.sessions:
            return "No sessions recorded."

        parts = []
        for info in self.sessions.values():
            age = int(time.time() - info.created_at)
            last = int(time.time() - info.last_event_at)
            parts.append(
                f"- {info.session_id} (user={info.user_id}, agent={info.agent_name}): "
                f"status={info.status}, messages={info.message_count}, errors={info.error_count}, "
                f"age={age}s, last_event={last}s ago"
            )
        return "\n".join(parts)

    def get_details(self, session_id: str) -> str:
        info = self.sessions.get(session_id)
        if not info:
            return f"No session found for id {session_id}."
        lines = [
            f"Session {session_id} (user={info.user_id}, agent={info.agent_name})",
            f"Status: {info.status}",
            f"Messages: {info.message_count}, Errors: {info.error_count}",
            f"Created: {time.ctime(info.created_at)}",
            f"Last event: {time.ctime(info.last_event_at)}",
            "Recent events:",
        ]
        for e in info.events[-10:]:
            lines.append(
                f"  - {time.ctime(e.timestamp)} | {e.event_type}"
                + (f" | {e.detail}" if e.detail else "")
                + (f" | error={e.error}" if e.error else "")
            )
        return "\n".join(lines)


# Global monitor instance to be reused across app
session_monitor = SessionMonitor()
