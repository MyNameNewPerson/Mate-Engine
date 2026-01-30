# ui/zone_tab.py
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from typing import List, Dict, Any, Optional
from core.models import ZoneProject, Quest, GrindTask, CustomPath, Vector3
from data_access.quests_repo import get_quests_by_zone, get_objectives_for_quest
from data_access.npc_repo import get_quest_starter_type
from logic.coord_parser import parse_coords
from logic.faction_filter import get_faction_mask, filter_quests_by_faction
from logic.quest_chains import build_quest_chains
from core.logger import get_logger

logger = get_logger(__name__)

class ZoneTab(ttkb.Frame):
    def __init__(self, master, db, zone_id, zone_name, faction_var, project_data: Optional[ZoneProject] = None):
        super().__init__(master, padding=10)
        self.db = db
        self.zone_id = zone_id
        self.zone_name = zone_name
        self.faction_var = faction_var
        self.quests = []
        self.objectives = {}
        self.check_vars = {}

        self.project_data = project_data or ZoneProject(zone_id=zone_id, zone_name=zone_name)

        self.create_widgets()
        self.load_quests()

    def create_widgets(self):
        # Панель управления вкладкой
        ctrl_frame = ttkb.Frame(self, padding=5)
        ctrl_frame.pack(fill=tk.X)

        ttkb.Label(ctrl_frame, text=f"Зона: {self.zone_name} (ID: {self.zone_id})", font=("Segoe UI Bold", 12)).pack(side=tk.LEFT)
        ttkb.Button(ctrl_frame, text="Обновить", bootstyle=INFO, command=self.load_quests, width=10).pack(side=tk.RIGHT, padx=5)

        # Основной контент: Квесты слева, Гринд/Пути справа
        paned = ttkb.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=10)

        # Левая часть: Дерево квестов
        quest_frame = ttkb.Frame(paned)
        paned.add(quest_frame, weight=3)

        tree_scroll = ttkb.Scrollbar(quest_frame, bootstyle=PRIMARY)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(quest_frame, columns=("Check", "ID", "Level", "Type"), show="tree headings", yscrollcommand=tree_scroll.set)
        self.tree.column("#0", width=400, anchor=tk.W)
        self.tree.heading("#0", text="Название квеста")
        self.tree.heading("Check", text="✓")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Level", text="Ур.")
        self.tree.heading("Type", text="Тип")

        self.tree.column("Check", width=40, anchor=tk.CENTER)
        self.tree.column("ID", width=60, anchor=tk.CENTER)
        self.tree.column("Level", width=40, anchor=tk.CENTER)
        self.tree.column("Type", width=120, anchor=tk.CENTER)

        self.tree.tag_configure("chain", foreground="#0dcaf0", font=("Segoe UI Bold", 10))
        self.tree.pack(fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)

        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<Button-3>", self.on_right_click)

        # Правая часть: Гринд и Пути
        right_panel = ttkb.Frame(paned, padding=(10, 0, 0, 0))
        paned.add(right_panel, weight=1)

        # Секция Гринда
        ttkb.Label(right_panel, text="Гринд / Фарм", font=("Segoe UI Bold", 11)).pack(anchor=tk.W)
        self.grind_list = tk.Listbox(right_panel, height=8, font=("Segoe UI", 10))
        self.grind_list.pack(fill=tk.X, pady=5)

        grind_btns = ttkb.Frame(right_panel)
        grind_btns.pack(fill=tk.X)
        ttkb.Button(grind_btns, text="Добавить", bootstyle=SUCCESS, command=self.add_grind, width=10).pack(side=tk.LEFT, padx=2)
        ttkb.Button(grind_btns, text="Удалить", bootstyle=DANGER, command=self.remove_grind, width=10).pack(side=tk.LEFT, padx=2)

        # Секция Путей
        ttkb.Label(right_panel, text="Точки маршрута (RunTo)", font=("Segoe UI Bold", 11)).pack(anchor=tk.W, pady=(15, 0))
        self.path_list = tk.Listbox(right_panel, height=8, font=("Segoe UI", 10))
        self.path_list.pack(fill=tk.X, pady=5)

        path_btns = ttkb.Frame(right_panel)
        path_btns.pack(fill=tk.X)
        ttkb.Button(path_btns, text="Добавить", bootstyle=SUCCESS, command=self.add_path, width=10).pack(side=tk.LEFT, padx=2)
        ttkb.Button(path_btns, text="Удалить", bootstyle=DANGER, command=self.remove_path, width=10).pack(side=tk.LEFT, padx=2)

    def load_quests(self):
        faction = self.faction_var.get()
        mask = get_faction_mask(faction)

        try:
            raw_quests = get_quests_by_zone(self.db, self.zone_id)
            valid_quests = filter_quests_by_faction(raw_quests, mask)

            # Фильтрация по типу стартера
            final_quests = []
            for q in valid_quests:
                if get_quest_starter_type(self.db, q.entry) != 'item':
                    final_quests.append(q)

            self.quests = final_quests
            self.objectives.clear()
            for q in final_quests:
                self.objectives[q.entry] = get_objectives_for_quest(self.db, q.entry)

            chains = build_quest_chains(final_quests)

            self.tree.delete(*self.tree.get_children())
            self.check_vars.clear()

            for chain in chains:
                if len(chain) == 1:
                    self.add_quest_node("", chain[0])
                else:
                    node = self.tree.insert("", "end", text=f"{chain[0].title} (Цепочка)", values=("☐", "", "", ""), tags=("chain",))
                    self.check_vars[node] = tk.BooleanVar(value=False)
                    for q in chain:
                        self.add_quest_node(node, q)

            # Восстанавливаем выделение из проекта
            self.restore_selection()

        except Exception as e:
            logger.error(f"Error loading quests for zone {self.zone_id}: {e}")

    def add_quest_node(self, parent, q):
        objs = self.objectives.get(q.entry, [])
        type_str = ", ".join(set(o.type for o in objs)) if objs else "Talk"
        node = self.tree.insert(parent, "end", text=q.title, values=("☐", q.entry, q.quest_level, type_str))
        self.check_vars[node] = tk.BooleanVar(value=False)

    def on_tree_click(self, event):
        item = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if item and col == "#1":
            var = self.check_vars[item]
            new_val = not var.get()
            var.set(new_val)
            self.tree.set(item, "Check", "☑" if new_val else "☐")

            if self.tree.tag_has("chain", item):
                for child in self.tree.get_children(item):
                    self.check_vars[child].set(new_val)
                    self.tree.set(child, "Check", "☑" if new_val else "☐")

            self.update_project_selection()

    def update_project_selection(self):
        selected_ids = []
        for item, var in self.check_vars.items():
            if var.get():
                val = self.tree.item(item, "values")
                if val and val[1]:
                    selected_ids.append(int(val[1]))
        self.project_data.selected_quest_ids = list(set(selected_ids))

    def restore_selection(self):
        for item, var in self.check_vars.items():
            val = self.tree.item(item, "values")
            if val and val[1] and int(val[1]) in self.project_data.selected_quest_ids:
                var.set(True)
                self.tree.set(item, "Check", "☑")

    def on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item: return

        self.tree.selection_set(item)
        val = self.tree.item(item, "values")
        if not val or not val[1]: return

        q_id = int(val[1])
        quest = next((q for q in self.quests if q.entry == q_id), None)
        if not quest: return

        # Показываем окно с деталями
        detail_win = ttkb.Toplevel(self)
        detail_win.title(f"Детали квеста: {quest.title}")
        detail_win.geometry("600x400")

        txt = tk.Text(detail_win, wrap=tk.WORD, font=("Segoe UI", 10), padx=10, pady=10)
        txt.pack(fill=tk.BOTH, expand=True)

        content = f"ID: {quest.entry}\n"
        content += f"Уровень: {quest.quest_level} (Мин: {quest.min_level})\n"
        content += f"----------------------------------\n\n"
        content += f"ОПИСАНИЕ:\n{quest.details}\n\n"
        content += f"ЦЕЛИ:\n"
        objs = self.objectives.get(quest.entry, [])
        for o in objs:
            content += f"- {o.type.capitalize()}: {o.target_id or o.item_id} (x{o.count})\n"

        txt.insert(tk.END, content)
        txt.config(state=tk.DISABLED)

    def add_grind(self):
        dialog = ttkb.Toplevel(self)
        dialog.title("Добавить задачу на гринд")
        dialog.geometry("500x500")

        ttkb.Label(dialog, text="ID моба:").pack(pady=5)
        mob_id_entry = ttkb.Entry(dialog)
        mob_id_entry.pack(fill=tk.X, padx=20)

        ttkb.Label(dialog, text="Название:").pack(pady=5)
        name_entry = ttkb.Entry(dialog)
        name_entry.pack(fill=tk.X, padx=20)

        ttkb.Label(dialog, text="До уровня:").pack(pady=5)
        lvl_entry = ttkb.Entry(dialog)
        lvl_entry.insert(0, "60")
        lvl_entry.pack(fill=tk.X, padx=20)

        ttkb.Label(dialog, text="Координаты (вставьте Vector3 или список):").pack(pady=5)
        coords_txt = tk.Text(dialog, height=10)
        coords_txt.pack(fill=tk.BOTH, expand=True, padx=20)

        def save():
            try:
                mid = int(mob_id_entry.get())
                mname = name_entry.get() or f"Mob {mid}"
                stop_lvl = int(lvl_entry.get())
                raw_coords = coords_txt.get("1.0", tk.END)
                hotspots = parse_coords(raw_coords)

                if not hotspots:
                    messagebox.showerror("Ошибка", "Координаты не распознаны!")
                    return

                task = GrindTask(mob_id=mid, mob_name=mname, hotspots=hotspots, stop_level=stop_lvl, zone_id=self.zone_id)
                self.project_data.grind_tasks.append(task)
                self.refresh_grind_list()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Ошибка", "ID и уровень должны быть числами")

        ttkb.Button(dialog, text="Сохранить", bootstyle=SUCCESS, command=save).pack(pady=10)

    def remove_grind(self):
        idx = self.grind_list.curselection()
        if idx:
            self.project_data.grind_tasks.pop(idx[0])
            self.refresh_grind_list()

    def refresh_grind_list(self):
        self.grind_list.delete(0, tk.END)
        for g in self.project_data.grind_tasks:
            self.grind_list.insert(tk.END, f"{g.mob_name} (до {g.stop_level} ур.)")

    def add_path(self):
        dialog = ttkb.Toplevel(self)
        dialog.title("Добавить точку перемещения (RunTo)")
        dialog.geometry("400x300")

        ttkb.Label(dialog, text="Название (например, To Flight Master):").pack(pady=5)
        name_entry = ttkb.Entry(dialog)
        name_entry.pack(fill=tk.X, padx=20)

        ttkb.Label(dialog, text="Координаты (Vector3):").pack(pady=5)
        coord_entry = ttkb.Entry(dialog)
        coord_entry.pack(fill=tk.X, padx=20)

        def save():
            raw = coord_entry.get()
            coords = parse_coords(raw)
            if not coords:
                messagebox.showerror("Ошибка", "Координаты не распознаны")
                return

            p = coords[0]
            path = CustomPath(name=name_entry.get() or "RunTo", x=p.x, y=p.y, z=p.z)
            self.project_data.custom_paths.append(path)
            self.refresh_path_list()
            dialog.destroy()

        ttkb.Button(dialog, text="Сохранить", bootstyle=SUCCESS, command=save).pack(pady=20)

    def remove_path(self):
        idx = self.path_list.curselection()
        if idx:
            self.project_data.custom_paths.pop(idx[0])
            self.refresh_path_list()

    def refresh_path_list(self):
        self.path_list.delete(0, tk.END)
        for p in self.project_data.custom_paths:
            self.path_list.insert(tk.END, f"{p.name} [{p.x:.1f}, {p.y:.1f}]")
