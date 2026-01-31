import sys
import os
from unittest.mock import MagicMock

# Add current directory to path so we can import core and data_access
sys.path.append(os.getcwd())

# Mock the database connection to avoid YAML loading and mysql connection
import yaml
import mysql.connector
sys.modules['mysql.connector'] = MagicMock()

from data_access.quests_repo import get_objectives_for_quest
from core.models import Objective

def test_objectives():
    mock_db = MagicMock()

    # Test case 1: Mixed objectives
    # Slot 1: Kill (positive ID)
    # Slot 2: Gather (negative ID)
    # Slot 3: Loot (Item ID)
    # Slot 4: Empty
    mock_db.execute.return_value = [{
        'quest_id': 100,
        'ReqCreatureOrGOId1': 123, 'ReqCreatureOrGOCount1': 10,
        'ReqCreatureOrGOId2': -456, 'ReqCreatureOrGOCount2': 5,
        'ReqItemId3': 789, 'ReqItemCount3': 1,
        'ReqCreatureOrGOId4': 0, 'ReqItemId4': 0,
        'ReqItemId1': 0, 'ReqItemCount1': 0,
        'ReqItemId2': 0, 'ReqItemCount2': 0,
        'ReqCreatureOrGOId3': 0, 'ReqCreatureOrGOCount3': 0,
        'ReqItemCount4': 0, 'ReqCreatureOrGOCount4': 0
    }]

    print("Running test_objectives...")
    objs = get_objectives_for_quest(mock_db, 100)

    assert len(objs) == 3, f"Expected 3 objectives, got {len(objs)}"

    # Slot 1: Kill
    assert objs[0].slot == 1
    assert objs[0].type == 'kill'
    assert objs[0].target_id == 123
    assert objs[0].count == 10

    # Slot 2: Gather
    assert objs[1].slot == 2
    assert objs[1].type == 'gather'
    assert objs[1].target_id == 456
    assert objs[1].count == 5

    # Slot 3: Loot
    assert objs[2].slot == 3
    assert objs[2].type == 'loot'
    assert objs[2].item_id == 789
    assert objs[2].count == 1

    print("Test case 1 passed!")

    # Test case 4: Loot with source target_id
    mock_db.execute.return_value = [{
        'quest_id': 103,
        'ReqItemId1': 555, 'ReqItemCount1': 5,
        'ReqCreatureOrGOId1': -777, # Loot from GO
    }]
    objs = get_objectives_for_quest(mock_db, 103)
    assert len(objs) == 1
    assert objs[0].type == 'loot'
    assert objs[0].item_id == 555
    assert objs[0].target_id == 777
    print("Test case 4 passed!")

    print("ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    try:
        test_objectives()
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
