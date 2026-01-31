# ui/app.py
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from core.db import Database
from core.logger import get_logger
from data_access.zones_repo import search_zones_by_name, get_zone_name, ZONE_NAMES
from ui.zone_tab import ZoneTab
from logic.session_manager import load_project, save_project
from core.models import ProjectState, ZoneProject

logger = get_logger(__name__)

class QuesterApp(ttkb.Window):
    def __init__(self):
        super().__init__(themename="superhero")
        self.title("Quester Profile Generator — CMaNGOS TBC 2.4.3")
        self.geometry("1400x900")
        self.minsize(1000, 700)

        self.db = Database()
        self.project = load_project()

        self.faction_var = tk.StringVar(value=self.project.faction)
        self.faction_var.trace_add("write", self.on_faction_change)

        self.tabs = {} # zone_id -> ZoneTab

        self.create_widgets()
        self.restore_project()

    def create_widgets(self):
        # Header
        header = ttkb.Frame(self, padding=10, bootstyle=PRIMARY)
        header.pack(fill=tk.X)
        ttkb.Label(header, text="WRobot Quester Generator", font=("Segoe UI Bold", 18), bootstyle=LIGHT).pack(side=tk.LEFT, padx=10)

        # Toolbar
        toolbar = ttkb.Frame(self, padding=5)
        toolbar.pack(fill=tk.X)

        ttkb.Label(toolbar, text="Добавить зону:").pack(side=tk.LEFT, padx=5)
        self.zone_combo = ttkb.Combobox(toolbar, width=35)
        self.zone_combo['values'] = list(ZONE_NAMES.values())
        self.zone_combo.pack(side=tk.LEFT, padx=5)
        self.zone_combo.bind("<KeyRelease>", self.on_zone_search)

        ttkb.Button(toolbar, text="➕", bootstyle=SUCCESS, command=self.add_zone_tab, width=3).pack(side=tk.LEFT, padx=5)

        # Faction
        ttkb.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttkb.Radiobutton(toolbar, text="Альянс", variable=self.faction_var, value="alliance", bootstyle=INFO).pack(side=tk.LEFT, padx=5)
        ttkb.Radiobutton(toolbar, text="Орда", variable=self.faction_var, value="horde", bootstyle=DANGER).pack(side=tk.LEFT, padx=5)

        # Actions
        ttkb.Button(toolbar, text="💾 Сохранить проект", bootstyle=SECONDARY, command=self.save_project_cmd).pack(side=tk.RIGHT, padx=5)
        ttkb.Button(toolbar, text="🚀 Сгенерировать XML", bootstyle=PRIMARY, command=self.generate_xml).pack(side=tk.RIGHT, padx=5)

        # Notebook (Tabs)
        self.notebook = ttkb.Notebook(self, bootstyle=INFO)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Status Bar
        self.status = ttkb.Label(self, text="Готово", bootstyle=SECONDARY, anchor=tk.W, padding=5)
        self.status.pack(fill=tk.X)

    def on_zone_search(self, event):
        query = self.zone_combo.get().lower()
        matching = [v for k, v in ZONE_NAMES.items() if query in v.lower()]
        self.zone_combo['values'] = matching

    def add_zone_tab(self, zone_id=None, project_data=None):
        if zone_id is None:
            zone_name = self.zone_combo.get()
            zone_id = self.get_zone_id_by_name(zone_name)
            if not zone_id:
                messagebox.showerror("Ошибка", "Зона не найдена")
                return
        else:
            zone_name = ZONE_NAMES.get(zone_id, f"Zone {zone_id}")

        if zone_id in self.tabs:
            self.notebook.select(self.tabs[zone_id])
            return

        tab = ZoneTab(self.notebook, self.db, zone_id, zone_name, self.faction_var, project_data)
        self.notebook.add(tab, text=zone_name)
        self.tabs[zone_id] = tab
        self.notebook.select(tab)

        if project_data is None:
            self.project.zones.append(tab.project_data)

    def get_zone_id_by_name(self, name):
        for zid, zname in ZONE_NAMES.items():
            if name.lower() == zname.lower(): return zid
        return None

    def restore_project(self):
        for zp in self.project.zones:
            self.add_zone_tab(zp.zone_id, zp)

    def on_faction_change(self, *args):
        self.project.faction = self.faction_var.get()
        # Мы не перезагружаем все вкладки сразу, чтобы не тормозить,
        # но текущую вкладку стоит обновить.
        current_tab = self.notebook.select()
        if current_tab:
            tab_obj = self.notebook.nametowidget(current_tab)
            if isinstance(tab_obj, ZoneTab):
                tab_obj.load_quests()

    def save_project_cmd(self):
        save_project(self.project)
        self.status.config(text="Проект сохранен")

    def generate_xml(self):
        if not self.project.zones:
            messagebox.showwarning("Внимание", "Нет зон в проекте")
            return

        filename = "GlobalProfile.xml"
        try:
            from exporter.easy_quest_xml import generate_xml_from_project
            generate_xml_from_project(self.project, filename, self.db)
            messagebox.showinfo("Успех", f"Профиль сохранен в {filename}")
        except Exception as e:
            logger.error(f"Export failed: {e}")
            messagebox.showerror("Ошибка", f"Не удалось экспортировать XML: {e}")

    def destroy(self):
        save_project(self.project)
        self.db.close()
        super().destroy()

if __name__ == "__main__":
    app = QuesterApp()
    app.mainloop()
