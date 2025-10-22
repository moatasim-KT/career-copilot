from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    components: Dict[str, Any]
