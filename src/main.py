import os
import shutil
import logging
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
from pathlib import Path
from PIL import Image
from pillow_heif import register_heif_opener

# Initialize HEIC support
register_heif_opener()

# --- CONFIGURATION ---
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "organizer.log"

# Create logs directory if it doesn't exist
LOG_DIR.mkdir(exist_ok=True)

# Setup Logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ImageSorterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Sorter")
        self.root.geometry("300x160") # Even more compact
        self.root.resizable(False, False)

        self.source_dir = None
        self.target_dir = None

        # Styling
        style = ttk.Style()
        style.theme_use('default')
        # 1. Thinner Progress Bar (thickness=5)
        style.configure("green.Horizontal.TProgressbar", background='#4CAF50', thickness=5, troughcolor='#f0f0f0', borderwidth=0)

        # Main Container
        main_frame = tk.Frame(root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 3. Removed Title Label

        # Source Selection Button
        self.btn_source = tk.Button(main_frame, text="1. Select Source", command=self.select_source, anchor="w", padx=5, relief=tk.GROOVE)
        self.btn_source.pack(fill=tk.X, pady=2)

        # Target Selection Button
        self.btn_target = tk.Button(main_frame, text="2. Select Destination", command=self.select_target, anchor="w", padx=5, relief=tk.GROOVE)
        self.btn_target.pack(fill=tk.X, pady=2)

        # 2. Small, Centered, Flat Green Start Button
        # We use a frame to center the button easily if needed, or just pack with minimal padding
        self.btn_start = tk.Button(
            main_frame, 
            text="Start Sorting", 
            command=self.start_sorting, 
            bg="#e0e0e0", 
            fg="black",
            state=tk.DISABLED, 
            height=1,     # Small height
            width=15,     # Small width
            relief=tk.FLAT
        )
        self.btn_start.pack(pady=10)

        # Status Text (Small)
        self.status_var = tk.StringVar(value="Ready")
        self.lbl_status = tk.Label(main_frame, textvariable=self.status_var, fg="gray", font=("Segoe UI", 7), anchor="w")
        self.lbl_status.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 0))
        
        # Progress Bar (Bottom)
        self.progress = ttk.Progressbar(main_frame, orient="horizontal", mode="determinate", style="green.Horizontal.TProgressbar")
        self.progress.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 2))

    def select_source(self):
        folder = filedialog.askdirectory()
        if folder:
            self.source_dir = Path(folder)
            display_name = self.source_dir.name if len(self.source_dir.name) < 20 else "..." + self.source_dir.name[-17:]
            self.btn_source.config(text=f"1. Source: {display_name}", fg="black")
            self.check_ready()

    def select_target(self):
        folder = filedialog.askdirectory()
        if folder:
            self.target_dir = Path(folder)
            display_name = self.target_dir.name if len(self.target_dir.name) < 20 else "..." + self.target_dir.name[-17:]
            self.btn_target.config(text=f"2. Dest: {display_name}", fg="black")
            self.check_ready()

    def check_ready(self):
        if self.source_dir and self.target_dir:
            self.btn_start.config(state=tk.NORMAL, bg="#4CAF50", fg="white") # Flat Green when ready

    def start_sorting(self):
        if not self.source_dir or not self.target_dir:
            return
        
        # Safety Check
        if self.source_dir in self.target_dir.parents:
             if not messagebox.askyesno("Warning", "Source folder contains Destination.\nPossible infinite loop. Continue?"):
                 return

        self.status_var.set(f"Starting...")
        self.progress['value'] = 0
        threading.Thread(target=self.run_sorting, daemon=True).start()

    def run_sorting(self):
        try:
            self.btn_start.config(state=tk.DISABLED, bg="#e0e0e0", fg="black")
            
            process_files(self.source_dir, self.target_dir, self.update_progress)
            
            self.update_status("Done!", "green")
            self.progress['value'] = 100
            messagebox.showinfo("Success", f"Organization complete!\nCheck: {self.target_dir.name}")
        except Exception as e:
            logging.error(f"Critical Error: {e}")
            self.update_status(f"Error: {e}", "red")
            messagebox.showerror("Error", f"An error occurred:\n{e}")
        finally:
            self.btn_start.config(state=tk.NORMAL, bg="#4CAF50", fg="white")

    def update_progress(self, current, total, message):
        self.status_var.set(message)
        if total > 0:
            pct = (current / total) * 100
            self.progress['value'] = pct

    def update_status(self, message, color="black"):
        self.status_var.set(message)
        self.lbl_status.config(fg=color)

def get_unique_path(target_path):
    """Adds a suffix to the filename if a file already exists at destination."""
    counter = 1
    original_path = target_path
    while target_path.exists():
        target_path = original_path.with_name(f"{original_path.stem}_{counter}{original_path.suffix}")
        counter += 1
    return target_path

def get_date_taken(image_path):
    """Retrieves the date taken, falling back to modification time if metadata is missing."""
    # 1. Try EXIF DateTimeOriginal (Tag 36867)
    try:
        with Image.open(image_path) as img:
            exif = img.getexif()
            if exif:
                # 36867 = DateTimeOriginal, 306 = DateTime
                date_str = exif.get(36867) or exif.get(306)
                if date_str:
                    try:
                        dt = datetime.strptime(date_str[:10], "%Y:%m:%d")
                        return dt.strftime("%Y-%m")
                    except ValueError:
                        pass
    except Exception:
        pass

    # 2. Fallback to File Modification Time
    try:
        timestamp = os.path.getmtime(image_path)
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m")
    except Exception:
        pass

    return "Unknown_Date"

def process_files(source_dir, target_dir, progress_callback):
    extensions = {'.jpg', '.jpeg', '.png', '.heic', '.webp', '.mp4', '.mov', '.avi', '.mkv'}
    
    # Scan files first for progress bar
    progress_callback(0, 0, "Scanning files...")
    files = [f for f in source_dir.rglob('*') if f.suffix.lower() in extensions]
    total_files = len(files)
    
    report_lines = []
    report_lines.append(f"Sorting Report - {datetime.now()}")
    report_lines.append(f"Source: {source_dir}")
    report_lines.append(f"Target: {target_dir}")
    report_lines.append("-" * 30)

    for i, file_path in enumerate(files):
        if i % 5 == 0:
             progress_callback(i, total_files, f"Processing {i}/{total_files}...")

        if target_dir in file_path.parents:
             continue 

        # Get Date
        folder_date = get_date_taken(file_path)
        
        # Resolve Destination
        dest_folder = target_dir / folder_date
        dest_folder.mkdir(parents=True, exist_ok=True)
        
        target_path = get_unique_path(dest_folder / file_path.name)
        
        # Execute Move
        try:
            if file_path.resolve() == target_path.resolve():
                 continue

            shutil.move(str(file_path), str(target_path))
            log_msg = f"[MOVED] {file_path.name} -> {folder_date}/{target_path.name}"
            logging.info(log_msg)
            report_lines.append(log_msg)
        except Exception as e:
            err_msg = f"[FAILED] {file_path.name}: {e}"
            logging.error(err_msg)
            report_lines.append(err_msg)
            
    progress_callback(total_files, total_files, "Finalizing...")

    # Write Report
    try:
        report_path = target_dir / "sorting_report.txt"
        with open(report_path, "a", encoding="utf-8") as f:
            f.write("\n" + "\n".join(report_lines))
    except Exception as e:
        logging.error(f"Failed to write report: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageSorterApp(root)
    root.mainloop()
