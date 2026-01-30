# WRobot Quester Generator for TBC 2.4.3

This tool generates WRobot Quester XML profiles from CMaNGOS database data.

## Changes in this version:
- Removed custom C# scripts from `IsCompleteCondition` to fix compilation errors (`wManager.wow` missing).
- Stopped splitting quests into multiple steps to simplify the profile and ensure compatibility with older WRobot versions.
- Ensured a valid `QuestClass` is always provided to avoid "Cannot find QuestClass" errors.
- Fixed `QuestId` handling in generated XML.

## Installation
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure database in `config/db.yaml`.

## Usage
Run `python main.py` to start the GUI.
