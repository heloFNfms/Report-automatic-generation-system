from pydantic import BaseModel
from typing import Any, Dict


class ToolBase:
    name: str
    description: str
    metadata: Dict[str, Any]


    async def run(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError