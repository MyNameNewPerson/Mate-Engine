# tests/test_new_features.py
import unittest
import os
from logic.coord_parser import parse_coords
from logic.session_manager import save_project, load_project
from core.models import ProjectState, ZoneProject, GrindTask, Vector3

class TestNewFeatures(unittest.TestCase):
    def test_coord_parser(self):
        text = 'My Position Vector: new Vector3(-9400.988, -2036.693, 58.38026, "None")'
        coords = parse_coords(text)
        self.assertEqual(len(coords), 1)
        self.assertAlmostEqual(coords[0].x, -9400.988)

        xml_text = '<Vector3 X="-9400.988" Y="-2036.693" Z="58.38026" Type="None" />'
        coords_xml = parse_coords(xml_text)
        self.assertEqual(len(coords_xml), 1)
        self.assertAlmostEqual(coords_xml[0].y, -2036.693)

    def test_session_management(self):
        filename = "test_session.json"
        state = ProjectState(faction="horde", zones=[
            ZoneProject(zone_id=1, zone_name="Durotar", selected_quest_ids=[1, 2],
                        grind_tasks=[GrindTask(mob_id=123, mob_name="Boar", hotspots=[Vector3(1, 2, 3)], stop_level=10, zone_id=1)])
        ])

        save_project(state, filename)
        self.assertTrue(os.path.exists(filename))

        loaded = load_project(filename)
        self.assertEqual(loaded.faction, "horde")
        self.assertEqual(len(loaded.zones), 1)
        self.assertEqual(loaded.zones[0].zone_name, "Durotar")
        self.assertEqual(loaded.zones[0].grind_tasks[0].mob_id, 123)
        self.assertEqual(loaded.zones[0].grind_tasks[0].hotspots[0].x, 1)

        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    unittest.main()
