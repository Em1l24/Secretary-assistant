import customtkinter as ctk
from tkinter import filedialog, messagebox, Toplevel, Menu
import os
import sys
from datetime import datetime
from core.database import Database
from core.generator import DocumentGenerator


class DesignConfig:
    """Конфигурация дизайна приложения"""
    PRIMARY = "#2563eb"
    PRIMARY_HOVER = "#1d4ed8"
    SUCCESS = "#059669"
    DANGER = "#dc2626"
    WARNING = "#d97706"
    
    BACKGROUND = "#f8fafc"
    CARD_BG = "#ffffff"
    CARD_HOVER = "#f1f5f9"
    
    TEXT_PRIMARY = "#1e293b"
    TEXT_SECONDARY = "#64748b"
    TEXT_MUTED = "#94a3b8"
    
    CORNER_RADIUS = 12
    BUTTON_HEIGHT = 45
    ENTRY_HEIGHT = 40
    PADDING = 16
    
    FONT_FAMILY = "Segoe UI"
    FONT_TITLE = 24
    FONT_SUBTITLE = 20
    FONT_BODY = 16
    FONT_SMALL = 11


class CTkEntryWithMenu(ctk.CTkEntry):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('corner_radius', DesignConfig.CORNER_RADIUS)
        kwargs.setdefault('height', DesignConfig.ENTRY_HEIGHT)
        kwargs.setdefault('font', ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=DesignConfig.FONT_BODY))
        super().__init__(*args, **kwargs)
        self.bind("<Button-3>", self._show_menu)
        self.bind("<Control-c>", lambda e: self._copy_event())
        self.bind("<Control-v>", lambda e: self._paste_event())
        self.bind("<Control-x>", lambda e: self._cut_event())
        self.bind("<Control-a>", lambda e: self._select_all_event())
    
    def _show_menu(self, event):
        menu = Menu(self, tearoff=0)
        menu.add_command(label="📋 Копировать", command=self._copy_event)
        menu.add_command(label="📥 Вставить", command=self._paste_event)
        try: menu.tk_popup(event.x_root, event.y_root)
        finally: menu = None
    
    def _copy_event(self):
        try: selection = self.selection_get(); self.clipboard_clear(); self.clipboard_append(selection)
        except: pass
    
    def _paste_event(self):
        try: text = self.clipboard_get(); self.insert(self.index("insert"), text)
        except: pass
    
    def _cut_event(self):
        try: selection = self.selection_get(); self.clipboard_clear(); self.clipboard_append(selection); self.delete("sel.first", "sel.last")
        except: pass
    
    def _select_all_event(self):
        self.select_range(0, 'end'); self.icursor('end')


class CTkTextboxWithMenu(ctk.CTkTextbox):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('corner_radius', DesignConfig.CORNER_RADIUS)
        kwargs.setdefault('font', ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=DesignConfig.FONT_BODY))
        super().__init__(*args, **kwargs)
        self.bind("<Button-3>", self._show_menu)
        self.bind("<Control-c>", lambda e: self._copy_event())
        self.bind("<Control-v>", lambda e: self._paste_event())
        self.bind("<Control-x>", lambda e: self._cut_event())
        self.bind("<Control-a>", lambda e: self._select_all_event())
    
    def _show_menu(self, event):
        menu = Menu(self, tearoff=0)
        menu.add_command(label="📋 Копировать", command=self._copy_event)
        menu.add_command(label="📥 Вставить", command=self._paste_event)
        try: menu.tk_popup(event.x_root, event.y_root)
        finally: menu = None
    
    def _copy_event(self):
        try: selection = self.get("sel.first", "sel.last"); self.clipboard_clear(); self.clipboard_append(selection)
        except: pass
    
    def _paste_event(self):
        try: text = self.clipboard_get(); self.insert("insert", text)
        except: pass
    
    def _cut_event(self):
        try: selection = self.get("sel.first", "sel.last"); self.clipboard_clear(); self.clipboard_append(selection); self.delete("sel.first", "sel.last")
        except: pass
    
    def _select_all_event(self):
        self.tag_add("sel", "1.0", "end")


class ModernCard(ctk.CTkFrame):
    def __init__(self, parent, title=None, **kwargs):
        kwargs.setdefault('corner_radius', DesignConfig.CORNER_RADIUS)
        kwargs.setdefault('fg_color', DesignConfig.CARD_BG)
        super().__init__(parent, **kwargs)
        if title:
            title_label = ctk.CTkLabel(
                self, text=title,
                font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=DesignConfig.FONT_SUBTITLE, weight="bold"),
                text_color=DesignConfig.TEXT_PRIMARY
            )
            title_label.pack(pady=(DesignConfig.PADDING, DesignConfig.PADDING//2), padx=DesignConfig.PADDING, anchor="w")


class ModernButton(ctk.CTkButton):
    def __init__(self, parent, text="", command=None, icon=None, color=None, **kwargs):
        kwargs.setdefault('corner_radius', DesignConfig.CORNER_RADIUS)
        kwargs.setdefault('height', DesignConfig.BUTTON_HEIGHT)
        kwargs.setdefault('font', ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=DesignConfig.FONT_BODY, weight="bold"))
        kwargs.setdefault('fg_color', color or DesignConfig.PRIMARY)
        kwargs.setdefault('hover_color', DesignConfig.PRIMARY_HOVER)
        kwargs.setdefault('text_color', "#ffffff")
        super().__init__(parent, text=text, command=command, **kwargs)


class VKRStudentDialog(Toplevel):
    def __init__(self, parent, callback, student_data=None):
        super().__init__(parent)
        self.callback = callback
        self.student_data = student_data
        self.is_edit = student_data is not None
        title = "✏️ Редактировать студента ВКР" if self.is_edit else "➕ Добавить студента ВКР"
        self.title(title)
        self.geometry("900x800")
        self.minsize(800, 700)
        self.resizable(True, True)
        self.grab_set()
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 900) // 2
        y = (self.winfo_screenheight() - 800) // 2
        self.geometry(f"900x800+{x}+{y}")
        ctk.set_appearance_mode("light")
        self._create_widgets()
        if self.is_edit and student_data:
            self._fill_data(student_data)
    
    def _create_widgets(self):
        main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=24, pady=24)
        header = ctk.CTkFrame(main_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="Данные студента для защиты ВКР", font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=DesignConfig.FONT_TITLE, weight="bold"), text_color=DesignConfig.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(header, text="Заполните сначала ФИО. Остальные поля можно заполнить позже.", font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=DesignConfig.FONT_BODY), text_color=DesignConfig.TEXT_SECONDARY).pack(anchor="w", pady=(4, 0))
        
        self.fields = {}
        field_config = [
            ("ФИО студента *", "fio", 1), ("Протокол №", "protocol", 2),
            ("Направление подготовки", "direction", 3), ("Тема дипломной работы", "theme", 4),
            ("Научный руководитель", "leader", 5), ("Дата защиты", "date", 6),
            ("Состав ГЭК утвержден приказом от", "dategek", 7), ("Должность руководителя", "post", 8),
            ("При консультации", "con", 9), ("Допущен до защиты приказом от", "order", 10),
            ("Кол-во страниц", "pages", 11), ("Чертежи", "con_1", 12),
            ("Иллюстрационный материал", "con_2", 13), ("Отзыв руководителя", "review", 14),
            ("Время сообщения (мин)", "time", 15), ("Заданные вопросы", "questions", 16),
            ("Характеристика ответов", "property", 17), ("Оценка ", "point", 18),
            ("Квалификация", "quali", 19), ("Выдать диплом", "diplom", 20),
            ("Отметить, что", "tom", 21),
        ]
        for label_text, key, row in field_config:
            row_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=8)
            ctk.CTkLabel(row_frame, text=label_text, width=320, font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=DesignConfig.FONT_BODY), text_color=DesignConfig.TEXT_PRIMARY).grid(row=0, column=0, padx=(0, 16), sticky="w")
            if key in ['questions', 'property', 'tom', 'theme']:
                entry = CTkTextboxWithMenu(row_frame, width=480, height=70)
            else:
                entry = CTkEntryWithMenu(row_frame, width=480)
            entry.grid(row=0, column=1, sticky="w")
            self.fields[key] = entry
        
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=30)
        ModernButton(btn_frame, text="💾 Сохранить", command=self._save, color=DesignConfig.SUCCESS).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="❌ Отмена", command=self.destroy, fg_color="#e5e7eb", hover_color="#d1d5db", text_color=DesignConfig.TEXT_PRIMARY, width=150, height=35, corner_radius=DesignConfig.CORNER_RADIUS, font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=DesignConfig.FONT_BODY, weight="bold")).pack(side="left", padx=8)
    
    def _fill_data(self, data):
        for key, widget in self.fields.items():
            value = data.get(key, '')
            if value:
                if isinstance(widget, CTkTextboxWithMenu): widget.insert("1.0", str(value))
                else: widget.insert(0, str(value))
    
    def _save(self):
        result = {}
        for key, widget in self.fields.items():
            if isinstance(widget, CTkTextboxWithMenu): result[key] = widget.get("1.0", "end").strip()
            else: result[key] = widget.get().strip()
        required = ['fio']
        for field in required:
            if not result.get(field): messagebox.showerror("Ошибка", f"Поле '{field}' обязательно!"); return
        if self.is_edit and self.student_data: result['_row'] = self.student_data.get('_row')
        self.callback(result)
        self.destroy()


class GosStudentDialog(Toplevel):
    def __init__(self, parent, gos_type, callback, student_data=None):
        super().__init__(parent)
        self.callback = callback
        self.gos_type = gos_type  # Строка: "тест" или "экзамен"
        self.student_data = student_data
        self.is_edit = student_data is not None
        title = "📝 ФИЭБ" if gos_type == "ФИЭБ" else "📚 Экзамен"
        edit_title = "✏️ Редактировать" if self.is_edit else "➕ Добавить"
        self.title(f"{edit_title} студента ({title})")
        self.geometry("900x700")
        self.minsize(800, 600)
        self.resizable(True, True)
        self.grab_set()
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 900) // 2
        y = (self.winfo_screenheight() - 700) // 2
        self.geometry(f"900x700+{x}+{y}")
        ctk.set_appearance_mode("light")
        self._create_widgets()
        if self.is_edit and student_data: self._fill_data(student_data)
    
    def _create_widgets(self):
        main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=24, pady=24)
        header = ctk.CTkFrame(main_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text=f"Данные студента для госэкзамена ({self.gos_type})", font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=DesignConfig.FONT_TITLE, weight="bold"), text_color=DesignConfig.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(header, text="Заполните сначала ФИО. Остальные поля можно заполнить позже.", font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=DesignConfig.FONT_BODY), text_color=DesignConfig.TEXT_SECONDARY).pack(anchor="w", pady=(4, 0))
        
        self.fields = {}
        common_fields = [
            ("ФИО студента *", "fio", 1), ("Протокол №", "protocol", 2),
            ("Направление подготовки", "direction", 3), ("Группа", "group", 4),
            ("Дата экзамена", "date", 5), ("Состав ГЭК утвержден приказом от", "dategek", 6),
            ("Характеристика ответов", "property", 7), ("Оценка ", "mark", 8),
        ]
        
        for label_text, key, row in common_fields:
            row_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=8)
            ctk.CTkLabel(row_frame, text=label_text, width=320, font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=DesignConfig.FONT_BODY), text_color=DesignConfig.TEXT_PRIMARY).grid(row=0, column=0, padx=(0, 16), sticky="w")
            
            # 🔧 ИЗМЕНЕНИЕ: Поле характеристика ответов увеличивается ТОЛЬКО для ТЕСТА
            if key == 'property':
                if self.gos_type == "ФИЭБ":
                    # Для тестирования - увеличенное поле (ширина 900, высота 200)
                    entry = CTkTextboxWithMenu(row_frame, width=900, height=200)
                else:
                    # Для экзамена - стандартное поле (как было раньше)
                    entry = CTkTextboxWithMenu(row_frame, width=480, height=70)
            else:
                entry = CTkEntryWithMenu(row_frame, width=480)
            
            entry.grid(row=0, column=1, sticky="w")
            self.fields[key] = entry
        
        if self.gos_type == "экзамен":
            exam_fields = [("№ вытянутого билета ", "ticket", 9), ("Дата утверждения билетов ", "state_date", 10), ("Вопросы билета", "questions", 11), ("Дополнительные вопросы", "add_questions", 12)]
            for label_text, key, row in exam_fields:
                row_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
                row_frame.pack(fill="x", pady=8)
                ctk.CTkLabel(row_frame, text=label_text, width=320, font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=DesignConfig.FONT_BODY), text_color=DesignConfig.TEXT_PRIMARY).grid(row=0, column=0, padx=(0, 16), sticky="w")
                entry = CTkTextboxWithMenu(row_frame, width=480, height=70)
                entry.grid(row=0, column=1, sticky="w")
                self.fields[key] = entry
        
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=30)
        ModernButton(btn_frame, text="💾 Сохранить", command=self._save, color=DesignConfig.SUCCESS).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="❌ Отмена", command=self.destroy, fg_color="#e5e7eb", hover_color="#d1d5db", text_color=DesignConfig.TEXT_PRIMARY, width=150, height=35, corner_radius=DesignConfig.CORNER_RADIUS, font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=DesignConfig.FONT_BODY, weight="bold")).pack(side="left", padx=8)
    
    def _fill_data(self, data):
        for key, widget in self.fields.items():
            value = data.get(key, '')
            if value:
                if isinstance(widget, CTkTextboxWithMenu): widget.insert("1.0", str(value))
                else: widget.insert(0, str(value))
    
    def _save(self):
        result = {'_type': self.gos_type}
        for key, widget in self.fields.items():
            if isinstance(widget, CTkTextboxWithMenu): result[key] = widget.get("1.0", "end").strip()
            else: result[key] = widget.get().strip()
        required = ['fio']
        for field in required:
            if not result.get(field): messagebox.showerror("Ошибка", f"Поле '{field}' обязательно!"); return
        if self.is_edit and self.student_data: result['_row'] = self.student_data.get('_row')
        self.callback(result)
        self.destroy()


class GECAssistantApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🎓 Secretary assistant")
        self.geometry("1400x900")
        self.minsize(1400, 800)
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.db = Database()
        self.generator = DocumentGenerator(self.db)
        self.current_section = "commission"
        self.nav_buttons = {}
        self._create_ui()
        self.after(100, self._load_startup_data)
    
    def _load_startup_data(self):
        self._load_commission()
    
    def _create_ui(self):
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        sidebar = ctk.CTkFrame(main_container, width=220, corner_radius=DesignConfig.CORNER_RADIUS, fg_color=DesignConfig.CARD_BG)
        sidebar.pack(side="left", fill="y", padx=(0, 20))
        sidebar.pack_propagate(False)
        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.pack(pady=25, padx=15)
        ctk.CTkLabel(logo_frame, text="🎓 Secretary assistant", font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=15, weight="bold"), text_color=DesignConfig.TEXT_PRIMARY).pack()
        ctk.CTkLabel(logo_frame, text="Цифровой помощник", font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=11), text_color=DesignConfig.TEXT_SECONDARY).pack(pady=(4, 0))
        
        nav_buttons = [("📋 Комиссия", "commission", self._show_commission), ("🎯 Госэкзамен", "gos", self._show_gos), ("📄 ВКР", "vkr", self._show_vkr), ("⚙️ Генерация", "generate", self._show_generate)]
        for text, section_id, command in nav_buttons:
            btn = ctk.CTkButton(sidebar, text=text, command=command, anchor="w", height=50, corner_radius=DesignConfig.CORNER_RADIUS, fg_color="transparent", hover_color=DesignConfig.CARD_HOVER, text_color=DesignConfig.TEXT_PRIMARY, font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=17))
            btn.pack(fill="x", padx=12, pady=4)
            self.nav_buttons[section_id] = btn
        self._update_nav_buttons()
        
        self.content_frame = ctk.CTkFrame(main_container, corner_radius=DesignConfig.CORNER_RADIUS, fg_color=DesignConfig.CARD_BG)
        self.content_frame.pack(side="right", fill="both", expand=True)
        self.section_title = ctk.CTkLabel(self.content_frame, text="", font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=DesignConfig.FONT_TITLE, weight="bold"), text_color=DesignConfig.TEXT_PRIMARY)
        self.section_title.pack(pady=24, padx=24, anchor="w")
        self.section_content = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent", corner_radius=0)
        self.section_content.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        self._show_commission()
    
    def _update_nav_buttons(self):
        for section_id, btn in self.nav_buttons.items():
            if section_id == self.current_section: btn.configure(fg_color=DesignConfig.PRIMARY)
            else: btn.configure(fg_color="transparent")
    
    def _show_commission(self):
        self.current_section = "commission"
        self.section_title.configure(text="📋 Данные комиссии")
        self._create_commission_content()
        self._update_nav_buttons()
        self.after(100, self._load_commission)
    
    def _show_vkr(self):
        self.current_section = "vkr"
        self.section_title.configure(text="📄 Выпускные квалификационные работы")
        self._create_vkr_content()
        self._update_nav_buttons()
    
    def _show_gos(self):
        self.current_section = "gos"
        self.section_title.configure(text="🎯 Государственный экзамен")
        self._create_gos_content()
        self._update_nav_buttons()
    
    def _show_generate(self):
        self.current_section = "generate"
        self.section_title.configure(text="⚙️ Генерация документов")
        self._create_generate_content()
        self._update_nav_buttons()
    
    def _create_commission_content(self):
        for widget in self.section_content.winfo_children(): widget.destroy()
        hint_card = ModernCard(self.section_content, title="💡 Подсказка")
        hint_card.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(hint_card, text="Заполните данные комиссии один раз. Они будут автоматически использоваться во всех сгенерированных протоколах.", font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=DesignConfig.FONT_BODY), text_color=DesignConfig.TEXT_SECONDARY, wraplength=500).pack(pady=12, padx=16, anchor="w")
        
        chairman_card = ModernCard(self.section_content, title="👤 Председатель ГЭК")
        chairman_card.pack(fill="x", pady=10)
        for label_text, key in [("ФИО *", "chairman"), ("Должность *", "chairman_position")]:
            row = ctk.CTkFrame(chairman_card, fg_color="transparent"); row.pack(fill="x", pady=8, padx=16)
            # Шрифт Председателя увеличен до 16
            ctk.CTkLabel(row, text=label_text, width=280, text_color=DesignConfig.TEXT_PRIMARY, font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=16)).pack(side="left")
            
            entry = CTkEntryWithMenu(row, width=450); entry.pack(side="left")
            self.commission_fields = getattr(self, 'commission_fields', {})
            self.commission_fields[key] = entry
        
        members_card = ModernCard(self.section_content, title="👥 Члены комиссии")
        members_card.pack(fill="x", pady=10)
        self.commission_fields = getattr(self, 'commission_fields', {})
        for i in range(1, 5):
            sub_card = ctk.CTkFrame(members_card, fg_color=DesignConfig.CARD_HOVER, corner_radius=8); sub_card.pack(fill="x", pady=6, padx=16)
            # Заголовок члена комиссии (размер 15)
            ctk.CTkLabel(sub_card, text=f"Член {i}", font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=15, weight="bold"), text_color=DesignConfig.TEXT_PRIMARY).pack(pady=(12, 4), padx=12, anchor="w")
            
            # ФИО и должность (размер 15)
            for label_text, key in [(f"ФИО {'*' if i <= 3 else ''}", f"member_{i}"), (f"Должность {'*' if i <= 3 else ''}", f"member_{i}_position")]:
                row = ctk.CTkFrame(sub_card, fg_color="transparent"); row.pack(fill="x", pady=4, padx=12)
                ctk.CTkLabel(row, text=label_text, width=260, text_color=DesignConfig.TEXT_PRIMARY, font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=15)).pack(side="left")
                
                entry = CTkEntryWithMenu(row, width=420); entry.pack(side="left")
                self.commission_fields[key] = entry
        
        secretary_card = ModernCard(self.section_content, title="✍️ Секретарь ГЭК")
        secretary_card.pack(fill="x", pady=10)
        for label_text, key in [("ФИО *", "secretary"), ("Должность *", "secretary_position")]:
            row = ctk.CTkFrame(secretary_card, fg_color="transparent"); row.pack(fill="x", pady=8, padx=16)
            # Шрифт Секретаря увеличен до 16
            ctk.CTkLabel(row, text=label_text, width=280, text_color=DesignConfig.TEXT_PRIMARY, font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=16)).pack(side="left")
            
            entry = CTkEntryWithMenu(row, width=450); entry.pack(side="left")
            self.commission_fields[key] = entry
        
        save_btn = ModernButton(self.section_content, text="💾 Сохранить данные комиссии", command=self._save_commission, color=DesignConfig.SUCCESS)
        save_btn.pack(pady=30)
    
    def _save_commission(self):
        data = {key: entry.get() for key, entry in self.commission_fields.items()}
        required = ['chairman', 'chairman_position', 'secretary', 'secretary_position']
        for field in required:
            if not data.get(field): messagebox.showerror("Ошибка", f"Поле '{field}' обязательно!"); return
        
        for i in [1, 2, 3]:
            name_key = f'member_{i}'
            pos_key = f'member_{i}_position'
            if not data.get(name_key) or not data.get(pos_key):
                messagebox.showerror("Ошибка", f"Обязательно заполните ФИО и должность Члена #{i}!")
                return
        
        self.db.save_commission(data)
        messagebox.showinfo("Успешно", "✅ Данные комиссии сохранены!")
    
    def _load_commission(self):
        if not hasattr(self, 'commission_fields'): return
        data = self.db.get_commission()
        for key, value in data.items():
            if key in self.commission_fields and value is not None:
                self.commission_fields[key].delete(0, 'end')
                self.commission_fields[key].insert(0, str(value))
    
    def _create_vkr_content(self):
        for widget in self.section_content.winfo_children(): widget.destroy()
        control_panel = ctk.CTkFrame(self.section_content, fg_color="transparent")
        control_panel.pack(fill="x", pady=(0, 16))
        ModernButton(control_panel, text="➕ Добавить студента", command=self._add_vkr_student, color=DesignConfig.PRIMARY).pack(side="left", padx=(0, 10))
        ModernButton(control_panel, text="🗑️ Очистить список", command=self._clear_vkr, color=DesignConfig.DANGER).pack(side="left")
        self.vkr_count_label = ctk.CTkLabel(control_panel, text="Студентов: 0", font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=20, weight="bold"), text_color=DesignConfig.TEXT_PRIMARY)
        self.vkr_count_label.pack(side="right")
        self.vkr_table_frame = ctk.CTkFrame(self.section_content, fg_color="transparent")
        self.vkr_table_frame.pack(fill="both", expand=True)
        self._refresh_vkr_table()
    
    def _create_gos_content(self):
        for widget in self.section_content.winfo_children(): widget.destroy()
        type_frame = ctk.CTkFrame(self.section_content, fg_color="transparent")
        type_frame.pack(fill="x", pady=(0, 16))
        self.gos_type_var = ctk.StringVar(value="ФИЭБ")
        ctk.CTkLabel(type_frame, text="Тип экзамена:", font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=20, weight="bold"), text_color=DesignConfig.TEXT_PRIMARY).pack(side="left", padx=(0, 16))
        for text, value in [("📝 ФИЭБ", "ФИЭБ"), ("📚 Экзамен", "Экзамен")]:
            ctk.CTkRadioButton(type_frame, text=text, variable=self.gos_type_var, value=value, font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=17)).pack(side="left", padx=8)
        control_panel = ctk.CTkFrame(self.section_content, fg_color="transparent")
        control_panel.pack(fill="x", pady=(16, 0))
        ModernButton(control_panel, text="➕ Добавить студента", command=self._add_gos_student, color=DesignConfig.PRIMARY).pack(side="left", padx=(0, 10))
        ModernButton(control_panel, text="🗑️ Очистить список", command=self._clear_gos, color=DesignConfig.DANGER).pack(side="left")
        self.gos_count_label = ctk.CTkLabel(control_panel, text="Студентов: 0", font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=20, weight="bold"), text_color=DesignConfig.TEXT_PRIMARY)
        self.gos_count_label.pack(side="right")
        self.gos_table_frame = ctk.CTkFrame(self.section_content, fg_color="transparent")
        self.gos_table_frame.pack(fill="both", expand=True, pady=(16, 0))
        self._refresh_gos_table()
    
    def _create_generate_content(self):
        for widget in self.section_content.winfo_children(): widget.destroy()
        options_card = ModernCard(self.section_content, title="📋 Выберите типы документов")
        options_card.pack(fill="x", pady=(0, 24))
        self.gen_vkr = ctk.BooleanVar(value=False)
        self.gen_gos = ctk.BooleanVar(value=False)
        for text, var, desc in [
            ("📄 Протоколы ВКР", self.gen_vkr, "Сгенерировать протоколы для выпускных квалификационных работ"),
            ("🎯 Протоколы Госэкзамена", self.gen_gos, "Сгенерировать протоколы для государственного экзамена (тест/экзамен)")
        ]:
            item = ctk.CTkFrame(options_card, fg_color="transparent")
            item.pack(fill="x", pady=12, padx=16)
            ctk.CTkCheckBox(item, text=text, variable=var, font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=20, weight="bold"), text_color=DesignConfig.TEXT_PRIMARY).pack(anchor="w")
            ctk.CTkLabel(item, text=desc, font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=15), text_color=DesignConfig.TEXT_SECONDARY).pack(anchor="w", pady=(4, 0))
        gen_btn = ModernButton(self.section_content, text="🚀 Сгенерировать документы", command=self._generate_documents, color=DesignConfig.SUCCESS, height=55)
        gen_btn.pack(pady=20)
        self.progress_label = ctk.CTkLabel(self.section_content, text="", font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, size=15), text_color=DesignConfig.TEXT_SECONDARY)
        self.progress_label.pack(pady=(10, 5))
        self.progress_bar = ctk.CTkProgressBar(self.section_content)
        self.progress_bar.pack(fill="x", padx=300, pady=10)
        self.progress_bar.set(0)
    
    def _refresh_vkr_table(self):
        if not hasattr(self, 'vkr_table_frame'): return
        for widget in self.vkr_table_frame.winfo_children(): widget.destroy()
        headers = ["№", "ФИО", "Тема", "Руководитель", "Оценка", ""]
        for col, header in enumerate(headers):
            ctk.CTkLabel(self.vkr_table_frame, text=header, font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, weight="bold", size=16), text_color=DesignConfig.TEXT_PRIMARY).grid(row=0, column=col, padx=12, pady=12, sticky="w")
        students = self.db.get_all_students('ВКР')
        self.vkr_count_label.configure(text=f"Студентов: {len(students)}")
        for i, student in enumerate(students, 1):
            row = i
            ctk.CTkLabel(self.vkr_table_frame, text=str(row), text_color=DesignConfig.TEXT_SECONDARY, font=ctk.CTkFont(size=16)).grid(row=row, column=0, padx=12, pady=8)
            ctk.CTkLabel(self.vkr_table_frame, text=student.get('fio', '')[:35], text_color=DesignConfig.TEXT_PRIMARY, font=ctk.CTkFont(size=16)).grid(row=row, column=1, padx=12, pady=8)
            ctk.CTkLabel(self.vkr_table_frame, text=student.get('theme', '')[:30], text_color=DesignConfig.TEXT_PRIMARY, font=ctk.CTkFont(size=16)).grid(row=row, column=2, padx=12, pady=8)
            ctk.CTkLabel(self.vkr_table_frame, text=student.get('leader', '')[:25], text_color=DesignConfig.TEXT_PRIMARY, font=ctk.CTkFont(size=16)).grid(row=row, column=3, padx=12, pady=8)
            ctk.CTkLabel(self.vkr_table_frame, text=student.get('point', ''), text_color=DesignConfig.SUCCESS, font=ctk.CTkFont(size=16)).grid(row=row, column=4, padx=12, pady=8)
            delete_btn = ctk.CTkButton(self.vkr_table_frame, text="🗑️", width=36, height=36, fg_color=DesignConfig.DANGER, hover_color="#b91c1c", corner_radius=8, command=lambda s=student: self._delete_vkr_student(s))
            delete_btn.grid(row=row, column=5, padx=12, pady=8)
            for col in range(5):
                for w in self.vkr_table_frame.grid_slaves(row=row, column=col): w.bind("<Double-Button-1>", lambda e, s=student: self._edit_vkr_student(s))
    
    def _refresh_gos_table(self):
        if not hasattr(self, 'gos_table_frame'): return
        for widget in self.gos_table_frame.winfo_children(): widget.destroy()
        headers = ["№", "ФИО", "Группа", "Тип", "Оценка", ""]
        for col, header in enumerate(headers):
            ctk.CTkLabel(self.gos_table_frame, text=header, font=ctk.CTkFont(family=DesignConfig.FONT_FAMILY, weight="bold", size=16), text_color=DesignConfig.TEXT_PRIMARY).grid(row=0, column=col, padx=12, pady=12, sticky="w")
        test_students = self.db.get_all_students('ФИЭБ')
        exam_students = self.db.get_all_students('экзамен')
        all_students = []
        for s in test_students: s['_type'] = 'ФИЭБ'; all_students.append(s)
        for s in exam_students: s['_type'] = 'экзамен'; all_students.append(s)
        self.gos_count_label.configure(text=f"Студентов: {len(all_students)}")
        for i, student in enumerate(all_students, 1):
            row = i
            ctk.CTkLabel(self.gos_table_frame, text=str(row), text_color=DesignConfig.TEXT_SECONDARY, font=ctk.CTkFont(size=16)).grid(row=row, column=0, padx=12, pady=8)
            ctk.CTkLabel(self.gos_table_frame, text=student.get('fio', '')[:35], text_color=DesignConfig.TEXT_PRIMARY, font=ctk.CTkFont(size=16)).grid(row=row, column=1, padx=12, pady=8)
            ctk.CTkLabel(self.gos_table_frame, text=student.get('group', ''), text_color=DesignConfig.TEXT_PRIMARY, font=ctk.CTkFont(size=16)).grid(row=row, column=2, padx=12, pady=8)
            ctk.CTkLabel(self.gos_table_frame, text=student.get('_type', ''), text_color=DesignConfig.TEXT_PRIMARY, font=ctk.CTkFont(size=16)).grid(row=row, column=3, padx=12, pady=8)
            ctk.CTkLabel(self.gos_table_frame, text=student.get('mark', ''), text_color=DesignConfig.SUCCESS, font=ctk.CTkFont(size=16)).grid(row=row, column=4, padx=12, pady=8)
            delete_btn = ctk.CTkButton(self.gos_table_frame, text="🗑️", width=36, height=36, fg_color=DesignConfig.DANGER, hover_color="#b91c1c", corner_radius=8, command=lambda s=student: self._delete_gos_student(s))
            delete_btn.grid(row=row, column=5, padx=12, pady=8)
            for col in range(5):
                for w in self.gos_table_frame.grid_slaves(row=row, column=col): w.bind("<Double-Button-1>", lambda e, s=student: self._edit_gos_student(s))

    def _add_vkr_student(self): dialog = VKRStudentDialog(self, self._save_vkr_student)
    def _edit_vkr_student(self, student): dialog = VKRStudentDialog(self, self._save_vkr_student, student)
    def _save_vkr_student(self, data):
        row = data.pop('_row', None)
        if row:
            if self.db.update_student('ВКР', row, data): self._refresh_vkr_table(); messagebox.showinfo("Успешно", "✅ Данные студента обновлены!")
            else: messagebox.showerror("Ошибка", "❌ Не удалось обновить данные")
        else:
            if self.db.add_student('ВКР', data): self._refresh_vkr_table(); messagebox.showinfo("Успешно", "✅ Студент добавлен!")
            else: messagebox.showerror("Ошибка", "❌ Не удалось добавить студента")
    def _delete_vkr_student(self, student):
        fio = student.get('fio')
        row = student.get('_row')
        if messagebox.askyesno("Подтверждение", f"Удалить студента {fio}?"):
            if row and self.db.delete_student('ВКР', row): self._refresh_vkr_table(); messagebox.showinfo("Успешно", "✅ Студент удалён!")
            else: messagebox.showerror("Ошибка", "❌ Не удалось удалить студента")
    def _add_gos_student(self):
        gos_type = self.gos_type_var.get()
        dialog = GosStudentDialog(self, gos_type, self._save_gos_student)
    def _edit_gos_student(self, student):
        gos_type = student.get('_type', 'ФИЭБ')
        dialog = GosStudentDialog(self, gos_type, self._save_gos_student, student)
    def _save_gos_student(self, data):
        row = data.pop('_row', None); sheet_name = data.pop('_type')
        if row:
            if self.db.update_student(sheet_name, row, data): self._refresh_gos_table(); messagebox.showinfo("Успешно", "✅ Данные студента обновлены!")
            else: messagebox.showerror("Ошибка", "❌ Не удалось обновить данные")
        else:
            if self.db.add_student(sheet_name, data): self._refresh_gos_table(); messagebox.showinfo("Успешно", "✅ Студент добавлен!")
            else: messagebox.showerror("Ошибка", "❌ Не удалось добавить студента")
    def _delete_gos_student(self, student):
        fio = student.get('fio')
        row = student.get('_row')
        if messagebox.askyesno("Подтверждение", f"Удалить студента {fio}?"):
            if row: sheet_name = student.get('_type', 'ФИЭБ')
            if self.db.delete_student(sheet_name, row): self._refresh_gos_table(); messagebox.showinfo("Успешно", "✅ Студент удалён!")
            else: messagebox.showerror("Ошибка", "❌ Не удалось удалить студента")
    def _clear_vkr(self):
        if messagebox.askyesno("Подтверждение", "Очистить весь список ВКР?"):
            if self.db.clear_sheet('ВКР'): self._refresh_vkr_table(); messagebox.showinfo("Успешно", "✅ Список ВКР очищен!")
            else: messagebox.showerror("Ошибка", "❌ Не удалось очистить список")
    def _clear_gos(self):
        if messagebox.askyesno("Подтверждение", "Очистить весь список госэкзамена?"):
            if self.db.clear_sheet('тест') and self.db.clear_sheet('экзамен'): self._refresh_gos_table(); messagebox.showinfo("Успешно", "✅ Список госэкзамена очищен!")
            else: messagebox.showerror("Ошибка", "❌ Не удалось очистить список")
    def _generate_documents(self):
        gen_vkr = self.gen_vkr.get(); gen_gos = self.gen_gos.get()
        if not gen_vkr and not gen_gos: messagebox.showwarning("Внимание", "⚠️ Выберите хотя бы один тип документов!"); return
        commission = self.db.get_commission()
        if not commission.get('chairman'): messagebox.showerror("Ошибка", "❌ Сначала заполните данные комиссии!"); return
        vkr_count = len(self.db.get_all_students('ВКР')); test_count = len(self.db.get_all_students('ФИЭБ')); exam_count = len(self.db.get_all_students('экзамен'))
        if gen_vkr and vkr_count == 0: messagebox.showwarning("Внимание", "⚠️ Нет студентов ВКР для генерации!"); return
        if gen_gos and test_count == 0 and exam_count == 0: messagebox.showwarning("Внимание", "⚠️ Нет студентов госэкзамена для генерации!"); return
        try:
            self.progress_label.configure(text="⏳ Генерация документов..."); self.progress_bar.set(0.3); self.update()
            archive_path = self.generator.generate(gen_vkr, gen_gos); self.progress_bar.set(1.0); self.progress_label.configure(text=f"✅ Готово! Архив: {os.path.basename(archive_path)}")
            messagebox.showinfo("Успешно", f"✅ Документы сгенерированы!\n\n📦 Архив:\n{archive_path}")
        except Exception as e:
            self.progress_label.configure(text=f"❌ Ошибка: {str(e)}"); messagebox.showerror("Ошибка", f"❌ Не удалось сгенерировать документы:\n{str(e)}")

if __name__ == "__main__":
    app = GECAssistantApp()
    app.mainloop()