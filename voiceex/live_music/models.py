from pydantic import BaseModel
from typing import Optional

class LivePart(BaseModel):
    time: int
    left3: Optional[int] = 0  # 6
    left2: Optional[int] = 0  # 4
    left: Optional[int] = 0  # 2
    center: Optional[int] = 0  # 1
    right: Optional[int] = 0  # 3
    right2: Optional[int] = 0  # 5
    right3: Optional[int] = 0  # 7

    def __init__(self, **data):
        if "lleft" in data:
            data["left2"] = data["lleft"]
        if "rright" in data:
            data["right2"] = data["rright"]
        super().__init__(**data)
