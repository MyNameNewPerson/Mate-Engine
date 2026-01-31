# logic/session_manager.py
import json
import os
from dataclasses import asdict
from core.models import ProjectState, ZoneProject, GrindTask, CustomPath, Vector3
from core.logger import get_logger

logger = get_logger(__name__)

SESSION_FILE = "project_session.json"

def save_project(state: ProjectState, filepath: str = SESSION_FILE):
    try:
        data = asdict(state)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"Проект успешно сохранен в {filepath}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении проекта: {e}")

def load_project(filepath: str = SESSION_FILE) -> ProjectState:
    if not os.path.exists(filepath):
        logger.info("Файл сессии не найден, создаем новый проект")
        return ProjectState()

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        zones = []
        for z_data in data.get("zones", []):
            grind_tasks = []
            for g_data in z_data.get("grind_tasks", []):
                hotspots = [Vector3(**h) for h in g_data.get("hotspots", [])]
                grind_tasks.append(GrindTask(
                    mob_id=g_data["mob_id"],
                    mob_name=g_data["mob_name"],
                    hotspots=hotspots,
                    stop_level=g_data["stop_level"],
                    zone_id=g_data["zone_id"]
                ))

            custom_paths = [CustomPath(**p) for p in z_data.get("custom_paths", [])]

            zones.append(ZoneProject(
                zone_id=z_data["zone_id"],
                zone_name=z_data["zone_name"],
                selected_quest_ids=z_data.get("selected_quest_ids", []),
                grind_tasks=grind_tasks,
                custom_paths=custom_paths
            ))

        return ProjectState(
            faction=data.get("faction", "alliance"),
            zones=zones
        )
    except Exception as e:
        logger.error(f"Ошибка при загрузке проекта: {e}")
        return ProjectState()
