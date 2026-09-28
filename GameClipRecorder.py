import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
import numpy as np
import threading
import time
import os
from datetime import datetime
from collections import deque
import keyboard
import mss

class GameClipRecorder:
    def __init__(self, root):
        self.root = root
        self.root.title("Game Clip Recorder - 40 Segundos")
        self.root.geometry("450x450") # Ampliado para que quepa la configuración
        self.root.configure(bg="#1a1a1a")
        
        # Variables principales
        self.is_recording = False
        self.clip_buffer = deque(maxlen=1200)
        self.buffer_lock = threading.Lock()  
        self.fps = 30
        self.recording_thread = None
        
        # Atajos de teclado por defecto
        self.hotkey_start = 'f9'
        self.hotkey_save = 'delete'
        
        # Escuchar globalmente la tecla de iniciar
        try:
            keyboard.add_hotkey(self.hotkey_start, self.start_recording_from_hotkey)
        except:
            pass
            
        # Ruta dinámica inicial
        user_profile = os.environ.get('USERPROFILE', os.path.expanduser('~'))
        self.output_folder = os.path.join(
            user_profile, 
            "Documents", 
            "GTA San Andreas User Files", 
            "SAMP", 
            "grabacioens"
        )
        
        if not os.path.exists(self.output_folder):
            try:
                os.makedirs(self.output_folder)
            except Exception as e:
                self.output_folder = "GameClips"
                if not os.path.exists(self.output_folder):
                    os.makedirs(self.output_folder)
        
        self.create_ui()
        
    def _shorten_path(self, path):
        if len(path) > 30:
            return "..." + path[-27:]
        return path
        
    def create_ui(self):
        # Título
        title_label = tk.Label(self.root, text="Game Clip Recorder", font=("Arial", 16, "bold"), bg="#1a1a1a", fg="#00ff00")
        title_label.pack(pady=10)
        
        # --- NUEVO FRAME DE CONFIGURACIÓN ---
        settings_frame = tk.Frame(self.root, bg="#1a1a1a")
        settings_frame.pack(pady=5, fill=tk.X, padx=20)
        
        tk.Label(settings_frame, text="Carpeta:", bg="#1a1a1a", fg="#ffffff", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.path_label = tk.Label(settings_frame, text=self._shorten_path(self.output_folder), bg="#1a1a1a", fg="#aaaaaa", width=30, anchor="w")
        self.path_label.grid(row=0, column=1, sticky="w", padx=5)
        tk.Button(settings_frame, text="Cambiar", command=self.change_path, bg="#444444", fg="white", font=("Arial", 8)).grid(row=0, column=2)
        
        tk.Label(settings_frame, text="Tecla Iniciar:", bg="#1a1a1a", fg="#ffffff", font=("Arial", 9, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        self.start_key_label = tk.Label(settings_frame, text=f"[{self.hotkey_start.upper()}]", bg="#1a1a1a", fg="#00ff00", width=30, anchor="w")
        self.start_key_label.grid(row=1, column=1, sticky="w", padx=5)
        self.start_key_btn = tk.Button(settings_frame, text="Cambiar", command=self.change_start_hotkey, bg="#444444", fg="white", font=("Arial", 8))
        self.start_key_btn.grid(row=1, column=2)
        
        tk.Label(settings_frame, text="Tecla Guardar:", bg="#1a1a1a", fg="#ffffff", font=("Arial", 9, "bold")).grid(row=2, column=0, sticky="w", pady=5)
        self.save_key_label = tk.Label(settings_frame, text=f"[{self.hotkey_save.upper()}]", bg="#1a1a1a", fg="#00aaff", width=30, anchor="w")
        self.save_key_label.grid(row=2, column=1, sticky="w", padx=5)
        self.save_key_btn = tk.Button(settings_frame, text="Cambiar", command=self.change_save_hotkey, bg="#444444", fg="white", font=("Arial", 8))
        self.save_key_btn.grid(row=2, column=2)

        # Separador visual
        tk.Frame(self.root, height=1, bg="#444444").pack(fill=tk.X, padx=20, pady=10)
        
        # --- SECCIÓN ORIGINAL ---
        # Status
        self.status_label = tk.Label(self.root, text="Estado: Listo", font=("Arial", 10), bg="#1a1a1a", fg="#ffffff")
        self.status_label.pack(pady=2)
        
        self.frame_label = tk.Label(self.root, text="Frames en buffer: 0/1200", font=("Arial", 9), bg="#1a1a1a", fg="#cccccc")
        self.frame_label.pack(pady=1)
        
        self.size_label = tk.Label(self.root, text="Tamaño en RAM: ~0 MB | Tamaño final: ~15-20 MB", font=("Arial", 8), bg="#1a1a1a", fg="#ffaa00")
        self.size_label.pack(pady=1)
        
        # Botones principales
        button_frame = tk.Frame(self.root, bg="#1a1a1a")
        button_frame.pack(pady=10)
        
        self.record_btn = tk.Button(button_frame, text="▶ Iniciar", command=self.start_recording, bg="#00aa00", fg="white", font=("Arial", 9, "bold"), padx=12, pady=6, cursor="hand2")
        self.record_btn.pack(side=tk.LEFT, padx=3)
        
        self.save_btn = tk.Button(button_frame, text="💾 Guardar", command=self.save_clip, bg="#0066cc", fg="white", font=("Arial", 9, "bold"), padx=12, pady=6, state=tk.DISABLED, cursor="hand2")
        self.save_btn.pack(side=tk.LEFT, padx=3)
        
        self.stop_btn = tk.Button(button_frame, text="⏹ Detener", command=self.stop_recording, bg="#cc0000", fg="white", font=("Arial", 9, "bold"), padx=12, pady=6, state=tk.DISABLED, cursor="hand2")
        self.stop_btn.pack(side=tk.LEFT, padx=3)
        
    def change_path(self):
        new_dir = filedialog.askdirectory(initialdir=self.output_folder)
        if new_dir:
            self.output_folder = os.path.normpath(new_dir)
            self.path_label.config(text=self._shorten_path(self.output_folder))
            
    def change_start_hotkey(self):
        self.start_key_btn.config(state=tk.DISABLED, text="...")
        def wait_key():
            time.sleep(0.2)
            key = keyboard.read_hotkey(suppress=False)
            self.root.after(0, self._set_start_key, key)
        threading.Thread(target=wait_key, daemon=True).start()
        
    def _set_start_key(self, key):
        try: keyboard.remove_hotkey(self.hotkey_start)
        except: pass
        self.hotkey_start = key
        try: keyboard.add_hotkey(self.hotkey_start, self.start_recording_from_hotkey)
        except: pass
        self.start_key_btn.config(state=tk.NORMAL, text="Cambiar")
        self.start_key_label.config(text=f"[{self.hotkey_start.upper()}]")
        
    def change_save_hotkey(self):
        self.save_key_btn.config(state=tk.DISABLED, text="...")
        def wait_key():
            time.sleep(0.2)
            key = keyboard.read_hotkey(suppress=False)
            self.root.after(0, self._set_save_key, key)
        threading.Thread(target=wait_key, daemon=True).start()
        
    def _set_save_key(self, key):
        self.hotkey_save = key
        self.save_key_btn.config(state=tk.NORMAL, text="Cambiar")
        self.save_key_label.config(text=f"[{self.hotkey_save.upper()}]")
        if self.is_recording:
            self.status_label.config(text=f"Estado: GRABANDO ● (Presiona {self.hotkey_save.upper()})", fg="#00ff00")
            # Refrescar atajos si se cambia mientras graba
            keyboard.unhook_all()
            try: keyboard.add_hotkey(self.hotkey_start, self.start_recording_from_hotkey)
            except: pass
            try: keyboard.add_hotkey(self.hotkey_save, self.save_clip_hotkey)
            except: pass

    def start_recording_from_hotkey(self):
        if not self.is_recording:
            self.root.after(0, self.start_recording)
            
    def start_recording(self):
        if not self.is_recording:
            self.is_recording = True
            self.record_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.save_btn.config(state=tk.NORMAL)
            self.status_label.config(text=f"Estado: GRABANDO ● (Presiona {self.hotkey_save.upper()})", fg="#00ff00")
            
            with self.buffer_lock:
                self.clip_buffer.clear()
            
            try:
                keyboard.add_hotkey(self.hotkey_save, self.save_clip_hotkey)
            except Exception as e:
                print(f"Error configurando hotkey: {e}")
            
            self.recording_thread = threading.Thread(target=self.record_frames, daemon=True)
            self.recording_thread.start()
    
    def record_frames(self):
        target_frame_time = 1.0 / self.fps
        with mss.MSS() as sct:
            try: monitor = sct.monitors[1]
            except Exception: monitor = sct.monitors[0]
            
            while self.is_recording:
                start_time = time.perf_counter()
                try:
                    screenshot = sct.grab(monitor)
                    frame = np.array(screenshot)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    
                    height, width = frame.shape[:2]
                    new_width = int(width * 0.75)
                    new_height = int(height * 0.75)
                    resized_frame = cv2.resize(frame, (new_width, new_height))
                    
                    _, encoded_frame = cv2.imencode('.jpg', resized_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                    
                    with self.buffer_lock:
                        self.clip_buffer.append(encoded_frame.tobytes())
                    
                    self.root.after(0, self.update_frame_count)
                except Exception as e:
                    print(f"Error durante captura: {e}")
                
                elapsed_time = time.perf_counter() - start_time
                sleep_time = target_frame_time - elapsed_time
                if sleep_time > 0: time.sleep(sleep_time)
    
    def update_frame_count(self):
        with self.buffer_lock:
            count = len(self.clip_buffer)
            estimated_ram_mb = (count * 50) / 1024 
        self.frame_label.config(text=f"Frames en buffer: {count}/1200")
        self.size_label.config(text=f"Tamaño en RAM: ~{estimated_ram_mb:.1f} MB | Tamaño final: ~15-20 MB")
    
    def stop_recording(self):
        self.is_recording = False
        self.record_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Estado: Detenido", fg="#ffaa00")
        
        try: keyboard.remove_hotkey(self.hotkey_save)
        except: pass
    
    def save_clip_hotkey(self):
        with self.buffer_lock:
            if len(self.clip_buffer) == 0: return
        try: keyboard.remove_hotkey(self.hotkey_save)
        except: pass
            
        self.status_label.config(text="Estado: GUARDANDO CLIP... (Espera)", fg="#00aaff")
        threading.Thread(target=self._save_in_background, daemon=True).start()
    
    def _save_in_background(self):
        try:
            with self.buffer_lock:
                if len(self.clip_buffer) == 0: return
                frames_copy = list(self.clip_buffer)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.output_folder, f"clip_{timestamp}.mp4")
            
            first_frame = cv2.imdecode(np.frombuffer(frames_copy[0], np.uint8), cv2.IMREAD_COLOR)
            height, width = first_frame.shape[:2]
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_file, fourcc, self.fps, (width, height))
            
            for frame_bytes in frames_copy:
                frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)
                out.write(frame)
            
            out.release()
            self.root.after(0, lambda: self.status_label.config(text=f"Clip guardado: {timestamp}", fg="#00ff00"))
            
            if self.is_recording:
                try: keyboard.add_hotkey(self.hotkey_save, self.save_clip_hotkey)
                except: pass
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text="Error al guardar clip", fg="#ff0000"))
    
    def save_clip(self):
        self.save_clip_hotkey()

if __name__ == "__main__":
    root = tk.Tk()
    app = GameClipRecorder(root)
    root.mainloop()
