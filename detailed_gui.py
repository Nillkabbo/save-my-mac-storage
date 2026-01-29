#!/usr/bin/env python3
"""
Detailed macOS Cleaner GUI - Advanced interface with precise file information and Finder integration

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import queue
from pathlib import Path
import subprocess
import json
from datetime import datetime
import sys

SRC_ROOT = Path(__file__).resolve().parent / "src"
if SRC_ROOT.exists():
    sys.path.insert(0, str(SRC_ROOT))

from mac_cleaner.file_analyzer import FileAnalyzer
from mac_cleaner.mac_cleaner import MacCleaner


class DetailedCleanerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🍎 macOS Cleaner - Detailed Analysis")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")

        self.analyzer = FileAnalyzer(enable_db_logging=True)
        self.cleaner = MacCleaner()
        self.update_queue = queue.Queue()
        self.current_files = []
        self.selected_directory = None
        self.current_scan_id = None

        self.setup_styles()
        self.create_widgets()
        self.check_queue()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Title.TLabel", font=("SF Pro Display", 18, "bold"), background="#f0f0f0", foreground="#0072ff"
        )
        style.configure(
            "Heading.TLabel", font=("SF Pro Text", 13, "bold"), background="#f0f0f0"
        )
        style.configure("Info.TLabel", font=("SF Pro Text", 10), background="#f0f0f0")
        style.configure(
            "Critical.TLabel",
            font=("SF Pro Text", 10, "bold"),
            foreground="#dc3545",
            background="#f0f0f0",
        )
        style.configure(
            "Important.TLabel",
            font=("SF Pro Text", 10, "bold"),
            foreground="#fd7e14",
            background="#f0f0f0",
        )
        style.configure(
            "Safe.TLabel",
            font=("SF Pro Text", 10, "bold"),
            foreground="#28a745",
            background="#f0f0f0",
        )

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, pady=(0, 20))
        header_frame.columnconfigure(0, weight=1)
        
        ttk.Label(
            header_frame,
            text="🍎 macOS Cleaner - Detailed Analysis",
            style="Title.TLabel",
        ).grid(row=0, column=0, sticky='w')
        
        # Analytics button
        analytics_btn = ttk.Button(
            header_frame,
            text="📊 Analytics Dashboard",
            command=self.open_analytics_dashboard
        )
        analytics_btn.grid(row=0, column=1, padx=(20, 0))

        # Directory selection
        self.create_directory_selector(main_frame)

        # File details view
        self.create_file_details_view(main_frame)

        # Control panel
        self.create_control_panel(main_frame)

        # Status bar
        self.create_status_bar(main_frame)

    def create_directory_selector(self, parent):
        dir_frame = ttk.LabelFrame(parent, text="Directory Analysis", padding="10")
        dir_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        dir_frame.columnconfigure(1, weight=1)

        ttk.Label(dir_frame, text="Select Directory:", style="Info.TLabel").grid(
            row=0, column=0, padx=(0, 10)
        )

        self.dir_var = tk.StringVar()
        self.dir_entry = ttk.Entry(
            dir_frame, textvariable=self.dir_var, font=("SF Mono", 10)
        )
        self.dir_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))

        ttk.Button(dir_frame, text="Browse", command=self.browse_directory).grid(
            row=0, column=2, padx=(0, 5)
        )
        ttk.Button(dir_frame, text="Analyze", command=self.start_analysis).grid(
            row=0, column=3, padx=(0, 5)
        )
        ttk.Button(dir_frame, text="Open in Finder", command=self.open_in_finder).grid(
            row=0, column=4
        )

        # Quick access buttons
        quick_frame = ttk.Frame(dir_frame)
        quick_frame.grid(row=1, column=0, columnspan=5, pady=(10, 0))

        ttk.Button(
            quick_frame,
            text="Caches",
            command=lambda: self.select_quick_dir("cache"),
        ).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(
            quick_frame, text="Logs", command=lambda: self.select_quick_dir("logs")
        ).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(
            quick_frame, text="Trash", command=lambda: self.select_quick_dir("trash")
        ).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(
            quick_frame,
            text="Browser Cache",
            command=lambda: self.select_quick_dir("browser"),
        ).grid(row=0, column=3, padx=(0, 5))

    def create_file_details_view(self, parent):
        details_frame = ttk.LabelFrame(parent, text="File Details", padding="10")
        details_frame.grid(
            row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10)
        )
        details_frame.columnconfigure(0, weight=1)
        details_frame.rowconfigure(0, weight=1)

        # Create treeview for file list
        columns = ("Name", "Size", "Modified", "Safety", "Recommendation", "Path")
        self.file_tree = ttk.Treeview(
            details_frame, columns=columns, show="tree headings", height=15
        )

        # Configure columns
        self.file_tree.heading("#0", text="📁")
        self.file_tree.column("#0", width=50)

        for col in columns:
            self.file_tree.heading(col, text=col)
            if col == "Path":
                self.file_tree.column(col, width=400)
            elif col == "Name":
                self.file_tree.column(col, width=200)
            else:
                self.file_tree.column(col, width=120)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(
            details_frame, orient="vertical", command=self.file_tree.yview
        )
        h_scrollbar = ttk.Scrollbar(
            details_frame, orient="horizontal", command=self.file_tree.xview
        )
        self.file_tree.configure(
            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set
        )

        # Grid layout
        self.file_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # Bind events
        self.file_tree.bind("<<TreeviewSelect>>", self.on_file_select)
        self.file_tree.bind("<Double-1>", self.on_file_double_click)

        # Summary panel
        self.create_summary_panel(details_frame)

    def create_summary_panel(self, parent):
        summary_frame = ttk.Frame(parent)
        summary_frame.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0)
        )

        self.summary_label = ttk.Label(
            summary_frame, text="No directory selected", style="Info.TLabel"
        )
        self.summary_label.grid(row=0, column=0, sticky=tk.W)

    def create_control_panel(self, parent):
        control_frame = ttk.LabelFrame(parent, text="Actions", padding="10")
        control_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # Filter controls
        filter_frame = ttk.Frame(control_frame)
        filter_frame.grid(
            row=0, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        ttk.Label(filter_frame, text="Filter by safety:").grid(
            row=0, column=0, padx=(0, 10)
        )

        self.filter_var = tk.StringVar(value="all")
        filters = [
            ("All", "all"),
            ("Very Safe", "very_safe"),
            ("Safe", "safe"),
            ("Moderate", "moderate"),
            ("Important", "important"),
            ("Critical", "critical"),
        ]

        for i, (text, value) in enumerate(filters):
            ttk.Radiobutton(
                filter_frame,
                text=text,
                variable=self.filter_var,
                value=value,
                command=self.apply_filter,
            ).grid(row=0, column=i + 1, padx=(0, 10))

        # Action buttons
        ttk.Button(
            control_frame,
            text="Top Space Consumers",
            command=self.show_top_consumers,
        ).grid(row=1, column=0, padx=(0, 10))
        ttk.Button(
            control_frame, text="Old Files", command=self.show_old_files
        ).grid(row=1, column=1, padx=(0, 10))
        ttk.Button(
            control_frame, text="Export Analysis", command=self.export_analysis
        ).grid(row=1, column=2, padx=(0, 10))
        self.clean_button = ttk.Button(
            control_frame,
            text="🧹 Review & Analyze",
            command=self.safe_clean,
            state="disabled",
            style="Action.TButton",
        )
        self.clean_button.grid(row=1, column=3, padx=(0, 10))

        # Progress
        self.progress = ttk.Progressbar(control_frame, mode="indeterminate")
        self.progress.grid(
            row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0)
        )

    def create_status_bar(self, parent):
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))

        self.status_label = ttk.Label(status_frame, text="Ready", style="Info.TLabel")
        self.status_label.grid(row=0, column=0, sticky=tk.W)

        self.file_count_label = ttk.Label(status_frame, text="", style="Info.TLabel")
        self.file_count_label.grid(row=0, column=1, sticky=tk.E)

        status_frame.columnconfigure(1, weight=1)

    def browse_directory(self):
        directory = filedialog.askdirectory(initialdir=str(Path.home()))
        if directory:
            self.dir_var.set(directory)
            self.selected_directory = directory

    def select_quick_dir(self, dir_type):
        home = Path.home()
        directories = {
            "cache": str(home / "Library" / "Caches"),
            "logs": str(home / "Library" / "Logs"),
            "trash": str(home / ".Trash"),
            "browser": str(home / "Library" / "Caches" / "Google" / "Chrome"),
        }

        if dir_type in directories:
            self.dir_var.set(directories[dir_type])
            self.selected_directory = directories[dir_type]

    def open_in_finder(self):
        if self.selected_directory:
            if self.analyzer.open_in_finder(self.selected_directory):
                self.update_status("Opened in Finder")
            else:
                messagebox.showerror("Error", "Could not open in Finder")
        else:
            messagebox.showwarning("Warning", "Please select a directory first")

    def start_analysis(self):
        if not self.selected_directory:
            messagebox.showwarning("Warning", "Please select a directory first")
            return

        self.update_status("🔍 Analyzing directory structure...")
        self.progress.start()

        thread = threading.Thread(target=self.analyze_directory, daemon=True)
        thread.start()

    def analyze_directory(self):
        try:
            self.update_queue.put(("status", "Scanning files..."))

            # Start scan tracking
            self.current_scan_id = self.analyzer.start_scan(
                scan_type="directory",
                categories=[self.analyzer._categorize_file(self.selected_directory)]
            )

            # Get directory summary
            summary = self.analyzer.get_directory_summary(self.selected_directory)

            # Scan files
            files = self.analyzer.scan_directory(
                self.selected_directory, max_files=2000
            )
            self.current_files = files

            # Finish scan and save to database
            if self.current_scan_id:
                self.analyzer.finish_scan(files, errors=0)
                self.update_queue.put(("status", f"Analysis complete - {len(files)} files found (saved to database)"))
            else:
                self.update_queue.put(("status", f"Analysis complete - {len(files)} files found"))

            # Update UI
            self.update_queue.put(("files", files))
            self.update_queue.put(("summary", summary))

        except Exception as e:
            self.update_queue.put(("status", f"Analysis failed: {str(e)}"))
        finally:
            self.update_queue.put(("progress_stop", None))

    def apply_filter(self):
        filter_value = self.filter_var.get()

        # Clear tree
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        # Filter and display files
        filtered_files = self.current_files
        if filter_value != "all":
            filtered_files = [
                f for f in self.current_files if f.get("safety_level") == filter_value
            ]

        self.populate_tree(filtered_files)
        self.update_status(
            f"Showing {len(filtered_files)} files (filter: {filter_value})"
        )

    def populate_tree(self, files):
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        for file_info in files:
            if "error" in file_info:
                continue

            # Determine icon and color based on safety
            safety = file_info.get("safety_level", "unknown")
            tags = (safety,)

            values = (
                file_info.get("name", ""),
                file_info.get("size_human", ""),
                file_info.get("modified", "").strftime("%Y-%m-%d %H:%M")
                if file_info.get("modified")
                else "",
                safety.replace("_", " ").title(),
                file_info.get("recommendation", "").title(),
                file_info.get("path", ""),
            )

            self.file_tree.insert("", "end", text="📄", values=values, tags=tags)

        # Configure tags for colors
        self.file_tree.tag_configure("critical", foreground="#dc3545")
        self.file_tree.tag_configure("important", foreground="#fd7e14")
        self.file_tree.tag_configure("moderate", foreground="#ffc107")
        self.file_tree.tag_configure("safe", foreground="#28a745")
        self.file_tree.tag_configure("very_safe", foreground="#20c997")

    def on_file_select(self, event):
        selection = self.file_tree.selection()
        if selection:
            item = self.file_tree.item(selection[0])
            values = item["values"]
            if len(values) >= 6:
                file_path = values[5]
                self.update_status(f"Selected: {file_path}")

    def on_file_double_click(self, event):
        selection = self.file_tree.selection()
        if selection:
            item = self.file_tree.item(selection[0])
            values = item["values"]
            if len(values) >= 6:
                file_path = values[5]
                self.analyzer.open_in_finder(file_path)

    def show_top_consumers(self):
        if not self.selected_directory:
            messagebox.showwarning("Warning", "Please select a directory first")
            return

        self.update_status("Finding top space consumers...")
        self.progress.start()

        thread = threading.Thread(target=self.get_top_consumers, daemon=True)
        thread.start()

    def get_top_consumers(self):
        try:
            top_files = self.analyzer.get_top_space_consumers(
                self.selected_directory, top_n=50
            )
            self.current_files = top_files # Update current_files for filtering/export
            self.update_queue.put(("files", top_files))
            self.update_queue.put(
                (
                    "status",
                    f"Top 50 space consumers - Total: {sum(f.get('size', 0) for f in top_files):,} bytes",
                )
            )
        except Exception as e:
            self.update_queue.put(("status", f"Error: {str(e)}"))
        finally:
            self.update_queue.put(("progress_stop", None))

    def show_old_files(self):
        if not self.selected_directory:
            messagebox.showwarning("Warning", "Please select a directory first")
            return

        self.update_status("Finding old files...")
        self.progress.start()

        thread = threading.Thread(target=self.get_old_files, daemon=True)
        thread.start()

    def get_old_files(self):
        try:
            old_files = self.analyzer.get_old_files(
                self.selected_directory, days_old=30
            )
            self.update_queue.put(("files", old_files))
            self.update_queue.put(
                ("status", f"Files older than 30 days: {len(old_files)}")
            )
        except Exception as e:
            self.update_queue.put(("status", f"Error: {str(e)}"))
        finally:
            self.update_queue.put(("progress_stop", None))

    def export_analysis(self):
        if not self.current_files:
            messagebox.showwarning("Warning", "No analysis data to export")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        )

        if filename:
            if self.analyzer.export_analysis(self.current_files, filename):
                messagebox.showinfo("Success", f"Analysis exported to {filename}")
            else:
                messagebox.showerror("Error", "Failed to export analysis")

    def safe_clean(self):
        if not self.selected_directory:
            messagebox.showwarning("Warning", "Please select a directory first")
            return

        # Get files marked as safe to delete
        safe_files = [
            f for f in self.current_files if f.get("recommendation") == "delete"
        ]

        if not safe_files:
            messagebox.showinfo("Info", "No files marked as safe to delete")
            return

        total_size = sum(f.get("size", 0) for f in safe_files)

        result = messagebox.askyesno(
            "Confirm Safe Cleaning",
            f"Found {len(safe_files)} files safe to delete.\n"
            f"Total space to be freed: {self.analyzer.format_bytes(total_size)}\n\n"
            "These files will be moved to Trash. Continue?",
        )

        if result:
            messagebox.showinfo(
                "Coming Soon",
                "Safe cleaning feature will be implemented in the next version!",
            )

    def update_status(self, message):
        self.update_queue.put(("status", message))

    def check_queue(self):
        try:
            while True:
                action, data = self.update_queue.get_nowait()

                if action == "status":
                    self.status_label.config(text=data)
                elif action == "files":
                    self.populate_tree(data)
                    self.file_count_label.config(text=f"Files: {len(data)}")
                elif action == "summary":
                    summary_text = (
                        f"Total: {data.get('file_count', 0)} files, "
                        f"{data.get('total_size_human', '0 B')} • "
                        f"Deletable: {self.analyzer.format_bytes(data.get('deletable_size', 0))}"
                    )
                    self.summary_label.config(text=summary_text)
                elif action == "progress_start":
                    self.progress.start()
                elif action == "progress_stop":
                    self.progress.stop()

        except queue.Empty:
            pass

        self.root.after(100, self.check_queue)

    def open_analytics_dashboard(self):
        """Open the analytics dashboard in a new window"""
        try:
            # Import here to avoid circular imports
            from src.mac_cleaner.gui.analytics_gui import AnalyticsGUI
            
            # Create analytics window
            analytics_window = tk.Toplevel(self.root)
            analytics_window.title("📊 Analytics Dashboard")
            analytics_window.geometry("1400x900")
            
            # Create analytics GUI
            analytics_app = AnalyticsGUI()
            analytics_app.root.destroy()  # Destroy the root created in AnalyticsGUI
            
            # Re-parent the analytics GUI to our window
            analytics_app.root = analytics_window
            
            # Recreate the analytics GUI in our window
            analytics_app.__init__()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open analytics dashboard: {e}")


def main():
    root = tk.Tk()
    app = DetailedCleanerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
