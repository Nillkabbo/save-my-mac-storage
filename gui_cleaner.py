#!/usr/bin/env python3
"""
macOS Cleaner GUI - Modern Tkinter interface for the macOS cleaner

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from pathlib import Path
import sys
import queue

SRC_ROOT = Path(__file__).resolve().parent / "src"
if SRC_ROOT.exists():
    sys.path.insert(0, str(SRC_ROOT))

from mac_cleaner.mac_cleaner import MacCleaner


class MacCleanerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("macOS Cleaner - Read-Only Analysis Mode")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")

        self.cleaner = MacCleaner()
        self.update_queue = queue.Queue()

        self.setup_styles()
        self.create_widgets()
        self.check_queue()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Title.TLabel", font=("SF Pro Display", 16, "bold"), background="#f0f0f0"
        )
        style.configure(
            "Heading.TLabel", font=("SF Pro Text", 12, "bold"), background="#f0f0f0"
        )
        style.configure("Info.TLabel", font=("SF Pro Text", 10), background="#f0f0f0")
        style.configure(
            "Success.TLabel",
            font=("SF Pro Text", 10),
            foreground="#28a745",
            background="#f0f0f0",
        )
        style.configure(
            "Warning.TLabel",
            font=("SF Pro Text", 10),
            foreground="#ffc107",
            background="#f0f0f0",
        )

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        ttk.Label(main_frame, text="🍎 macOS Cleaner", style="Title.TLabel").grid(
            row=0, column=0, columnspan=3, pady=(0, 20)
        )

        self.create_system_info(main_frame)
        self.create_analysis_section(main_frame)
        self.create_controls(main_frame)
        self.create_log_section(main_frame)

    def create_system_info(self, parent):
        info_frame = ttk.LabelFrame(parent, text="System Information", padding="10")
        info_frame.grid(
            row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        system_info = self.cleaner.system_info
        info_text = f"macOS {system_info['release']} • Memory: {self.cleaner.format_bytes(system_info['total_memory'])} • Disk: {self.cleaner.format_bytes(system_info['disk_usage'])}"
        ttk.Label(info_frame, text=info_text, style="Info.TLabel").grid(
            row=0, column=0, sticky=tk.W
        )

    def create_analysis_section(self, parent):
        analysis_frame = ttk.LabelFrame(parent, text="Space Analysis", padding="10")
        analysis_frame.grid(
            row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10)
        )
        analysis_frame.columnconfigure(0, weight=1)

        self.analysis_text = scrolledtext.ScrolledText(
            analysis_frame, height=8, wrap=tk.WORD, font=("SF Mono", 10)
        )
        self.analysis_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.analyze_button = ttk.Button(
            analysis_frame, text="📊 Analyze Space", command=self.start_analysis
        )
        self.analyze_button.grid(row=1, column=0, pady=(10, 0))

    def create_controls(self, parent):
        control_frame = ttk.LabelFrame(parent, text="Cleaning Controls", padding="10")
        control_frame.grid(
            row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        self.clean_all_button = ttk.Button(
            control_frame,
            text="Scan All Categories",
            command=self.start_cleaning_all,
            state="disabled",
            style="Primary.TButton"
        )
        self.clean_all_button.grid(row=0, column=0, padx=(0, 10))

        self.clean_selected_button = ttk.Button(
            control_frame,
            text="Scan Selected",
            command=self.start_cleaning_selected,
            state="disabled",
        )
        self.clean_selected_button.grid(row=0, column=1, padx=(0, 10))

        self.dry_run_var = tk.BooleanVar(value=True)
        ttk.Label(
            control_frame, text="🔒 Read-Only Mode", foreground="gray"
        ).grid(row=0, column=2, padx=(0, 10))

        self.progress = ttk.Progressbar(control_frame, mode="indeterminate")
        self.progress.grid(
            row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0)
        )

        self.status_label = ttk.Label(control_frame, text="Ready for system scan", style="Info.TLabel")
        self.status_label.grid(row=2, column=0, columnspan=3, pady=(15, 0))

    def create_log_section(self, parent):
        log_frame = ttk.LabelFrame(parent, text="Activity Log", padding="10")
        log_frame.grid(
            row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10)
        )
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        parent.rowconfigure(4, weight=1)

        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=10, wrap=tk.WORD, font=("SF Mono", 9)
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        clear_button = ttk.Button(log_frame, text="Clear Log", command=self.clear_log)
        clear_button.grid(row=1, column=0, pady=(5, 0))

    def log_message(self, message, level="info"):
        timestamp = (
            threading.current_thread().name
            if threading.current_thread().name != "MainThread"
            else "Main"
        )
        formatted_message = f"[{timestamp}] {message}\n"

        self.update_queue.put(("log", formatted_message))

    def check_queue(self):
        try:
            while True:
                action, data = self.update_queue.get_nowait()

                if action == "log":
                    self.log_text.insert(tk.END, data)
                    self.log_text.see(tk.END)
                elif action == "status":
                    self.status_label.config(text=data)
                elif action == "progress_start":
                    self.progress.start()
                elif action == "progress_stop":
                    self.progress.stop()
                elif action == "enable_buttons":
                    self.clean_all_button.config(state="normal")
                    self.clean_selected_button.config(state="normal")
                elif action == "disable_buttons":
                    self.clean_all_button.config(state="disabled")
                    self.clean_selected_button.config(state="disabled")

        except queue.Empty:
            pass # Removed incorrect style configuration from here

        self.root.after(100, self.check_queue)

    def start_analysis(self):
        self.analyze_button.config(state="disabled")
        self.update_queue.put(("progress_start", None))
        self.update_queue.put(("status", "Analyzing disk space..."))

        thread = threading.Thread(target=self.analyze_space, daemon=True)
        thread.start()

    def analyze_space(self):
        try:
            self.log_message("Starting space analysis...")
            analysis = self.cleaner.analyze_cleanable_space()

            self.update_queue.put(("log", "\n=== SPACE ANALYSIS ===\n"))

            total_cleanable = 0
            for category, info in analysis.items():
                if info["total_size"] > 0:
                    message = f"{category.replace('_', ' ').title()}: {info['total_size_human']}"
                    self.update_queue.put(("log", message + "\n"))
                    total_cleanable += info["total_size"]

                    for detail in info["details"]:
                        self.update_queue.put(
                            ("log", f"  └─ {detail['path']}: {detail['size_human']}\n")
                        )

            total_message = (
                f"\nTotal cleanable space: {self.cleaner.format_bytes(total_cleanable)}"
            )
            self.update_queue.put(("log", total_message + "\n"))

            self.update_queue.put(("log", "\n" + "=" * 50 + "\n"))

            self.analysis_text.delete(1.0, tk.END)
            self.analysis_text.insert(tk.END, f"Space Analysis Results\n{'=' * 30}\n\n")

            for category, info in analysis.items():
                if info["total_size"] > 0:
                    self.analysis_text.insert(
                        tk.END,
                        f"{category.replace('_', ' ').title()}: {info['total_size_human']}\n",
                    )

            self.analysis_text.insert(
                tk.END, f"\nTotal: {self.cleaner.format_bytes(total_cleanable)}"
            )

            self.update_queue.put(("status", "Analysis complete"))
            self.update_queue.put(("enable_buttons", None))

        except Exception as e:
            self.update_queue.put(("log", f"Error during analysis: {str(e)}\n"))
            self.update_queue.put(("status", "Analysis failed"))
        finally:
            self.update_queue.put(("progress_stop", None))
            self.analyze_button.config(state="normal")

    def start_cleaning_all(self):
        if self.dry_run_var.get():
            result = messagebox.askyesno(
                "Dry Run", "This is a DRY RUN - no files will be deleted. Continue?"
            )
        else:
            result = messagebox.askyesno(
                "Confirm Cleaning", "This will permanently delete files. Are you sure?"
            )

        if result:
            self.update_queue.put(("disable_buttons", None))
            self.update_queue.put(("progress_start", None))
            self.update_queue.put(("status", "Analyzing..."))

            thread = threading.Thread(target=self.clean_all, daemon=True)
            thread.start()

    def clean_all(self):
        try:
            dry_run = self.dry_run_var.get()
            mode_text = "DRY RUN" if dry_run else "LIVE CLEANING"

            self.log_message(f"Starting {mode_text}...")

            results = self.cleaner.clean_all(dry_run=dry_run)

            self.update_queue.put(("log", f"\n=== {mode_text} RESULTS ===\n"))
            self.update_queue.put(
                ("log", f"Files identified: {results['total_files']}\n")
            )
            self.update_queue.put(
                ("log", f"Potential savings: {results['total_space_human']}\n")
            )

            if self.cleaner.stats["errors"]:
                self.update_queue.put(
                    ("log", f"\nErrors: {len(self.cleaner.stats['errors'])}\n")
                )
                for error in self.cleaner.stats["errors"][:5]:
                    self.update_queue.put(("log", f"  - {error}\n"))

            self.update_queue.put(("status", f"{mode_text} complete"))

        except Exception as e:
            self.update_queue.put(("log", f"Error during cleaning: {str(e)}\n"))
            self.update_queue.put(("status", "Cleaning failed"))
        finally:
            self.update_queue.put(("progress_stop", None))
            self.update_queue.put(("enable_buttons", None))

    def start_cleaning_selected(self):
        messagebox.showinfo(
            "Coming Soon", "Selective cleaning will be available in the next version!"
        )

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)


def main():
    root = tk.Tk()
    app = MacCleanerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
