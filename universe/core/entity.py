from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import uuid

@dataclass
class Entity:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    entity_type: str = "agent"
    sex: Optional[str] = None
    age: int = 0
    energy: float = 100.0
    health: float = 100.0
    location: tuple = (0, 0)
    
    characteristics: Dict[str, Any] = field(default_factory=dict)
    
    parents: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)
    
    knowledge: List[str] = field(default_factory=list)
    memory: List[str] = field(default_factory=list)
    
    alive: bool = True

    def add_characteristic(self, key: str, value: Any):
        self.characteristics[key] = value

    def get(self, key: str, default=None):
        return self.characteristics.get(key, default)