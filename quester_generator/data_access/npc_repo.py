# data_access/npc_repo.py
from core.db import Database
from core.logger import get_logger
from typing import Optional, Dict, Any, List
# Импортируем проверку границ, чтобы фильтровать вендоров по зоне
from core.coord_converter import is_coords_in_bounds, get_zone_dimensions

logger = get_logger(__name__)

def get_quest_starter_type(db: Database, quest_id: int) -> str:
    """
    Определяет тип стартера квеста через SQL.
    Возвращает: 'npc', 'object', 'item' или 'unknown'.
    """
    # 1. Проверяем NPC
    npc_query = "SELECT id FROM creature_questrelation WHERE quest = %s LIMIT 1"
    if db.execute(npc_query, (quest_id,)):
        return 'npc'

    # 2. Проверяем Объекты (GameObjects)
    go_query = "SELECT id FROM gameobject_questrelation WHERE quest = %s LIMIT 1"
    if db.execute(go_query, (quest_id,)):
        return 'object'

    # 3. Проверяем Предметы (Item-started)
    item_query = "SELECT entry FROM item_template WHERE startquest = %s LIMIT 1"
    if db.execute(item_query, (quest_id,)):
        return 'item'

    return 'unknown'

def get_quest_starter_npc(db: Database, quest_id: int) -> Optional[Dict[str, Any]]:
    query = """
    SELECT
        ct.entry AS entity_id,
        ct.Name AS entity_name,
        c.position_x AS x,
        c.position_y AS y,
        c.position_z AS z,
        c.map
    FROM creature_questrelation cq
    JOIN creature c ON cq.id = c.id
    JOIN creature_template ct ON cq.id = ct.entry
    WHERE cq.quest = %s
    LIMIT 1
    """
    results = db.execute(query, (quest_id,))
    if results:
        res = results[0]
        # Конвертируем Decimal в float во избежание ошибок
        res['x'] = float(res['x'])
        res['y'] = float(res['y'])
        res['z'] = float(res['z'])
        return res
    return None

def get_quest_ender_npc(db: Database, quest_id: int) -> Optional[Dict[str, Any]]:
    query = """
    SELECT
        ct.entry AS entity_id,
        ct.Name AS entity_name,
        c.position_x AS x,
        c.position_y AS y,
        c.position_z AS z,
        c.map
    FROM creature_involvedrelation cq
    JOIN creature c ON cq.id = c.id
    JOIN creature_template ct ON cq.id = ct.entry
    WHERE cq.quest = %s
    LIMIT 1
    """
    results = db.execute(query, (quest_id,))
    if results:
        res = results[0]
        res['x'] = float(res['x'])
        res['y'] = float(res['y'])
        res['z'] = float(res['z'])
        return res
    return None

def get_quest_starter_go(db: Database, quest_id: int) -> Optional[Dict[str, Any]]:
    query = """
    SELECT
        gt.entry AS entity_id,
        gt.name AS entity_name,
        g.position_x AS x,
        g.position_y AS y,
        g.position_z AS z,
        g.map
    FROM gameobject_questrelation gq
    JOIN gameobject g ON gq.id = g.id
    JOIN gameobject_template gt ON gq.id = gt.entry
    WHERE gq.quest = %s
    LIMIT 1
    """
    results = db.execute(query, (quest_id,))
    if results:
        res = results[0]
        res['x'] = float(res['x'])
        res['y'] = float(res['y'])
        res['z'] = float(res['z'])
        return res
    return None

def get_quest_ender_go(db: Database, quest_id: int) -> Optional[Dict[str, Any]]:
    query = """
    SELECT
        gt.entry AS entity_id,
        gt.name AS entity_name,
        g.position_x AS x,
        g.position_y AS y,
        g.position_z AS z,
        g.map
    FROM gameobject_involvedrelation gq
    JOIN gameobject g ON gq.id = g.id
    JOIN gameobject_template gt ON gq.id = gt.entry
    WHERE gq.quest = %s
    LIMIT 1
    """
    results = db.execute(query, (quest_id,))
    if results:
        res = results[0]
        res['x'] = float(res['x'])
        res['y'] = float(res['y'])
        res['z'] = float(res['z'])
        return res
    return None

def get_zone_vendors(db: Database, zone_id: int) -> List[Dict[str, Any]]:
    """
    Находит всех вендоров и ремонтников в указанной зоне.
    NPC Flag 128 = Vendor
    NPC Flag 4096 = Repairer
    """
    dims = get_zone_dimensions(zone_id)
    if not dims:
        return []

    map_id = dims['map']

    query = """
    SELECT
        c.id as entry,
        ct.Name as name,
        ct.SubName as subname,
        ct.NpcFlags as npcflag,
        c.position_x,
        c.position_y,
        c.position_z
    FROM creature c
    JOIN creature_template ct ON c.id = ct.entry
    WHERE c.map = %s
      AND (ct.NpcFlags & 128 = 128 OR ct.NpcFlags & 4096 = 4096)
    """
    results = db.execute(query, (map_id,))

    vendors = []
    seen_ids = set()

    for row in results:
        # ОБЯЗАТЕЛЬНО конвертируем в float перед проверкой границ
        px = float(row['position_x'])
        py = float(row['position_y'])
        pz = float(row['position_z'])

        # Проверяем, попадает ли вендор ГЕОМЕТРИЧЕСКИ в нашу зону
        if is_coords_in_bounds(zone_id, px, py):

            flags = row['npcflag']
            is_vendor = (flags & 128) == 128
            is_repair = (flags & 4096) == 4096

            wrobot_type = "Vendor"
            if is_vendor and is_repair:
                wrobot_type = "VendorRepair"
            elif is_repair:
                wrobot_type = "Repair"

            if row['entry'] not in seen_ids:
                vendors.append({
                    'Id': row['entry'],
                    'Name': row['name'],
                    'Type': wrobot_type,
                    'X': px,
                    'Y': py,
                    'Z': pz
                })
                seen_ids.add(row['entry'])

    logger.info(f"Найдено {len(vendors)} торговцев/ремонтников в зоне {zone_id}")
    return vendors

def get_continent_flight_masters(db: Database, map_id: int) -> List[Dict[str, Any]]:
    """
    Находит всех Мастеров Полетов (Flight Masters) на всем КОНТИНЕНТЕ (MapID).
    NPC Flag 8192 (0x2000) = Flight Master.
    """
    query = """
    SELECT
        c.id as entry,
        ct.Name as name,
        c.position_x,
        c.position_y,
        c.position_z
    FROM creature c
    JOIN creature_template ct ON c.id = ct.entry
    WHERE c.map = %s
      AND (ct.NpcFlags & 8192 = 8192)
    """
    # Мы не фильтруем по координатам зоны, берем весь континент (map)
    results = db.execute(query, (map_id,))

    flight_masters = []
    seen_ids = set()

    for row in results:
        if row['entry'] not in seen_ids:
            flight_masters.append({
                'Id': row['entry'],
                'Name': row['name'],
                'Type': "FlightMaster", # Тип для WRobot
                'X': float(row['position_x']), # Конвертация в float обязательна
                'Y': float(row['position_y']),
                'Z': float(row['position_z'])
            })
            seen_ids.add(row['entry'])

    logger.info(f"Найдено {len(flight_masters)} мастеров полетов на карте {map_id}")
    return flight_masters