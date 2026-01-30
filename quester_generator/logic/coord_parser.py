# logic/coord_parser.py
import re
from typing import List
from core.models import Vector3
from core.logger import get_logger

logger = get_logger(__name__)

def parse_coords(text: str) -> List[Vector3]:
    """
    Парсит координаты Vector3 из различных форматов WRobot.
    Поддерживает XML-вид и текстовый вид.
    """
    results = []

    # 1. Поиск XML формата: <Vector3 X="-9400.988" Y="-2036.693" Z="58.38026" ... />
    xml_pattern = r'X="([\-\d\.]+)"\s+Y="([\-\d\.]+)"\s+Z="([\-\d\.]+)"'
    for match in re.finditer(xml_pattern, text):
        results.append(Vector3(x=float(match.group(1)), y=float(match.group(2)), z=float(match.group(3))))

    if results:
        return results

    # 2. Поиск текстового формата: -9400.988, -2036.693, 58.38026
    # Или Vector3(-9400.988, -2036.693, 58.38026, "None")
    text_pattern = r'([\-\d\.]+),\s*([\-\d\.]+),\s*([\-\d\.]+)'
    for match in re.finditer(text_pattern, text):
        results.append(Vector3(x=float(match.group(1)), y=float(match.group(2)), z=float(match.group(3))))

    return results
