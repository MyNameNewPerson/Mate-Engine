# data_access/trainer_repo.py
from core.db import Database
from core.logger import get_logger
from typing import List, Dict, Any

logger = get_logger(__name__)

CLASS_MAP = {
    "Warrior": 1,
    "Paladin": 2,
    "Hunter": 3,
    "Rogue": 4,
    "Priest": 5,
    "Shaman": 7,
    "Mage": 8,
    "Warlock": 9,
    "Druid": 11
}

def get_class_trainers(db: Database, map_id: int) -> List[Dict[str, Any]]:
    """
    Находит всех классовых тренеров на континенте.
    NPC Flag 16 = Trainer
    TrainerType 0 = Class Trainer
    """
    query = """
    SELECT
        c.id as entry,
        ct.Name as name,
        ct.TrainerClass as class_id,
        c.position_x as x,
        c.position_y as y,
        c.position_z as z
    FROM creature c
    JOIN creature_template ct ON c.id = ct.entry
    WHERE c.map = %s
      AND (ct.NpcFlags & 16 = 16)
      AND ct.TrainerType = 0
    """
    results = db.execute(query, (map_id,))

    trainers = []
    seen_ids = set()

    # Реверсивный маппинг имен классов
    id_to_class = {v: k for k, v in CLASS_MAP.items()}

    for row in results:
        if row['entry'] not in seen_ids:
            class_name = id_to_class.get(row['class_id'], "Unknown")
            trainers.append({
                'Id': row['entry'],
                'Name': f"{row['name']} ({class_name} Trainer)",
                'Type': "Trainer",
                'X': float(row['x']),
                'Y': float(row['y']),
                'Z': float(row['z']),
                'Class': class_name
            })
            seen_ids.add(row['entry'])

    return trainers
