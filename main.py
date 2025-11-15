# main.py
import os
import csv
from datetime import datetime
from functools import partial

import pandas as pd

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ListProperty, StringProperty
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import OneLineListItem
from kivymd.uix.label import MDLabel
from kivymd.uix.pickers import MDDatePicker
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout as KVBox
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.dialog import MDDialog
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import ScrollView
from kivy.metrics import dp

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAPPINGS_CSV = os.path.join(BASE_DIR, "mappings.csv")
FAULT_TYPES_CSV = os.path.join(BASE_DIR, "fault_types.csv")
DAILY_LOG_CSV = os.path.join(BASE_DIR, "daily_log.csv")

# Load mapping CSV (expect the same columns you used previously)
m_df = pd.read_csv(MAPPINGS_CSV)
ft_df = pd.read_csv(FAULT_TYPES_CSV)

# Default Excel export location
if "ANDROID_ARGUMENT" in os.environ:
    DEFAULT_EXPORT = "/sdcard/Download/logbook_data.xlsx"
else:
    DEFAULT_EXPORT = os.path.join(BASE_DIR, "logbook_data.xlsx")

# Build nested mapping dicts for cascading dropdowns
mapping = {}
for _, r in m_df.iterrows():
    line = str(r['Line']).strip()
    area = str(r['Area']).strip()
    etype = str(r['Equipment Type']).strip()
    equip = str(r['Equipment']).strip()
    mapping.setdefault(line, {}).setdefault(area, {}).setdefault(etype, set()).add(equip)

# Convert sets to lists
for line in mapping:
    for area in mapping[line]:
        for etype in mapping[line][area]:
            mapping[line][area][etype] = sorted(list(mapping[line][area][etype]))

FAULT_TYPES = ft_df['Type of Fault'].dropna().astype(str).tolist()

# Ensure daily_log.csv exists with headers
if not os.path.exists(DAILY_LOG_CSV):
    with open(DAILY_LOG_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Time", "Date", "Line", "Area", "Equipment_Type", "Equipment", "Problem_Description",
            "Action_Type", "Action", "Type_of_Fault", "Job_Type", "EST", "LOTO_Applied"
        ])



class LogForm(MDBoxLayout):
    # lists used to populate menus dynamically
    lines = ListProperty(sorted(list(mapping.keys())))
    areas = ListProperty([])
    types = ListProperty([])
    equips = ListProperty([])
    fault_types = ListProperty(FAULT_TYPES)
    status = StringProperty("Ready")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # load existing daily log (safe even if only headers exist)
        self._preview_dialog = None  # store dialog reference
        try:
            self.saved_entries = pd.read_csv(DAILY_LOG_CSV).to_dict(orient="records")
        except Exception:
            self.saved_entries = []
        Clock.schedule_once(self._fill_datetime, 0.1)

        # holders for active menus (we create menus on demand)
        self._menus = {}

        # static options
        self._static_options = {
            "job_type": ["Breakdown Maint", "Preventive Maint", "Operational Maint"],
            "action_type": ["Reset/Adjustment", "Repair/Replacement"],
            "loto": ["Yes", "No"],
        }

        # prepare static menus
        Clock.schedule_once(lambda dt: self._prepare_static_menus(), 0.2)
    
    def _fill_datetime(self, dt=None):
        now = datetime.now()
        # default date/time values
        self.ids.date_input.text = now.strftime("%d/%m/%Y")  # day/month/year
        self.ids.time_input.text = now.strftime("%H:%M:%S")

    # -------------------------
    # Date picker
    # -------------------------
    def open_date_picker(self):
        date_dialog = MDDatePicker(year=datetime.now().year, month=datetime.now().month, day=datetime.now().day)
        date_dialog.bind(on_save=self._on_date_save)
        date_dialog.open()

    def _on_date_save(self, instance, value, range_range):
        # value is a datetime.date
        self.ids.date_input.text = value.isoformat()

    # -------------------------
    # MDDropdownMenu helpers (searchable)
    # -------------------------
    def _prepare_static_menus(self):
        # static menus: job_type, action_type, loto
        for key, options in self._static_options.items():
            field_id = f"{key}_field"
            self._create_menu(field_id, options, searchable=False)

        # create initial line menu (lines likely available) - searchable
        self._create_menu("line_field", self.lines, searchable=True)

        # create empty menus for dynamic fields (searchable where needed)
        self._create_menu("area_field", self.areas, searchable=True)
        self._create_menu("type_field", self.types, searchable=True)
        self._create_menu("equip_field", self.equips, searchable=True)
        self._create_menu("fault_type_field", self.fault_types, searchable=True)

    def _create_menu(self, field_id, options, searchable=False):
        old = self._menus.get(field_id)
        if old:
            try:
                old.dismiss()
            except Exception:
                pass
            self._menus[field_id] = None

        caller = self.ids.get(field_id, None)
        if not caller:
            return

        def make_items(opt_list):
            items = []
            for opt in opt_list:
                items.append({
                    "viewclass": "OneLineListItem",
                    "text": str(opt),
                    "height": dp(44),
                    "on_release": partial(self._on_menu_select, field_id, str(opt)),
                })
            return items

        items = make_items(options)

        menu = MDDropdownMenu(
            caller=caller,
            items=items,
            width_mult=4,
            max_height=dp(300),
        )

        self._menus[field_id] = menu
        menu.is_open_flag = False
        menu.bind(on_open=lambda *a: setattr(menu, "is_open_flag", True))
        menu.bind(on_dismiss=lambda *a: setattr(menu, "is_open_flag", False))

        if searchable:
            caller.readonly = False

            def on_text(instance, value):
                filtered = [o for o in options if value.lower() in str(o).lower()]
                menu.items = make_items(filtered)
                if filtered and not menu.is_open_flag:
                    try:
                        menu.open()
                    except Exception:
                        pass

            caller.bind(text=on_text)

    def _on_menu_select(self, field_id, selected_text, *args):
        """
        Called when a dropdown item is chosen.
        field_id is the mdtextfield id (e.g. 'line_field')
        """
        # set the text
        fld = self.ids.get(field_id)
        if fld:
            fld.text = selected_text

        # dismiss menu
        menu = self._menus.get(field_id)
        if menu:
            menu.dismiss()

        # trigger cascading updates where required
        if field_id == "line_field":
            # update areas list and menu
            self.on_line_changed(selected_text)
        elif field_id == "area_field":
            self.on_area_changed(selected_text)
        elif field_id == "type_field":
            self.on_type_changed(selected_text)
        # No extra action for equip_field selection

    # -------------------------
    # cascading handlers (logic preserved)
    # -------------------------
    def on_line_changed(self, value):
        if not value:
            self.areas = []
        else:
            self.areas = sorted(list(mapping.get(value, {}).keys()))
        # update area menu (rebuild)
        self.ids.area_field.text = "Select Area"
        self._create_menu("area_field", self.areas, searchable=True)

        # reset downstream
        self.types = []
        self.equips = []
        self.ids.type_field.text = "Select Type"
        self.ids.equip_field.text = "Select Equipment"
        self._create_menu("type_field", self.types, searchable=True)
        self._create_menu("equip_field", self.equips, searchable=True)

    def on_area_changed(self, value):
        line = self.ids.line_field.text
        if line in mapping and value in mapping[line]:
            self.types = sorted(list(mapping[line][value].keys()))
        else:
            self.types = []
        self.ids.type_field.text = "Select Type"
        self._create_menu("type_field", self.types, searchable=True)

        # reset equipment
        self.equips = []
        self.ids.equip_field.text = "Select Equipment"
        self._create_menu("equip_field", self.equips, searchable=True)

    def on_type_changed(self, value):
        line = self.ids.line_field.text
        area = self.ids.area_field.text
        if line in mapping and area in mapping[line] and value in mapping[line][area]:
            self.equips = mapping[line][area][value]
        else:
            self.equips = []
        self.ids.equip_field.text = "Select Equipment"
        self._create_menu("equip_field", self.equips, searchable=True)

    def validate_form(self):
        required_text_ids = [
            "fault_input",
            "action_input",
            "est_input"
        ]

        # 1️⃣ Check normal text fields
        for fid in required_text_ids:
            if fid in self.ids:
                if not self.ids[fid].text.strip():
                    return f"Please fill the '{fid.replace('_', ' ').title()}' field."

        # 2️⃣ Check dropdowns (MDTextField + MDDropdownMenu)
        for fid in [
            "line_field", "area_field", "type_field", "equip_field",
            "fault_type_field", "job_type_field", "loto_field", "action_type_field",
        ]:
            if fid in self.ids:
                text = self.ids[fid].text.strip()
                if not text or text.startswith("Select"):
                    return f"Please select a valid value for '{fid.replace('_', ' ').title()}'"

        return None


    # -------------------------
    # form actions
    # -------------------------
    def save_entry(self):
        rec = {
            "Time": self.ids.time_input.text,
            "Date": self.ids.date_input.text,
            "Line": self.ids.line_field.text,
            "Area": self.ids.area_field.text,
            "Equipment_Type": self.ids.type_field.text,
            "Equipment": self.ids.equip_field.text,
            "Problem_Description": self.ids.fault_input.text,
            "Action_Type": self.ids.action_type_field.text,
            "Action": self.ids.action_input.text,
            "Type_of_Fault": self.ids.fault_type_field.text,
            "Job_Type": self.ids.job_type_field.text,
            "EST": self.ids.est_input.text,
            "LOTO_Applied": self.ids.loto_field.text
        }
        error = self.validate_form()
        if error:
            MDDialog(
                text=error,
                size_hint=(0.5,0.3)
            ).open()
            return

        # Basic validation
        if rec['Line'] in ("", "Select Line") or rec['Area'] in ("", "Select Area"):
            self.status = "Please select Line and Area"
            return

        self.saved_entries.append(rec)

        # Append to CSV
        with open(DAILY_LOG_CSV, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rec.keys())
            writer.writerow(rec)

        self.status = f"Saved locally ({len(self.saved_entries)} rows)"
        # update date/time
        self._fill_datetime()
        # clear form fields
        self.clear_form()

    def clear_form(self):
        # Clear text input fields
        clear_ids = [
            "fault_input", "action_input", "est_input"
        ]
        for fid in clear_ids:
            if fid in self.ids:
                self.ids[fid].text = ""

        # Reset dropdown placeholders
        placeholders = {
            "line_field": "Select Line",
            "area_field": "Select Area",
            "type_field": "Select Type",
            "equip_field": "Select Equipment",
            "fault_type_field": "Select Fault Type",
            "job_type_field": "Select Job Type",
            "loto_field": "Select LOTO",
            "action_type_field": "Select Action Type",
        }

        for fid, placeholder in placeholders.items():
            if fid in self.ids:
                self.ids[fid].text = placeholder

                # Dynamic dropdowns – rebuild using live lists
                if fid == "area_field":
                    self._create_menu(fid, self.areas, searchable=True)
                elif fid == "type_field":
                    self._create_menu(fid, self.types, searchable=True)
                elif fid == "equip_field":
                    self._create_menu(fid, self.equips, searchable=True)
                elif fid == "fault_type_field":
                    self._create_menu(fid, self.fault_types, searchable=True)

                # Static dropdowns — always rebuild using static options
                elif fid == "job_type_field":
                    self._create_menu(fid, self._static_options["job_type"], searchable=False)
                elif fid == "loto_field":
                    self._create_menu(fid, self._static_options["loto"], searchable=False)
                elif fid == "action_type_field":
                    self._create_menu(fid, self._static_options["action_type"], searchable=False)



    # from kivymd.uix.datatables import MDDataTable
    # from kivy.metrics import dp
    # from kivymd.uix.dialog import MDDialog

    def preview(self):
        if not self.saved_entries:
            self.status = "No entries to preview"
            return

        df = pd.DataFrame(self.saved_entries)
        if df.empty:
            MDDialog(text="No entries to preview", size_hint=(0.7, 0.3)).open()
            return

        # Close previous dialog if exists
        if self._preview_dialog:
            try:
                self._preview_dialog.dismiss()
            except Exception:
                pass
            self._preview_dialog = None

        column_data = [(col.replace("_", " "), dp(30)) for col in df.columns]
        row_data = [tuple(str(v) for v in row.values()) for row in self.saved_entries]

        table = MDDataTable(
            size_hint=(1, None),
            height=dp(600),
            column_data=column_data,
            row_data=row_data,
            check=False,
            use_pagination=False,  # important
        )

        # Directly pass table as content_cls
        self._preview_dialog = MDDialog(
            title=f"Preview ({len(df)} rows)",
            type="custom",
            content_cls=table,
            size_hint=(0.95, 0.95),
        )
        self._preview_dialog.open()

    def export_xlsx(self, path=None):
        if not self.saved_entries:
            self.status = "No entries to export"
            return
        if path is None:
            path = DEFAULT_EXPORT
        df = pd.DataFrame(self.saved_entries)
        df.to_excel(path, index=False)
        self.status = f"Exported {len(df)} rows → {path}"

        # Reset CSV with headers only
        with open(DAILY_LOG_CSV, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(df.columns)

        # Clear memory
        self.saved_entries = []

    def clear_saved(self):
        self.saved_entries = []
        with open(DAILY_LOG_CSV, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Time", "Date", "Line", "Area", "Equipment_Type", "Equipment", "Problem_Description",
                "Action_Type", "Action", "Type_of_Fault", "Job_Type", "EST", "LOTO_Applied"
            ])

        self.status = "Cleared local entries"

    # Small helper to toggle app theme (Light <-> Dark)
    def toggle_theme(self):
        app = MDApp.get_running_app()
        app.theme_cls.theme_style = "Light" if app.theme_cls.theme_style == "Dark" else "Dark"
        # force refresh menus (optional)
        for k in list(self._menus.keys()):
            if self._menus[k]:
                try:
                    self._menus[k].dismiss()
                except Exception:
                    pass
                self._menus[k] = None
        # rebuild menus to pick up any theme/background dims
        Clock.schedule_once(lambda dt: self._prepare_static_menus(), 0.05)


# Load KV
KV = Builder.load_file(os.path.join(BASE_DIR, "logform3.kv"))


class LogApp(MDApp):
    def build(self):
        # default to Light so user isn't surprised by too dark UI,
        # but you can toggle in the app with the toolbar button.
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.accent_palette = "Amber"
        return LogForm()


if __name__ == "__main__":
    LogApp().run()
