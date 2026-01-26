# Integration Examples

## Backend: пример маршрута для ping

```py
from fastapi import APIRouter

router = APIRouter(prefix="/integration")

@router.get("/ping")
def ping() -> dict[str, str]:
    return {"status": "ok"}
```

## Frontend: вызов через API client

```ts
import { api } from "../services/api";

const requests = await api.listRequests(apiKey, "?limit=5");
```
