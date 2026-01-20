from typing import Sequence  # если нужно для type-hint в list_request_logs

from sqlalchemy.orm import Session

from app.models.request_log import RequestLog
from app.core.enums import RequestAction


def add_request_log(
    db: Session,
    *,
    request_id: int,
    user_id: int,
    action: RequestAction | str,
    old_value: str | None = None,
    new_value: str | None = None,
    client_ip: str | None = None,
    user_agent: str | None = None,
    comment: str | None = None,
    source: str = "API",
) -> RequestLog:
    """
    Логирует любое изменение по заявке.
    """

    if isinstance(action, RequestAction):
        action_value = action.value
    else:
        action_value = str(action)

    log = RequestLog(
        request_id=request_id,
        user_id=user_id,
        action=action_value,
        old_value=old_value,
        new_value=new_value,
        client_ip=client_ip,
        user_agent=user_agent,
        comment=comment,
        source=source,
    )

    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def list_request_logs(db: Session, request_id: int) -> list[RequestLog]:
    return (
        db.query(RequestLog)
        .filter(RequestLog.request_id == request_id)
        .order_by(RequestLog.timestamp.asc())
        .all()
    )
