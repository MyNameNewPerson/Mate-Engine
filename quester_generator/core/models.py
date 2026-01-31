# core/models.py
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Zone:
    id: int
    name: str

@dataclass
class Quest:
    entry: int
    title: str
    min_level: int
    quest_level: int
    zone_or_sort: int
    required_races: int
    prev_quest_id: int = 0
    next_quest_id: int = 0
    next_quest_in_chain: int = 0
    special_flags: int = 0
    details: str = ""

@dataclass
class Objective:
    quest_id: int
    slot: int
    type: str          # 'kill', 'gather', 'loot', 'unknown'
    target_id: Optional[int] = None
    item_id: Optional[int] = None
    count: int = 1

@dataclass
class FarmZone:
    map_id: int
    center_x: float
    center_y: float
    center_z: float
    radius: float = 80.0

@dataclass
class Vector3:
    x: float
    y: float
    z: float

@dataclass
class GrindTask:
    mob_id: int
    mob_name: str
    hotspots: List[Vector3]
    stop_level: int
    zone_id: int

@dataclass
class CustomPath:
    name: str
    x: float
    y: float
    z: float

@dataclass
class ZoneProject:
    zone_id: int
    zone_name: str
    selected_quest_ids: List[int] = field(default_factory=list)
    grind_tasks: List[GrindTask] = field(default_factory=list)
    custom_paths: List[CustomPath] = field(default_factory=list)

@dataclass
class ProjectState:
    faction: str = "alliance"
    zones: List[ZoneProject] = field(default_factory=list)
