# dev_runner.py
"""
Скрипт для разработки с автоперезапуском при изменении файлов
"""
import subprocess
import time
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ChangeHandler(FileSystemEventHandler):
    def __init__(self, process):
        self.process = process
        self.last_modified = time.time()
    
    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            # Защита от множественных перезапусков
            if time.time() - self.last_modified > 1:
                print(f"🔄 Изменения обнаружены в {event.src_path}")
                print("🔄 Перезапуск приложения...")
                
                # Завершаем старый процесс
                self.process.terminate()
                
                # Запускаем новый
                self.process = subprocess.Popen(
                    ['python', 'main.py'],
                    cwd=os.getcwd()
                )
                
                self.last_modified = time.time()

if __name__ == "__main__":
    print("🚀 Запуск режима разработки с автоперезапуском...")
    print("📁 Мониторинг изменений в файлах .py...")
    print("⚠️  Нажмите Ctrl+C для остановки\n")
    
    # Первый запуск
    process = subprocess.Popen(['python', 'main.py'], cwd=os.getcwd())
    
    # Настройка наблюдателя
    event_handler = ChangeHandler(process)
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        process.terminate()
        print("\n✅ Режим разработки остановлен")
    
    observer.join()