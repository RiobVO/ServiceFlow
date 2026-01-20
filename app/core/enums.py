from enum import Enum


class RequestStatus(str, Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    CANCELED = "CANCELED"


class UserRole(str, Enum):
    ADMIN = "admin"
    AGENT = "agent"
    EMPLOYEE = "employee"


class RequestAction(str, Enum):
    CREATED = "created"
    STATUS_CHANGED = "status_changed"
    ASSIGNEE_CHANGED = "assignee_changed"