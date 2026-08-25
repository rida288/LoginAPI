from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from app.service.chat_service import ChatService

# Application-lifetime cache of ChatService instances, keyed by project_id.
# This avoids re-building the LLM client, pandas agent, and LangGraph react
# agent on every single chat request — only the DB-session-dependent search
# tool is rebuilt per request (inside ask_question).
_chat_service_cache: Dict[int, "ChatService"] = {}


def get_cached_chat_service(project_id: int, file_path: str) -> "ChatService":
    """
    Returns a cached ChatService for the given project, constructing it once
    and reusing it for all subsequent requests to the same project.
    """
    if project_id not in _chat_service_cache:
        from app.service.chat_service import ChatService
        print(f"[InsightAI] Building ChatService for project {project_id} (first request)...")
        _chat_service_cache[project_id] = ChatService(
            project_id=project_id,
            file_path=file_path,
        )
    return _chat_service_cache[project_id]


def invalidate_chat_service(project_id: int) -> None:
    """
    Removes the cached ChatService for a project.
    Must be called when a project is deleted so stale state is cleared.
    """
    removed = _chat_service_cache.pop(project_id, None)
    if removed:
        print(f"[InsightAI] Evicted ChatService cache for deleted project {project_id}")
