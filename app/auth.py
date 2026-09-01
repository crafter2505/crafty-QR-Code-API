from fastapi import HTTPException, Depends
from fastapi.security import APIKeyHeader
from app.database import get_key_info, get_today_usage, log_usage
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)
PLAN_LIMITS = {
    "Free": 10,
    "Pro": 100,
    "Enterprise": 10000,
}
def verify_api_key(api_key: str = Depends(api_key_header)):
    key_data = get_key_info(api_key)
    if not key_data:
        raise HTTPException(status_code=401, detail="Invaild API key!!")
    if key_data.get("error"):
        raise HTTPException(status_code=401, detail=key_data["Error"])
    key_id = key_data["id"]
    plan = key_data["plan"]
    limit = PLAN_LIMITS.get(plan, 10)
    today_usage = get_today_usage(key_id)
    if today_usage >= limit:
        raise HTTPException(status_code=429, detail=f"Daily rate limit exceeded({limit} requests/day for {plan} plan)")
    log_usage(key_id, "generate")
    return key_data