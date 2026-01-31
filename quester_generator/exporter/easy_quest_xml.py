# exporter/easy_quest_xml.py
import xml.etree.ElementTree as ET
from xml.dom import minidom
import math
from typing import List, Dict, Set

from core.db import Database
from core.logger import get_logger
from core.models import ProjectState, ZoneProject, Quest, Objective, GrindTask, CustomPath
from data_access.spawns_repo import get_creature_spawns, get_gameobject_spawns
from data_access.npc_repo import (
    get_quest_starter_npc, get_quest_ender_npc,
    get_quest_starter_go, get_quest_ender_go,
    get_zone_vendors, get_quest_starter_type,
    get_continent_flight_masters
)
from data_access.trainer_repo import get_class_trainers
from logic.clustering import cluster_spawns
from logic.loot_resolver import resolve_loot_to_kills, resolve_loot_to_gos
from logic.quest_sorter import sort_quests_with_dependencies

logger = get_logger(__name__)

XSI_URL = "http://www.w3.org/2001/XMLSchema-instance"
XSD_URL = "http://www.w3.org/2001/XMLSchema"

def pretty_print_xml(element: ET.Element) -> str:
    rough_string = ET.tostring(element, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent=" ")

def clean_name(text: str) -> str:
    if not text: return "Unknown"
    return "".join(c for c in text if c.isalnum())

def get_distance(x1, y1, x2, y2):
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

def is_gameobject(db: Database, entry: int) -> bool:
    query = "SELECT entry FROM gameobject_template WHERE entry = %s"
    return bool(db.execute(query, (entry,)))

def determine_quest_type(db: Database, quest: Quest, objectives: List[Objective]) -> str:
    if quest.special_flags & 2: return "Exploration"
    if not objectives: return "None"

    obj_types = set(o.type for o in objectives)
    has_kill = "kill" in obj_types
    has_loot = "loot" in obj_types

    loot_mob = False
    if has_loot:
        for o in objectives:
            if o.type == 'loot':
                if o.target_id and o.target_id > 0:
                    if not is_gameobject(db, o.target_id): loot_mob = True
                elif o.item_id:
                    if resolve_loot_to_kills(db, o.item_id): loot_mob = True

    if has_kill or loot_mob: return "KillAndLoot"
    if "gather" in obj_types: return "Gatherer"
    return "None"

def get_targets_for_objectives(db: Database, objs: List[Objective]):
    mobs, gos = [], []
    for o in objs:
        if o.type == 'kill' and o.target_id: mobs.append(o.target_id)
        elif o.type == 'gather' and o.target_id: gos.append(o.target_id)
        elif o.type == 'loot':
            if o.target_id and o.target_id > 0:
                if is_gameobject(db, o.target_id): gos.append(o.target_id)
                else: mobs.append(o.target_id)
            elif o.item_id:
                gos.extend(resolve_loot_to_gos(db, o.item_id))
                mobs.extend(resolve_loot_to_kills(db, o.item_id))
    return list(set(mobs)), list(set(gos))

def get_hotspots_for_targets(db: Database, quest_id: int, mobs: List[int], gos: List[int]):
    raw_spawns = []
    for tid in gos: raw_spawns.extend(get_gameobject_spawns(db, tid))
    for tid in mobs: raw_spawns.extend(get_creature_spawns(db, tid))

    valid_spawns = []
    starter_ref = get_quest_starter_npc(db, quest_id) or get_quest_starter_go(db, quest_id)
    if starter_ref and raw_spawns:
        sx, sy, smap = float(starter_ref['x']), float(starter_ref['y']), int(starter_ref['map'])
        for s in raw_spawns:
            if int(s['map']) == smap and get_distance(sx, sy, s['position_x'], s['position_y']) <= 2500:
                valid_spawns.append(s)
        if not valid_spawns: valid_spawns = raw_spawns
    else:
        valid_spawns = raw_spawns

    return cluster_spawns(valid_spawns) if valid_spawns else []

def add_quest_element(parent, quest, objs, quest_type, db):
    unique_name = f"{clean_name(quest.title)}{quest.entry}"
    eq = ET.SubElement(parent, "EasyQuest")
    ET.SubElement(eq, "Name").text = unique_name
    q_id = ET.SubElement(eq, "QuestId")
    ET.SubElement(q_id, "int").text = str(quest.entry)
    ET.SubElement(eq, "QuestType").text = quest_type

    effective_type = quest_type if quest_type != "None" else "KillAndLoot"
    qc = ET.SubElement(eq, "QuestClass", attrib={f"{{{XSI_URL}}}type": f"{effective_type}EasyQuestClass"})

    mobs, gos = get_targets_for_objectives(db, objs)
    if effective_type == "KillAndLoot":
        if mobs:
            et = ET.SubElement(qc, "EntryTarget")
            for m in mobs: ET.SubElement(et, "int").text = str(m)
        if gos:
            eo = ET.SubElement(qc, "EntryIdObjects")
            for g in gos: ET.SubElement(eo, "int").text = str(g)
        ET.SubElement(qc, "IsGrinderNotQuest").text = "false"
    elif effective_type == "Gatherer" and gos:
        eo = ET.SubElement(qc, "EntryIdObjects")
        for g in gos: ET.SubElement(eo, "int").text = str(g)

    hs_list = get_hotspots_for_targets(db, quest.entry, mobs, gos)
    hotspots_elem = ET.SubElement(qc, "HotSpots")
    for z in hs_list:
        ET.SubElement(hotspots_elem, "Vector3", X=str(z.center_x), Y=str(z.center_y), Z=str(z.center_z))
    ET.SubElement(qc, "IsHotspots").text = "true" if hs_list else "false"

    for i in range(1, 6):
        count = next((o.count for o in objs if o.slot == i), 0)
        ET.SubElement(eq, f"ObjectiveCount{i}").text = str(count)
        ET.SubElement(eq, f"AutoDetectObjectiveCount{i}").text = "true" if count > 0 else "false"

def add_grinder_element(parent, task: GrindTask):
    unique_name = f"Grind_{clean_name(task.mob_name)}_{task.mob_id}"
    eq = ET.SubElement(parent, "EasyQuest")
    ET.SubElement(eq, "Name").text = unique_name
    ET.SubElement(eq, "QuestId")
    ET.SubElement(eq, "QuestType").text = "KillAndLoot"

    qc = ET.SubElement(eq, "QuestClass", attrib={f"{{{XSI_URL}}}type": "KillAndLootEasyQuestClass"})
    et = ET.SubElement(qc, "EntryTarget")
    ET.SubElement(et, "int").text = str(task.mob_id)

    hs_elem = ET.SubElement(qc, "HotSpots")
    for h in task.hotspots:
        ET.SubElement(hs_elem, "Vector3", X=str(h.x), Y=str(h.y), Z=str(h.z))

    ET.SubElement(qc, "IsGrinderNotQuest").text = "true"
    ET.SubElement(qc, "IsHotspots").text = "true"

    # Condition: Stop at level
    cond = ET.SubElement(eq, "CanCondition")
    ET.SubElement(cond, "string").text = f"return ObjectManager.Me.Level < {task.stop_level};"

def generate_xml_from_project(project: ProjectState, filename: str, db: Database):
    ET.register_namespace('xsi', XSI_URL)
    ET.register_namespace('xsd', XSD_URL)
    root = ET.Element("EasyQuestProfile")

    quests_sorted = ET.SubElement(root, "QuestsSorted")
    npc_quest_section = ET.SubElement(root, "NpcQuest")
    npc_section = ET.SubElement(root, "Npc")
    easy_quests = ET.SubElement(root, "EasyQuests")

    seen_npcs = set()
    seen_vendors = set()
    processed_quests = {} # id -> Quest object

    for zone_proj in project.zones:
        # 1. Загружаем квесты зоны
        from data_access.quests_repo import get_quests_by_zone, get_objectives_for_quest
        all_zone_quests = get_quests_by_zone(db, zone_proj.zone_id)
        selected_quests = [q for q in all_zone_quests if q.entry in zone_proj.selected_quest_ids]
        selected_quests = sort_quests_with_dependencies(selected_quests)

        # 2. Обрабатываем квесты
        for q in selected_quests:
            if q.entry not in processed_quests:
                processed_quests[q.entry] = q
                objs = get_objectives_for_quest(db, q.entry)
                q_type = determine_quest_type(db, q, objs)
                add_quest_element(easy_quests, q, objs, q_type, db)

                # NPC Relation
                for func in [get_quest_starter_npc, get_quest_ender_npc, get_quest_starter_go, get_quest_ender_go]:
                    target = func(db, q.entry)
                    if target and target['entity_id'] not in seen_npcs:
                        is_go = "go" in func.__name__
                        npc_elem = ET.SubElement(npc_quest_section, "NPCQuest", Id=str(target['entity_id']), Name=target['entity_name'], GameObject="true" if is_go else "false")
                        ET.SubElement(npc_elem, "PickUpQuests")
                        ET.SubElement(npc_elem, "TurnInQuests")
                        ET.SubElement(npc_elem, "Position", X=str(target['x']), Y=str(target['y']), Z=str(target['z']), Type="None")
                        seen_npcs.add(target['entity_id'])

            # Add to QuestsSorted
            uname = f"{clean_name(q.title)}{q.entry}"
            ET.SubElement(quests_sorted, "QuestsSorted", Action="PickUp", NameClass=uname)
            ET.SubElement(quests_sorted, "QuestsSorted", Action="Pulse", NameClass=uname)
            ET.SubElement(quests_sorted, "QuestsSorted", Action="TurnIn", NameClass=uname)

        # 3. Добавляем гриндеров в QuestsSorted
        for gt in zone_proj.grind_tasks:
            add_grinder_element(easy_quests, gt)
            uname = f"Grind_{clean_name(gt.mob_name)}_{gt.mob_id}"
            ET.SubElement(quests_sorted, "QuestsSorted", Action="Pulse", NameClass=uname)

        # 4. Добавляем кастомные пути
        for cp in zone_proj.custom_paths:
            uname = f"Path_{clean_name(cp.name)}_{cp.x:.0f}_{cp.y:.0f}"
            ET.SubElement(quests_sorted, "QuestsSorted", Action="RunTo", NameClass=uname)

            # Добавляем фиктивный EasyQuest для RunTo
            eq = ET.SubElement(easy_quests, "EasyQuest")
            ET.SubElement(eq, "Name").text = uname
            ET.SubElement(eq, "QuestId")
            ET.SubElement(eq, "QuestType").text = "KillAndLoot"
            qc = ET.SubElement(eq, "QuestClass", attrib={f"{{{XSI_URL}}}type": "KillAndLootEasyQuestClass"})
            hs_elem = ET.SubElement(qc, "HotSpots")
            ET.SubElement(hs_elem, "Vector3", X=str(cp.x), Y=str(cp.y), Z=str(cp.z))
            ET.SubElement(qc, "IsGrinderNotQuest").text = "false"
            ET.SubElement(qc, "IsHotspots").text = "true"

        # 5. Вендоры и ФМ для зоны
        vendors = get_zone_vendors(db, zone_proj.zone_id)
        for v in vendors:
            if v['Id'] not in seen_vendors:
                npc_elem = ET.SubElement(npc_section, "Npc", Id=str(v['Id']), Name=v['Name'], Type=v['Type'])
                ET.SubElement(npc_elem, "Position", X=str(v['X']), Y=str(v['Y']), Z=str(v['Z']), Type="None")
                seen_vendors.add(v['Id'])

    # Глобальные ФМ и Тренеры (на основе первой зоны для континента)
    if project.zones:
        # Получаем MapID из первой зоны (упрощенно)
        from core.coord_converter import get_zone_dimensions
        dims = get_zone_dimensions(project.zones[0].zone_id)
        if dims:
            map_id = dims['map']
            fms = get_continent_flight_masters(db, map_id)
            for f in fms:
                if f['Id'] not in seen_vendors:
                    npc_elem = ET.SubElement(npc_section, "Npc", Id=str(f['Id']), Name=f['Name'], Type=f['Type'])
                    ET.SubElement(npc_elem, "Position", X=str(f['X']), Y=str(f['Y']), Z=str(f['Z']), Type="None")
                    seen_vendors.add(f['Id'])

            trainers = get_class_trainers(db, map_id)
            for t in trainers:
                if t['Id'] not in seen_vendors:
                    npc_elem = ET.SubElement(npc_section, "Npc", Id=str(t['Id']), Name=t['Name'], Type=t['Type'])
                    ET.SubElement(npc_elem, "Position", X=str(t['X']), Y=str(t['Y']), Z=str(t['Z']), Type="None")
                    seen_vendors.add(t['Id'])

    xml_str = pretty_print_xml(root).replace('<?xml version="1.0" ?>', '<?xml version="1.0" encoding="utf-16"?>')
    with open(filename, "w", encoding="utf-16") as f:
        f.write(xml_str)
    logger.info(f"Профиль успешно экспортирован в {filename}")

def generate_easy_quest_xml(quests, objectives, filename):
    """Оставлен для обратной совместимости, но теперь лучше использовать generate_xml_from_project"""
    db = Database()
    # Конвертируем старый формат в фиктивный ProjectState
    ps = ProjectState(zones=[ZoneProject(zone_id=quests[0].zone_or_sort, zone_name="Export", selected_quest_ids=[q.entry for q in quests])])
    generate_xml_from_project(ps, filename, db)
    db.close()
