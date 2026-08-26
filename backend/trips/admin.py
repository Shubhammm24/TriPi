"""Django admin registration for the trips app.

Registering models with the admin site gives you a free data inspection
dashboard at /admin/ — one of Django's biggest advantages over FastAPI.
You can view, search, and filter sessions, itineraries, and tasks without
writing any frontend code.
"""

from django.contrib import admin

from trips.models import AgentTask, Itinerary, Message, Session, TripPreferences


class TripPreferencesInline(admin.StackedInline):
    model = TripPreferences
    extra = 0
    readonly_fields = [
        "budget", "duration", "start_date", "end_date",
        "origin", "destination", "purpose",
    ]


class ItineraryInline(admin.TabularInline):
    model = Itinerary
    extra = 0
    readonly_fields = ["version", "tool_calls", "created_at"]
    fields = ["version", "tool_calls", "created_at"]
    show_change_link = True


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ["role", "content", "created_at"]
    fields = ["role", "content", "created_at"]


class AgentTaskInline(admin.TabularInline):
    model = AgentTask
    extra = 0
    readonly_fields = [
        "id", "task_type", "status", "celery_task_id",
        "duration_seconds", "tokens_used", "created_at", "completed_at",
    ]
    fields = [
        "id", "task_type", "status", "duration_seconds",
        "tokens_used", "created_at", "completed_at",
    ]


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "status", "created_at", "last_active"]
    list_filter = ["status", "created_at", "last_active"]
    search_fields = ["id", "user__username"]
    readonly_fields = ["id", "thread_id", "created_at", "last_active"]
    inlines = [TripPreferencesInline, MessageInline, ItineraryInline, AgentTaskInline]


@admin.register(TripPreferences)
class TripPreferencesAdmin(admin.ModelAdmin):
    list_display = ["session", "origin", "destination", "duration", "budget"]
    list_filter = ["purpose", "hidden_gems_preference"]
    search_fields = ["origin", "destination"]


@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = ["session", "version", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["content"]
    readonly_fields = ["created_at"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["session", "role", "short_content", "created_at"]
    list_filter = ["role", "created_at"]
    search_fields = ["content"]
    readonly_fields = ["created_at"]

    @admin.display(description="Content")
    def short_content(self, obj):
        return obj.content[:80] + "…" if len(obj.content) > 80 else obj.content


@admin.register(AgentTask)
class AgentTaskAdmin(admin.ModelAdmin):
    list_display = [
        "id", "session", "task_type", "status",
        "duration_seconds", "tokens_used", "created_at", "completed_at",
    ]
    list_filter = ["status", "task_type", "created_at"]
    readonly_fields = [
        "id", "celery_task_id", "tools_used", "result",
        "error", "created_at", "completed_at",
    ]
