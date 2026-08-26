"""Celery tasks that run the LangGraph agent in a background worker.

Why not run the agent inline in the Django view?
- Agent runs take 30-60 seconds and call 8+ external APIs.
- Django's default WSGI model uses a fixed worker pool (e.g. 4 Gunicorn
  workers). Blocking one for 60s means 25% of capacity is gone.
- Celery workers are a separate process pool that scales independently.
- Bonus: retry on failure, configurable timeouts, and monitoring via Flower.

These tasks import from agent/ and tools/ which sit at the project root.
The sys.path addition in settings.py ensures they're importable.
"""

import logging
import time
import traceback

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from langchain_core.messages import HumanMessage

logger = logging.getLogger("trips.tasks")

# Lazy-loaded agent singleton (one per worker process)
_agent = None


def _get_agent():
    """Build the LangGraph agent once per Celery worker process."""
    global _agent
    if _agent is None:
        from agent.graph import build_agent

        _agent = build_agent(settings.GOOGLE_API_KEY)
        logger.info("LangGraph agent built successfully")
    return _agent


def _invoke_agent(message: str, thread_id: str) -> tuple[str, list[str]]:
    """Run the agent with a human message and return (response, tool_names).

    This is a direct port of the _invoke_agent() helper from main.py.
    """
    agent = _get_agent()
    config = {"configurable": {"thread_id": thread_id}}

    logger.info("Invoking agent with thread=%s, prompt=%s...", thread_id, message[:200])

    result = agent.invoke({"messages": [HumanMessage(content=message)]}, config)

    messages = result.get("messages", [])
    ai_response = ""
    tool_names: list[str] = []

    for msg in messages:
        msg_type = getattr(msg, "type", None)
        if msg_type == "ai":
            content = getattr(msg, "content", "")
            if isinstance(content, str) and content.strip():
                ai_response = content
            elif isinstance(content, list):
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_parts.append(part.get("text", ""))
                    elif isinstance(part, str):
                        text_parts.append(part)
                joined = "\n".join(text_parts).strip()
                if joined:
                    ai_response = joined
        elif msg_type == "tool":
            name = getattr(msg, "name", None)
            if name:
                tool_names.append(name)

    logger.info("Agent finished: %d tools used, %d chars response", len(tool_names), len(ai_response))
    return ai_response, tool_names


@shared_task(bind=True, max_retries=1, time_limit=120, soft_time_limit=100)
def run_agent_task(self, task_id: str, session_id: str, prompt: str, thread_id: str, task_type: str):
    """Execute the LangGraph agent and persist the result.

    Args:
        task_id: UUID of the AgentTask model instance.
        session_id: UUID of the Session.
        prompt: The text prompt to send to the agent.
        thread_id: LangGraph MemorySaver thread ID.
        task_type: One of 'generate', 'refine', 'chat'.

    The task updates both AgentTask and Session through status transitions:
    AgentTask: pending → running → completed/failed
    Session:   pending → running → completed/failed (on first generate)
    """
    from trips.models import AgentTask, Itinerary, Message, Session

    start_time = time.time()

    try:
        agent_task = AgentTask.objects.get(id=task_id)
        agent_task.status = AgentTask.Status.RUNNING
        agent_task.save(update_fields=["status"])

        # Update session status
        session = Session.objects.get(id=session_id)
        if session.status in (Session.Status.PENDING, Session.Status.FAILED):
            session.status = Session.Status.RUNNING
            session.save(update_fields=["status"])

        logger.info("[Task %s] Running %s for session %s", task_id, task_type, session_id)

        # Persist the user message
        Message.objects.create(
            session=session,
            role=Message.Role.USER,
            content=prompt,
        )

        itinerary_text, tools_used = _invoke_agent(prompt, thread_id)

        if not itinerary_text:
            itinerary_text = (
                "The agent did not return an itinerary. "
                "This may be a temporary issue. Please try again."
            )

        # Persist the assistant response message
        Message.objects.create(
            session=session,
            role=Message.Role.ASSISTANT,
            content=itinerary_text,
        )

        # Save the itinerary to the database
        latest_version = (
            Itinerary.objects.filter(session=session)
            .order_by("-version")
            .values_list("version", flat=True)
            .first()
        ) or 0

        Itinerary.objects.create(
            session=session,
            version=latest_version + 1,
            content=itinerary_text,
            tool_calls=tools_used,
        )

        # Update the session
        session.status = Session.Status.COMPLETED
        session.save(update_fields=["status", "last_active"])

        # Calculate duration
        duration = time.time() - start_time

        # Build the result payload (same shape as old ItineraryResponse)
        result_payload = {
            "session_id": str(session_id),
            "itinerary": itinerary_text,
            "tool_calls": tools_used,
            "error": None,
        }

        agent_task.status = AgentTask.Status.COMPLETED
        agent_task.result = result_payload
        agent_task.tools_used = tools_used
        agent_task.duration_seconds = round(duration, 2)
        agent_task.completed_at = timezone.now()
        agent_task.save(update_fields=[
            "status", "result", "tools_used",
            "duration_seconds", "completed_at",
        ])

        logger.info(
            "[Task %s] Completed in %.1fs, %d tools used",
            task_id, duration, len(tools_used),
        )

    except Exception as exc:
        duration = time.time() - start_time
        error_detail = traceback.format_exc()
        logger.error("[Task %s] Failed after %.1fs: %s", task_id, duration, error_detail)

        try:
            agent_task = AgentTask.objects.get(id=task_id)
            agent_task.status = AgentTask.Status.FAILED
            agent_task.error = str(exc)
            agent_task.duration_seconds = round(duration, 2)
            agent_task.result = {
                "session_id": str(session_id),
                "itinerary": f"## ⚠️ Error\n\nSomething went wrong: **{str(exc)}**\n\n"
                             f"Please check that your `GOOGLE_API_KEY` is valid and try again.",
                "tool_calls": [],
                "error": str(exc),
            }
            agent_task.completed_at = timezone.now()
            agent_task.save(update_fields=[
                "status", "error", "result",
                "duration_seconds", "completed_at",
            ])

            # Mark session as failed
            session = Session.objects.get(id=session_id)
            session.status = Session.Status.FAILED
            session.save(update_fields=["status"])

        except Exception:
            logger.error(
                "[Task %s] Failed to update task status: %s",
                task_id, traceback.format_exc(),
            )

        # Let Celery retry once on failure
        raise self.retry(exc=exc, countdown=5)


@shared_task
def recover_stuck_tasks():
    """Mark tasks stuck in 'running' for >5 minutes as failed.

    Why this exists:
    - If a Celery worker crashes mid-task, the AgentTask row stays in
      'running' forever. No one is coming to update it.
    - This task runs periodically (via Celery beat or a management command)
      to clean up orphaned tasks and unblock the frontend.

    Schedule this in Celery beat:
        CELERY_BEAT_SCHEDULE = {
            'recover-stuck-tasks': {
                'task': 'trips.tasks.recover_stuck_tasks',
                'schedule': 300.0,  # every 5 minutes
            },
        }
    """
    from trips.models import AgentTask, Session

    cutoff = timezone.now() - timezone.timedelta(minutes=5)
    stuck = AgentTask.objects.filter(
        status=AgentTask.Status.RUNNING,
        created_at__lt=cutoff,
    )

    count = 0
    for task in stuck:
        task.status = AgentTask.Status.FAILED
        task.error = "Task timed out — worker may have crashed."
        task.completed_at = timezone.now()
        task.save(update_fields=["status", "error", "completed_at"])

        # Also mark the session as failed
        task.session.status = Session.Status.FAILED
        task.session.save(update_fields=["status"])
        count += 1

    if count:
        logger.warning("Recovered %d stuck tasks", count)
