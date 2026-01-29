#!/usr/bin/env python3
"""
Analytics GUI - Display historical scan records and system analytics

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys
import logging

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.mac_cleaner.file_analyzer import FileAnalyzer
from src.mac_cleaner.core.database import DatabaseManager


class AnalyticsGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("macOS Cleaner - Analytics Dashboard")
        self.root.geometry("1400x900")
        
        # Initialize components
        self.file_analyzer = FileAnalyzer()
        self.db_manager = DatabaseManager()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Setup GUI
        self.setup_styles()
        self.create_widgets()
        self.load_data()
        
    def setup_styles(self):
        """Setup modern macOS-style GUI"""
        self.root.configure(bg='#f0f0f0')
        
        # Configure styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Title.TLabel', background='#f0f0f0', foreground='#333333', font=('SF Pro Display', 24, 'bold'))
        style.configure('Subtitle.TLabel', background='#f0f0f0', foreground='#666666', font=('SF Pro Text', 12))
        style.configure('Card.TFrame', background='white', relief='raised', borderwidth=1)
        style.configure('Header.TLabel', background='white', foreground='#333333', font=('SF Pro Text', 14, 'bold'))
        style.configure('Data.TLabel', background='white', foreground='#666666', font=('SF Pro Text', 11))
        
    def create_widgets(self):
        """Create main GUI widgets"""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_container, text="Analytics Dashboard", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill='both', expand=True)
        
        # Create tabs
        self.create_overview_tab()
        self.create_scan_history_tab()
        self.create_analytics_tab()
        self.create_top_consumers_tab()
        
    def create_overview_tab(self):
        """Create overview tab with summary statistics"""
        overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(overview_frame, text="Overview")
        
        # Container with padding
        container = ttk.Frame(overview_frame)
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Database stats card
        self.create_database_stats_card(container)
        
        # Recent activity card
        self.create_recent_activity_card(container)
        
        # System info card
        self.create_system_info_card(container)
        
    def create_database_stats_card(self, parent):
        """Create database statistics card"""
        card = ttk.Frame(parent, style='Card.TFrame')
        card.pack(fill='x', pady=(0, 15))
        
        # Header
        header = ttk.Label(card, text="Database Statistics", style='Header.TLabel')
        header.pack(padx=15, pady=(15, 10))
        
        # Stats container
        stats_container = ttk.Frame(card)
        stats_container.pack(fill='x', padx=15, pady=(0, 15))
        
        self.db_stats_labels = {}
        stats = [
            ("Total Scans:", "total_scans", "0"),
            ("Files Analyzed:", "total_files", "0"),
            ("Database Size:", "db_size", "0 B"),
            ("Date Range:", "date_range", "No data")
        ]
        
        for i, (label, key, default) in enumerate(stats):
            frame = ttk.Frame(stats_container)
            frame.grid(row=i//2, column=i%2, sticky='w', padx=10, pady=5)
            
            ttk.Label(frame, text=label, style='Data.TLabel').pack(side='left')
            value_label = ttk.Label(frame, text=default, style='Data.TLabel', font=('SF Pro Text', 11, 'bold'))
            value_label.pack(side='left', padx=(10, 0))
            self.db_stats_labels[key] = value_label
            
    def create_recent_activity_card(self, parent):
        """Create recent activity card"""
        card = ttk.Frame(parent, style='Card.TFrame')
        card.pack(fill='x', pady=(0, 15))
        
        # Header
        header = ttk.Label(card, text="Recent Activity", style='Header.TLabel')
        header.pack(padx=15, pady=(15, 10))
        
        # Activity text
        self.activity_text = scrolledtext.ScrolledText(card, height=8, wrap='word', font=('SF Mono', 10))
        self.activity_text.pack(fill='x', padx=15, pady=(0, 15))
        
    def create_system_info_card(self, parent):
        """Create system information card"""
        card = ttk.Frame(parent, style='Card.TFrame')
        card.pack(fill='x', pady=(0, 15))
        
        # Header
        header = ttk.Label(card, text="System Information", style='Header.TLabel')
        header.pack(padx=15, pady=(15, 10))
        
        # System info container
        self.system_info_container = ttk.Frame(card)
        self.system_info_container.pack(fill='x', padx=15, pady=(0, 15))
        
    def create_scan_history_tab(self):
        """Create scan history tab"""
        history_frame = ttk.Frame(self.notebook)
        self.notebook.add(history_frame, text="Scan History")
        
        # Container with padding
        container = ttk.Frame(history_frame)
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Controls
        controls_frame = ttk.Frame(container)
        controls_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(controls_frame, text="Show last:", style='Data.TLabel').pack(side='left')
        
        self.history_limit_var = tk.StringVar(value="50")
        limit_combo = ttk.Combobox(controls_frame, textvariable=self.history_limit_var, 
                                   values=["10", "25", "50", "100", "All"], width=10, state='readonly')
        limit_combo.pack(side='left', padx=(10, 20))
        limit_combo.bind('<<ComboboxSelected>>', lambda e: self.load_scan_history())
        
        refresh_btn = ttk.Button(controls_frame, text="Refresh", command=self.load_scan_history)
        refresh_btn.pack(side='left')
        
        # History treeview
        self.create_history_treeview(container)
        
    def create_history_treeview(self, parent):
        """Create scan history treeview"""
        # Treeview with scrollbars
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill='both', expand=True)
        
        # Scrollbars
        y_scrollbar = ttk.Scrollbar(tree_frame, orient='vertical')
        y_scrollbar.pack(side='right', fill='y')
        
        x_scrollbar = ttk.Scrollbar(tree_frame, orient='horizontal')
        x_scrollbar.pack(side='bottom', fill='x')
        
        # Treeview
        columns = ('Date', 'Type', 'Files', 'Size', 'Duration', 'Space Freed', 'Status')
        self.history_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15,
                                        yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Configure columns
        column_widths = {'Date': 150, 'Type': 100, 'Files': 80, 'Size': 120, 
                        'Duration': 80, 'Space Freed': 120, 'Status': 80}
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=column_widths.get(col, 100))
        
        self.history_tree.pack(fill='both', expand=True)
        
        # Configure scrollbars
        y_scrollbar.config(command=self.history_tree.yview)
        x_scrollbar.config(command=self.history_tree.xview)
        
        # Bind double-click for details
        self.history_tree.bind('<Double-1>', self.show_scan_details)
        
    def create_analytics_tab(self):
        """Create analytics tab with charts"""
        analytics_frame = ttk.Frame(self.notebook)
        self.notebook.add(analytics_frame, text="Analytics")
        
        # Container with padding
        container = ttk.Frame(analytics_frame)
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Controls
        controls_frame = ttk.Frame(container)
        controls_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(controls_frame, text="Period:", style='Data.TLabel').pack(side='left')
        
        self.analytics_period_var = tk.StringVar(value="30")
        period_combo = ttk.Combobox(controls_frame, textvariable=self.analytics_period_var,
                                    values=["7", "30", "90", "365"], width=10, state='readonly')
        period_combo.pack(side='left', padx=(10, 20))
        period_combo.bind('<<ComboboxSelected>>', lambda e: self.load_analytics())
        
        refresh_btn = ttk.Button(controls_frame, text="Refresh", command=self.load_analytics)
        refresh_btn.pack(side='left')
        
        # Charts frame
        self.charts_frame = ttk.Frame(container)
        self.charts_frame.pack(fill='both', expand=True)
        
    def create_top_consumers_tab(self):
        """Create top space consumers tab"""
        consumers_frame = ttk.Frame(self.notebook)
        self.notebook.add(consumers_frame, text="Top Space Consumers")
        
        # Container with padding
        container = ttk.Frame(consumers_frame)
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Controls
        controls_frame = ttk.Frame(container)
        controls_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(controls_frame, text="Period:", style='Data.TLabel').pack(side='left')
        
        self.consumers_period_var = tk.StringVar(value="30")
        period_combo = ttk.Combobox(controls_frame, textvariable=self.consumers_period_var,
                                    values=["7", "30", "90", "365"], width=10, state='readonly')
        period_combo.pack(side='left', padx=(10, 20))
        period_combo.bind('<<ComboboxSelected>>', lambda e: self.load_top_consumers())
        
        ttk.Label(controls_frame, text="Limit:", style='Data.TLabel').pack(side='left', padx=(20, 10))
        
        self.consumers_limit_var = tk.StringVar(value="20")
        limit_combo = ttk.Combobox(controls_frame, textvariable=self.consumers_limit_var,
                                   values=["10", "20", "50", "100"], width=10, state='readonly')
        limit_combo.pack(side='left', padx=(0, 20))
        limit_combo.bind('<<ComboboxSelected>>', lambda e: self.load_top_consumers())
        
        refresh_btn = ttk.Button(controls_frame, text="Refresh", command=self.load_top_consumers)
        refresh_btn.pack(side='left')
        
        # Consumers treeview
        self.create_consumers_treeview(container)
        
    def create_consumers_treeview(self, parent):
        """Create top consumers treeview"""
        # Treeview with scrollbars
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill='both', expand=True)
        
        # Scrollbars
        y_scrollbar = ttk.Scrollbar(tree_frame, orient='vertical')
        y_scrollbar.pack(side='right', fill='y')
        
        x_scrollbar = ttk.Scrollbar(tree_frame, orient='horizontal')
        x_scrollbar.pack(side='bottom', fill='x')
        
        # Treeview
        columns = ('File Path', 'File Name', 'Size', 'Safety Level', 'Category', 'Recommendation', 'Modified')
        self.consumers_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20,
                                          yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Configure columns
        column_widths = {'File Path': 300, 'File Name': 200, 'Size': 100, 'Safety Level': 100,
                        'Category': 100, 'Recommendation': 120, 'Modified': 150}
        
        for col in columns:
            self.consumers_tree.heading(col, text=col)
            self.consumers_tree.column(col, width=column_widths.get(col, 100))
        
        self.consumers_tree.pack(fill='both', expand=True)
        
        # Configure scrollbars
        y_scrollbar.config(command=self.consumers_tree.yview)
        x_scrollbar.config(command=self.consumers_tree.xview)
        
    def load_data(self):
        """Load all data"""
        self.load_database_stats()
        self.load_recent_activity()
        self.load_system_info()
        self.load_scan_history()
        self.load_analytics()
        self.load_top_consumers()
        
    def load_database_stats(self):
        """Load database statistics"""
        try:
            stats = self.db_manager.get_database_stats()
            
            self.db_stats_labels['total_scans'].config(text=str(stats['scan_records']))
            self.db_stats_labels['total_files'].config(text=f"{stats['file_records']:,}")
            self.db_stats_labels['db_size'].config(text=stats['database_size_human'])
            
            date_range = stats['date_range']
            if date_range['earliest'] and date_range['latest']:
                start = datetime.fromisoformat(date_range['earliest']).strftime('%Y-%m-%d')
                end = datetime.fromisoformat(date_range['latest']).strftime('%Y-%m-%d')
                self.db_stats_labels['date_range'].config(text=f"{start} to {end}")
            else:
                self.db_stats_labels['date_range'].config(text="No data")
                
        except Exception as e:
            self.logger.error(f"Error loading database stats: {e}")
            
    def load_recent_activity(self):
        """Load recent activity"""
        try:
            # Get recent scans
            scans = self.db_manager.get_scan_history(limit=10)
            
            self.activity_text.delete(1.0, tk.END)
            
            if not scans:
                self.activity_text.insert(tk.END, "No recent activity found.\n")
                return
                
            for scan in scans:
                timestamp = datetime.fromisoformat(scan['timestamp'])
                date_str = timestamp.strftime('%Y-%m-%d %H:%M')
                
                activity = f"[{date_str}] {scan['scan_type'].title()} scan completed\n"
                activity += f"  Files: {scan['total_files_scanned']:,}, "
                activity += f"Size: {self.format_bytes(scan['total_size_scanned'])}, "
                activity += f"Duration: {scan['duration_seconds']:.1f}s\n"
                
                if scan['space_freed'] > 0:
                    activity += f"  Space freed: {self.format_bytes(scan['space_freed'])}\n"
                    
                if scan['files_deleted'] > 0:
                    activity += f"  Files deleted: {scan['files_deleted']:,}\n"
                    
                activity += f"  Status: {'✓ Success' if scan['success'] else '✗ Failed'}\n\n"
                
                self.activity_text.insert(tk.END, activity)
                
        except Exception as e:
            self.logger.error(f"Error loading recent activity: {e}")
            self.activity_text.delete(1.0, tk.END)
            self.activity_text.insert(tk.END, f"Error loading activity: {e}")
            
    def load_system_info(self):
        """Load system information"""
        try:
            # Clear existing widgets
            for widget in self.system_info_container.winfo_children():
                widget.destroy()
                
            # Get latest system snapshot
            snapshots = self.db_manager.get_system_snapshots(days=7)
            
            if not snapshots:
                ttk.Label(self.system_info_container, text="No system data available", 
                         style='Data.TLabel').pack()
                return
                
            latest = snapshots[0]
            
            # Display system info
            info_items = [
                ("Platform:", latest['platform_info'].get('system', 'Unknown')),
                ("Release:", latest['platform_info'].get('release', 'Unknown')),
                ("Total Disk Space:", self.format_bytes(latest['total_disk_space'])),
                ("Used Space:", self.format_bytes(latest['used_space'])),
                ("Free Space:", self.format_bytes(latest['free_space'])),
                ("Memory Usage:", f"{latest['memory_info'].get('percent', 0):.1f}%"),
            ]
            
            for i, (label, value) in enumerate(info_items):
                frame = ttk.Frame(self.system_info_container)
                frame.grid(row=i//2, column=i%2, sticky='w', padx=10, pady=5)
                
                ttk.Label(frame, text=label, style='Data.TLabel').pack(side='left')
                ttk.Label(frame, text=value, style='Data.TLabel', 
                         font=('SF Pro Text', 11, 'bold')).pack(side='left', padx=(10, 0))
                
        except Exception as e:
            self.logger.error(f"Error loading system info: {e}")
            
    def load_scan_history(self):
        """Load scan history"""
        try:
            limit = self.history_limit_var.get()
            limit = int(limit) if limit.isdigit() else 50
            
            scans = self.db_manager.get_scan_history(limit=limit)
            
            # Clear existing items
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
                
            # Add scans to tree
            for scan in scans:
                timestamp = datetime.fromisoformat(scan['timestamp'])
                date_str = timestamp.strftime('%Y-%m-%d %H:%M')
                
                values = (
                    date_str,
                    scan['scan_type'].title(),
                    f"{scan['total_files_scanned']:,}",
                    self.format_bytes(scan['total_size_scanned']),
                    f"{scan['duration_seconds']:.1f}s",
                    self.format_bytes(scan['space_freed']),
                    "✓ Success" if scan['success'] else "✗ Failed"
                )
                
                self.history_tree.insert('', 'end', values=values, tags=(scan['id'],))
                
        except Exception as e:
            self.logger.error(f"Error loading scan history: {e}")
            messagebox.showerror("Error", f"Failed to load scan history: {e}")
            
    def load_analytics(self):
        """Load analytics and create charts"""
        try:
            days = int(self.analytics_period_var.get())
            analytics = self.db_manager.get_analytics_summary(days=days)
            
            # Clear existing charts
            for widget in self.charts_frame.winfo_children():
                widget.destroy()
                
            if not analytics or 'scan_statistics' not in analytics:
                ttk.Label(self.charts_frame, text="No analytics data available", 
                         style='Data.TLabel').pack()
                return
                
            # Create charts
            self.create_analytics_charts(analytics)
            
        except Exception as e:
            self.logger.error(f"Error loading analytics: {e}")
            
    def create_analytics_charts(self, analytics):
        """Create analytics charts"""
        # Create figure with subplots
        fig = Figure(figsize=(12, 8), dpi=100)
        fig.patch.set_facecolor('white')
        
        # Daily scans chart
        if analytics.get('daily_scans'):
            ax1 = fig.add_subplot(2, 2, 1)
            daily_data = analytics['daily_scans']
            dates = [d['date'] for d in daily_data[:10]]  # Last 10 days
            counts = [d['scans'] for d in daily_data[:10]]
            
            ax1.bar(range(len(dates)), counts, color='#007AFF', alpha=0.7)
            ax1.set_title('Daily Scans (Last 10 days)', fontweight='bold')
            ax1.set_xlabel('Date')
            ax1.set_ylabel('Number of Scans')
            ax1.set_xticks(range(len(dates)))
            ax1.set_xticklabels([d[-5:] for d in dates], rotation=45)
            
        # Category breakdown chart
        if analytics.get('category_breakdown'):
            ax2 = fig.add_subplot(2, 2, 2)
            category_data = analytics['category_breakdown'][:8]  # Top 8 categories
            
            categories = [c['category'] for c in category_data]
            sizes = [c['total_size'] for c in category_data]
            
            ax2.pie(sizes, labels=categories, autopct='%1.1f%%', startangle=90)
            ax2.set_title('Space by Category', fontweight='bold')
            
        # Safety level chart
        if analytics.get('safety_breakdown'):
            ax3 = fig.add_subplot(2, 2, 3)
            safety_data = analytics['safety_breakdown']
            
            safety_levels = [s['safety_level'] for s in safety_data]
            counts = [s['count'] for s in safety_data]
            
            colors = {'critical': '#FF3B30', 'important': '#FF9500', 'moderate': '#FFCC00',
                     'safe': '#34C759', 'very_safe': '#30D158'}
            bar_colors = [colors.get(level, '#8E8E93') for level in safety_levels]
            
            ax3.bar(safety_levels, counts, color=bar_colors, alpha=0.7)
            ax3.set_title('Files by Safety Level', fontweight='bold')
            ax3.set_xlabel('Safety Level')
            ax3.set_ylabel('Number of Files')
            ax3.tick_params(axis='x', rotation=45)
            
        # Statistics text
        ax4 = fig.add_subplot(2, 2, 4)
        ax4.axis('off')
        
        stats = analytics['scan_statistics']
        stats_text = f"""
        Scan Statistics (Last {analytics['period_days']} days)
        
        Total Scans: {stats['total_scans'] or 0}
        Files Analyzed: {stats['total_files'] or 0:,}
        Size Processed: {self.format_bytes(stats['total_size'] or 0)}
        Space Freed: {self.format_bytes(stats['total_space_freed'] or 0)}
        Files Deleted: {stats['total_files_deleted'] or 0:,}
        Success Rate: {(stats['successful_scans'] or 0) / max(stats['total_scans'] or 1, 1) * 100:.1f}%
        Avg Duration: {stats['avg_duration'] or 0:.1f}s
        """
        
        ax4.text(0.1, 0.9, stats_text, transform=ax4.transAxes, fontsize=10,
                 verticalalignment='top', fontfamily='monospace')
        
        fig.tight_layout()
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.charts_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
    def load_top_consumers(self):
        """Load top space consumers"""
        try:
            days = int(self.consumers_period_var.get())
            limit = int(self.consumers_limit_var.get())
            
            consumers = self.db_manager.get_top_space_consumers(days=days, limit=limit)
            
            # Clear existing items
            for item in self.consumers_tree.get_children():
                self.consumers_tree.delete(item)
                
            # Add consumers to tree
            for consumer in consumers:
                modified = datetime.fromisoformat(consumer['modified_time']).strftime('%Y-%m-%d %H:%M')
                
                values = (
                    consumer['file_path'],
                    consumer['file_name'],
                    self.format_bytes(consumer['file_size']),
                    consumer['safety_level'].title(),
                    consumer['category'],
                    consumer['recommendation'].title(),
                    modified
                )
                
                self.consumers_tree.insert('', 'end', values=values)
                
        except Exception as e:
            self.logger.error(f"Error loading top consumers: {e}")
            messagebox.showerror("Error", f"Failed to load top consumers: {e}")
            
    def show_scan_details(self, event):
        """Show detailed scan information"""
        selection = self.history_tree.selection()
        if not selection:
            return
            
        item = self.history_tree.item(selection[0])
        tags = item.get('tags', [])
        
        if not tags:
            return
            
        scan_id = tags[0]
        
        try:
            details = self.db_manager.get_scan_details(scan_id)
            
            if 'error' in details:
                messagebox.showerror("Error", details['error'])
                return
                
            # Create details window
            self.create_details_window(details)
            
        except Exception as e:
            self.logger.error(f"Error showing scan details: {e}")
            messagebox.showerror("Error", f"Failed to load scan details: {e}")
            
    def create_details_window(self, details):
        """Create scan details window"""
        window = tk.Toplevel(self.root)
        window.title(f"Scan Details - {details['timestamp']}")
        window.geometry("800x600")
        
        # Create notebook for tabs
        notebook = ttk.Notebook(window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Summary tab
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text="Summary")
        
        summary_text = scrolledtext.ScrolledText(summary_frame, wrap='word', font=('SF Mono', 10))
        summary_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Format summary
        summary = f"""
Scan ID: {details['id']}
Timestamp: {details['timestamp']}
Scan Type: {details['scan_type']}
Success: {'Yes' if details['success'] else 'No'}

Files Scanned: {details['total_files_scanned']:,}
Total Size: {self.format_bytes(details['total_size_scanned'])}
Duration: {details['duration_seconds']:.1f} seconds
Space Freed: {self.format_bytes(details['space_freed'])}
Files Deleted: {details['files_deleted']:,}
Errors: {details['errors_count']}

Categories Scanned: {', '.join(details['categories_scanned'])}

Scan Summary:
{json.dumps(details['scan_summary'], indent=2)}
        """
        
        summary_text.insert(tk.END, summary)
        summary_text.config(state='disabled')
        
        # Files tab
        files_frame = ttk.Frame(notebook)
        notebook.add(files_frame, text="Files")
        
        # Files treeview
        tree_frame = ttk.Frame(files_frame)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        columns = ('Path', 'Name', 'Size', 'Safety', 'Category', 'Recommendation')
        files_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        
        for col in columns:
            files_tree.heading(col, text=col)
            files_tree.column(col, width=120)
            
        # Add files
        for file_record in details.get('file_records', [])[:100]:  # Limit to 100 files
            values = (
                file_record['file_path'],
                file_record['file_name'],
                self.format_bytes(file_record['file_size']),
                file_record['safety_level'],
                file_record['category'],
                file_record['recommendation']
            )
            files_tree.insert('', 'end', values=values)
            
        files_tree.pack(fill='both', expand=True)
        
    def format_bytes(self, bytes_count):
        """Format bytes into human readable string"""
        if not bytes_count:
            return "0 B"
            
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} PB"
        
    def run(self):
        """Run the GUI"""
        self.root.mainloop()


def main():
    """Main entry point"""
    try:
        app = AnalyticsGUI()
        app.run()
    except Exception as e:
        print(f"Error starting Analytics GUI: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
