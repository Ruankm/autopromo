"""API endpoints initialization."""
from .auth import router as auth_router
from .webhooks import router as webhooks_router
from .groups import router as groups_router
from .tags import router as tags_router
from .dashboard import router as dashboard_router
from .whatsapp import router as whatsapp_router

__all__ = [
    "auth_router", 
    "webhooks_router", 
    "groups_router", 
    "tags_router", 
    "dashboard_router",
    "whatsapp_router"
]
