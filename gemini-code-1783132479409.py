import time
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from pynput import keyboard, mouse
from pywinauto import Desktop, Application

class SmartAutomationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Công cụ Tự động hóa Thông minh v3.0")
        self.root.geometry("550x450")
        self.root.resizable(False, False)

        # Biến trạng thái
        self.is_recording = False
        self.is_running = False
        self.actions_log = []
        self.desktop = Desktop(backend="uia")
        self.start_time = 0
        self.current_focused_element = None
        self.proc = None

        # Giao diện người dùng (GUI)
        self.create_widgets()

        # Khởi chạy các bộ lắng nghe sự kiện hệ thống ngầm
        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press)
        self.mouse_listener.start()
        self.keyboard_listener.start()

    def create_widgets(self):
        # --- Vùng cấu hình hệ thống ---
        config_frame = tk.LabelFrame(self.root, text=" Cấu hình đường dẫn & Cửa sổ ", padx=10, pady=10)
        config_frame.pack(fill="x", padx=15, pady=10)

        tk.Label(config_frame, text="Đường dẫn file (.exe):").grid(row=0, column=0, sticky="w")
        self.entry_path = tk.Entry(config_frame, width=40)
        self.entry_path.grid(row=0, column=1, pady=5)
        self.entry_path.insert(0, r"C:\Windows\notepad.exe")

        tk.Label(config_frame, text="Tên cửa sổ (Title):").grid(row=1, column=0, sticky="w")
        self.entry_title = tk.Entry(config_frame, width=40)
        self.entry_title.grid(row=1, column=1, pady=5)
        self.entry_title.insert(0, "Untitled - Notepad")

        # --- Vùng thiết lập thời gian ---
        time_frame = tk.LabelFrame(self.root, text=" Thiết lập thời gian (Chu kỳ) ", padx=10, pady=10)
        time_frame.pack(fill="x", padx=15, pady=5)

        tk.Label(time_frame, text="Sau khi thao tác xong, chờ ngâm máy:").grid(row=0, column=0, sticky="w")
        self.entry_time = tk.Entry(time_frame, width=10)
        self.entry_time.grid(row=0, column=1, padx=5)
        self.entry_time.insert(0, "10")
        tk.Label(time_frame, text="giây rồi Tắt/Bật lại.").grid(row=0, column=2, sticky="w")

        # --- Vùng Nút điều khiển ---
        btn_frame = tk.Frame(self.root, pady=10)
        btn_frame.pack()

        self.btn_record = tk.Button(btn_frame, text="🔴 Bắt đầu Học (F7)", font=("Helvetica", 10, "bold"), bg="#ffcccc", width=20, command=self.toggle_record)
        self.btn_record.grid(row=0, column=0, padx=10)

        self.btn_run = tk.Button(btn_frame, text="▶️ Chạy Tự động (F8)", font=("Helvetica", 10, "bold"), bg="#ccffcc", width=20, command=self.toggle_run)
        self.btn_run.grid(row=0, column=1, padx=10)

        # --- Log màn hình ---
        log_frame = tk.LabelFrame(self.root, text=" Trạng thái hoạt động ")
        log_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.log_text = tk.Text(log_frame, height=10, state="disabled", bg="#f0f0f0")
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

    def write_log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    # --- LOGIC THAO TÁC HỌC (RECORDING) ---
    def toggle_record(self):
        if not self.is_recording:
            if self.is_running: return
            self.actions_log.clear()
            self.start_time = time.time()
            self.is_recording = True
            self.btn_record.config(text="⏹️ Dừng Học (F7)", bg="#ff3333", fg="white")
            self.write_log("🔴 CHẾ ĐỘ HỌC ĐÃ BẬT: Hãy thao tác trên phần mềm mục tiêu...")
        else:
            self.is_recording = False
            self.btn_record.config(text="🔴 Bắt đầu Học (F7)", bg="#ffcccc", fg="black")
            self.write_log(f"⏹️ ĐÃ DỪNG HỌC. Lưu thành công {len(self.actions_log)} hành động ngầm.")

    def on_click(self, x, y, button, pressed):
        if self.is_recording and pressed:
            try:
                element = self.desktop.from_point(x, y)
                title = element.window_text()
                control_type = element.element_info.control_type
                self.current_focused_element = {'title': title, 'control_type': control_type}
                
                self.actions_log.append({
                    'action_type': 'click', 'title': title, 'control_type': control_type, 'time': time.time() - self.start_time
                })
                self.root.after(0, self.write_log, f"👉 Đã học Click: [{control_type}] '{title}'")
            except Exception: pass

    def on_press(self, key):
        if key == keyboard.Key.f7:
            self.root.after(0, self.toggle_record)
        elif key == keyboard.Key.f8:
            self.root.after(0, self.toggle_run)
        elif self.is_recording and self.current_focused_element:
            try:
                char = key.char
                if char:
                    self.actions_log.append({
                        'action_type': 'type_text', 'title': self.current_focused_element['title'],
                        'control_type': self.current_focused_element['control_type'], 'text': str(char), 'time': time.time() - self.start_time
                    })
            except AttributeError:
                if key in [keyboard.Key.enter, keyboard.Key.tab]:
                    self.actions_log.append({
                        'action_type': 'press_key', 'title': self.current_focused_element['title'],
                        'control_type': self.current_focused_element['control_type'], 'key_name': key.name, 'time': time.time() - self.start_time
                    })

    # --- LOGIC PHÁT LẠI VÀ CHU KỲ RESET (RUNNING) ---
    def toggle_run(self):
        if not self.is_running:
            if self.is_recording: return
            if not self.actions_log:
                messagebox.showwarning("Cảnh báo", "Bạn chưa cho công cụ 'Học' thao tác nào cả!")
                return
            self.is_running = True
            self.btn_run.config(text="⏹️ Dừng Chạy (F8)", bg="#ff3333", fg="white")
            threading.Thread(target=self.automation_loop, daemon=True).start()
        else:
            self.is_running = False
            self.btn_run.config(text="▶️ Chạy Tự động (F8)", bg="#ccffcc", fg="black")
            self.write_log("⏹️ ĐÃ DỪNG TIẾN TRÌNH TỰ ĐỘNG HÓA.")
            if self.proc:
                self.proc.kill()

    def automation_loop(self):
        path_app = self.entry_path.get()
        title_app = self.entry_title.get()
        
        try:
            delay_reset = int(self.entry_time.get())
        except ValueError:
            delay_reset = 10

        loop_count = 1
        while self.is_running:
            self.write_log(f"\n🔄 === CHU KỲ TỰ ĐỘNG THỨ {loop_count} ===")
            self.write_log(f"-> Khởi động: {path_app}")
            try:
                self.proc = subprocess.Popen(path_app)
            except Exception as e:
                self.write_log(f"❌ Không thể mở file exe: {e}")
                self.is_running = False
                break
                
            time.sleep(3)
            
            if not self.is_running: break

            try:
                app = Application(backend="uia").connect(title_re=f".*{title_app}.*")
                main_win = app.window(title_re=f".*{title_app}.*")
                
                self.write_log("-> Đang thực hiện các thao tác ngầm...")
                prev_time = 0
                for action in self.actions_log:
                    if not self.is_running: break
                    delay = action['time'] - prev_time
                    time.sleep(max(0, delay))
                    prev_time = action['time']
                    
                    target_element = main_win.child_window(title=action['title'], control_type=action['control_type'])
                    
                    if action['action_type'] == 'click':
                        target_element.click_input()
                    elif action['action_type'] == 'type_text':
                        target_element.type_keys(action['text'], with_spaces=True, with_tabs=True)
                    elif action['action_type'] == 'press_key':
                        target_element.type_keys(f"{{{action['key_name']}}}")
                
                self.write_log(f"-> Thao tác xong. Treo máy đợi {delay_reset} giây...")
                
                # Chờ đợi thông minh, cho phép ngắt giữa chừng khi nhấn dừng
                for _ in range(delay_reset):
                    if not self.is_running: break
                    time.sleep(1)

            except Exception as e:
                self.write_log(f"❌ Lỗi điều khiển: {e}")

            if self.proc:
                self.write_log("-> Tắt phần mềm mục tiêu để reset.")
                self.proc.kill()
            time.sleep(2)
            loop_count += 1

if __name__ == "__main__":
    root = tk.Tk()
    app = SmartAutomationApp(root)
    root.mainloop()