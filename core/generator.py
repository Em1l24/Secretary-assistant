# core/generator.py
from docxtpl import DocxTemplate
import zipfile, os, sys, tempfile, shutil, subprocess
from pathlib import Path
from datetime import datetime
from core.utils import (normalize_fio, get_gender_from_fio, to_genitive, to_dative, to_accusative, reverse_initials, create_safe_filename, create_archive, leader_to_genitive)

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class DocumentGenerator:
    def __init__(self, database, template_dir='templates'):
        self.db = database
        self.template_dir = template_dir
        self.template_vkr_book = get_resource_path(os.path.join(template_dir, 'книга_протоколов_ВКР.docx'))
        self.template_vkr = get_resource_path(os.path.join(template_dir, 'шаблон_протокола_ВКР.docx'))
        self.template_gos_book = get_resource_path(os.path.join(template_dir, 'книга_протоколов_госы.docx'))
        self.template_gos_test = get_resource_path(os.path.join(template_dir, 'шаблон_протокола_гос_экз_тест.docx'))
        self.template_gos_exam = get_resource_path(os.path.join(template_dir, 'шаблон_протокола_гос_экз_экзамен.docx'))
    
    def generate(self, generate_vkr=False, generate_gos=False):
        temp_dir = tempfile.mkdtemp(prefix="gec_protocols_")
        try:
            commission = self.db.get_commission()
            chairman_reversed = reverse_initials(commission.get('chairman'))
            secretary_reversed = reverse_initials(commission.get('secretary'))
            generated_files = []
            if generate_vkr:
                generated_files.extend(self._generate_vkr_documents(temp_dir, commission, chairman_reversed, secretary_reversed))
            if generate_gos:
                generated_files.extend(self._generate_gos_documents(temp_dir, commission, chairman_reversed, secretary_reversed))
            if not generated_files:
                raise ValueError("Нет данных для генерации документов.")
            return self._create_archive(temp_dir, generated_files)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _generate_vkr_documents(self, temp_dir, commission, chairman_reversed, secretary_reversed):
        students = self.db.get_all_students('ВКР')
        if not students: return []
        common_vkr = self.db.get_common_data_vkr()
        book_data = students[0]
        book_context = {
            'direction_2': book_data.get('direction') or common_vkr.get('direction'),
            'date_2': book_data.get('date') or common_vkr.get('date'),
            'status': commission.get('secretary_position'),
            'secretary_3': commission.get('secretary')
        }
        book_doc = DocxTemplate(self.template_vkr_book)
        book_doc.render(book_context)
        book_path = os.path.join(temp_dir, 'книга_протоколов_ВКР.docx')
        book_doc.save(book_path)
        generated_files = [book_path]
        for i, student in enumerate(students, start=5):
            fio = student.get('fio')
            if not fio: continue
            member_4 = commission.get('member_4') if commission.get('member_4') else '–'
            position_4 = commission.get('member_4_position') if commission.get('member_4_position') else '–'
            context = {
                'protocol_2': student.get('protocol'),
                'direction_2': student.get('direction') or common_vkr.get('direction'),
                'date_2': student.get('date') or common_vkr.get('date'),
                'initials_gene': to_genitive(fio), 'theme': student.get('theme'),
                'chairman': commission.get('chairman'), 'position': commission.get('chairman_position'),
                'member_1': commission.get('member_1', ''), 'position_1': commission.get('member_1_position', ''),
                'member_2': commission.get('member_2', ''), 'position_2': commission.get('member_2_position', ''),
                'member_3': commission.get('member_3', ''), 'position_3': commission.get('member_3_position', ''),
                'member_4': member_4, 'position_4': position_4,
                'secretary_1': secretary_reversed, 'secretary_2': secretary_reversed, 'secretary_3': commission.get('secretary'),
                'dategek_2': student.get('dategek') or common_vkr.get('dategek'),
                'leader': leader_to_genitive(student.get('leader')) if student.get('leader') else "",
                'post': student.get('post'), 'con': student.get('con'), 'order': student.get('order') or common_vkr.get('order'),
                'pages': student.get('pages'), 'con_1': student.get('con_1'), 'con_2': student.get('con_2'),
                'review': student.get('review'), 'time': student.get('time'), 'questions_1': student.get('questions'),
                'property_2': student.get('property'), 'point': student.get('point'), 'initials_acc': to_dative(fio),
                'quali': student.get('quali') or common_vkr.get('quali'), 'diplom': student.get('diplom'), 'tom': student.get('tom'),
                'chairman_2': chairman_reversed
            }
            doc = DocxTemplate(self.template_vkr)
            doc.render(context)
            file_path = os.path.join(temp_dir, create_safe_filename(fio, 'ВКР', i))
            doc.save(file_path)
            generated_files.append(file_path)
        return generated_files
    
    def _generate_gos_documents(self, temp_dir, commission, chairman_reversed, secretary_reversed):
        generated_files = []
        test_students = self.db.get_all_students('тест')
        exam_students = self.db.get_all_students('экзамен')
        # 🔧 ИСПОЛЬЗУЕМ ЕДИНЫЙ МЕТОД БЕЗ ПАРАМЕТРОВ
        common_gos = self.db.get_common_data_gos()
        
        if test_students or exam_students:
            book_data = exam_students[0] if exam_students else test_students[0]
            book_context = {
                'direction_1': book_data.get('direction') or common_gos.get('direction'),
                'date_1': book_data.get('date') or common_gos.get('date'),
                'secretary_1': secretary_reversed
            }
            book_doc = DocxTemplate(self.template_gos_book)
            book_doc.render(book_context)
            book_path = os.path.join(temp_dir, 'книга_протоколов_госы.docx')
            book_doc.save(book_path)
            generated_files.append(book_path)
        
        member_4 = commission.get('member_4') if commission.get('member_4') else '–'
        position_4 = commission.get('member_4_position') if commission.get('member_4_position') else '–'
        
        for i, student in enumerate(test_students, start=4):
            fio = student.get('fio')
            if not fio: continue
            context = {
                'protocol': student.get('protocol'),
                'direction': student.get('direction') or common_gos.get('direction'),
                'date': student.get('date') or common_gos.get('date'),
                'chairman': commission.get('chairman'), 'position': commission.get('chairman_position'),
                'member_1': commission.get('member_1', ''), 'position_1': commission.get('member_1_position', ''),
                'member_2': commission.get('member_2', ''), 'position_2': commission.get('member_2_position', ''),
                'member_3': commission.get('member_3', ''), 'position_3': commission.get('member_3_position', ''),
                'member_4': member_4, 'position_4': position_4,
                'secretary_1': secretary_reversed, 'secretary_2': secretary_reversed, 'secretary_3': commission.get('secretary'),
                'dategek': student.get('dategek') or common_gos.get('dategek'),
                'group': student.get('group') or common_gos.get('group'),
                'initials_gen': to_accusative(fio), 'property': student.get('property'),
                'initials': normalize_fio(fio), 'mark': student.get('mark'), 'chairman_1': chairman_reversed
            }
            doc = DocxTemplate(self.template_gos_test)
            doc.render(context)
            file_path = os.path.join(temp_dir, create_safe_filename(fio, 'тест', i))
            doc.save(file_path)
            generated_files.append(file_path)
        
        for i, student in enumerate(exam_students, start=4):
            fio = student.get('fio')
            if not fio: continue
            context = {
                'protocol_1': student.get('protocol'),
                'direction_1': student.get('direction') or common_gos.get('direction'),
                'date_1': student.get('date') or common_gos.get('date'),
                'chairman': commission.get('chairman'), 'position': commission.get('chairman_position'),
                'member_1': commission.get('member_1', ''), 'position_1': commission.get('member_1_position', ''),
                'member_2': commission.get('member_2', ''), 'position_2': commission.get('member_2_position', ''),
                'member_3': commission.get('member_3', ''), 'position_3': commission.get('member_3_position', ''),
                'member_4': member_4, 'position_4': position_4,
                'secretary_1': secretary_reversed, 'secretary_2': secretary_reversed, 'secretary_3': commission.get('secretary'),
                'dategek_1': student.get('dategek') or common_gos.get('dategek'),
                'group_1': student.get('group') or common_gos.get('group'),
                'initials_gen_1': to_accusative(fio), 'ticket': student.get('ticket'),
                'state_date': student.get('state_date') or common_gos.get('state_date'),
                'questions': student.get('questions'), 'add_questions': student.get('add_questions'),
                'property_1': student.get('property'), 'initials_1': normalize_fio(fio),
                'mark_1': student.get('mark'), 'chairman_1': chairman_reversed
            }
            doc = DocxTemplate(self.template_gos_exam)
            doc.render(context)
            file_path = os.path.join(temp_dir, create_safe_filename(fio, 'экзамен', i))
            doc.save(file_path)
            generated_files.append(file_path)
        return generated_files
    
    def _create_archive(self, temp_dir, generated_files):
        desktop_dir = Path.home() / "Desktop"
        archive_path = desktop_dir / f"протоколы_ГЭК_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in generated_files:
                if os.path.exists(file_path):
                    zipf.write(file_path, os.path.basename(file_path))
        try:
            if sys.platform == "win32":
                subprocess.run(["explorer", "/select,", str(archive_path)], check=True, capture_output=True)
        except: pass
        return str(archive_path)