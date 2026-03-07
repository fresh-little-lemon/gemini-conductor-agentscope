from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class RunEvent(BaseModel):
    type: str
    runId: Optional[str] = None
    ts: str = Field(default_factory=lambda: datetime.now().isoformat())
    payload: Dict[str, Any] = Field(default_factory=dict)
