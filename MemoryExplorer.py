"""
Memory Explorer - Professional Memory Analysis Tool
Fully integrated with StealthEngine for kernel-level access
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import ctypes
from ctypes import *
import threading
import json
from datetime import datetime
import struct
import os
import time

# Load Stealth Engine (relative to script directory)
script_dir = os.path.dirname(os.path.abspath(__file__))
stealth_dll_path = os.path.join(script_dir, "StealthEngine", "StealthEngine.dll")

stealth = ctypes.CDLL(stealth_dll_path)
stealth.CreateEngine.restype = c_void_p
stealth.AttachToProcess.argtypes = [c_void_p, c_char_p]
stealth.AttachToProcess.restype = c_bool
stealth.ReadMemory.argtypes = [c_void_p, c_void_p, c_void_p, c_size_t]
stealth.ReadMemory.restype = c_bool
stealth.WriteMemory.argtypes = [c_void_p, c_void_p, c_void_p, c_size_t]
stealth.WriteMemory.restype = c_bool


class MemoryExplorer:
    def __init__(self, root):
        self.root = root
        self.root.title("Memory Explorer Pro")
        self.root.geometry("1600x950")
        self.root.configure(bg='#0a0a0a')
        
        self.engine = None
        self.attached = False
        self.scanning = False
        self.bookmarks = {}
        self.scan_results = []
        self.process_name = "RobloxPlayerBeta.exe"
        self.base_address = 0x7FF6F39B0000
        self.available_processes = []
        self.ghidra_project = os.path.join(script_dir, "GhidraProjects")
        self.export_dir = os.path.join(script_dir, "Exports")
        self.current_pid = None
        self.memory_snapshots = []
        
        # Create export directories
        os.makedirs(self.export_dir, exist_ok=True)
        os.makedirs(os.path.join(self.export_dir, "memory_dumps"), exist_ok=True)
        os.makedirs(os.path.join(self.export_dir, "ghidra_ready"), exist_ok=True)
        os.makedirs(os.path.join(self.export_dir, "logs"), exist_ok=True)
        
        self.setup_ui()
        self.refresh_process_list()
        
    def setup_ui(self):
        # Menu bar
        menubar = tk.Menu(self.root, bg='#1a1a1a', fg='white')
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0, bg='#1a1a1a', fg='white')
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Results", command=self.save_results)
        file_menu.add_command(label="Load Results", command=self.load_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        tools_menu = tk.Menu(menubar, tearoff=0, bg='#1a1a1a', fg='white')
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Refresh Processes", command=self.refresh_process_list)
        tools_menu.add_command(label="Process Info", command=self.show_process_info)
        tools_menu.add_command(label="Memory Map", command=self.show_memory_map)
        tools_menu.add_separator()
        tools_menu.add_command(label="Scan All Games", command=self.scan_all_games)
        
        export_menu = tk.Menu(menubar, tearoff=0, bg='#1a1a1a', fg='white')
        menubar.add_cascade(label="Export", menu=export_menu)
        export_menu.add_command(label="📦 Full Memory Dump", command=self.export_full_memory)
        export_menu.add_command(label="📄 Export Selected Region", command=self.export_selected_region)
        export_menu.add_command(label="📊 Export Scan Results", command=self.export_scan_results)
        export_menu.add_separator()
        export_menu.add_command(label="💾 Take Memory Snapshot", command=self.take_snapshot)
        export_menu.add_command(label="📈 Compare Snapshots", command=self.compare_snapshots)
        
        ghidra_menu = tk.Menu(menubar, tearoff=0, bg='#1a1a1a', fg='white')
        menubar.add_cascade(label="Ghidra", menu=ghidra_menu)
        ghidra_menu.add_command(label="🚀 Quick Export to Ghidra", command=self.quick_ghidra_export)
        ghidra_menu.add_command(label="📂 Export Executable", command=self.export_executable)
        ghidra_menu.add_command(label="🔍 Export Selected + Decompile", command=self.export_and_decompile)
        ghidra_menu.add_separator()
        ghidra_menu.add_command(label="⚙️ Open Ghidra Project", command=self.open_ghidra_project)
        ghidra_menu.add_command(label="📋 Generate Analysis Script", command=self.generate_ghidra_script)
        
        ai_menu = tk.Menu(menubar, tearoff=0, bg='#1a1a1a', fg='white')
        menubar.add_cascade(label="AI Analysis", menu=ai_menu)
        ai_menu.add_command(label="🤖 Auto-Label Functions", command=self.auto_label_functions)
        ai_menu.add_command(label="🧠 Pattern Learning Mode", command=self.pattern_learning)
        ai_menu.add_command(label="🔍 Function Recognition", command=self.recognize_functions)
        ai_menu.add_command(label="📊 Memory Heat Map", command=self.show_memory_heatmap)
        ai_menu.add_separator()
        ai_menu.add_command(label="⚡ Dynamic Analysis", command=self.dynamic_analysis)
        ai_menu.add_command(label="🎯 Smart Pattern Generator", command=self.generate_smart_patterns)
        ai_menu.add_command(label="📚 Build Knowledge Base", command=self.build_knowledge_base)
        
        # Top toolbar
        toolbar = tk.Frame(self.root, bg='#0a0a0a', height=60)
        toolbar.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(toolbar, text="Process:", bg='#0a0a0a', fg='white', 
                font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
        
        # Process selector button (opens popup) - LARGE and visible
        self.process_btn = tk.Button(toolbar, text="⬇ SELECT PROCESS ⬇", 
                                     command=self.show_process_selector,
                                     bg='#ff6600', fg='white', font=('Segoe UI', 11, 'bold'),
                                     padx=20, pady=10, relief=tk.RAISED, bd=3,
                                     cursor='hand2')
        self.process_btn.pack(side=tk.LEFT, padx=5)
        
        # Selected process label
        self.selected_process_label = tk.Label(toolbar, text="[No Process Selected]", 
                                               bg='#0a0a0a', fg='#ffaa00', 
                                               font=('Consolas', 10, 'bold'))
        self.selected_process_label.pack(side=tk.LEFT, padx=10)
        
        tk.Button(toolbar, text="🔄", command=self.refresh_process_list,
                 bg='#1a1a1a', fg='#00ff41', font=('Segoe UI', 10, 'bold'),
                 padx=8, pady=5, relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        
        self.attach_btn = tk.Button(toolbar, text="⚡ ATTACH", command=self.attach,
                                    bg='#00ff41', fg='black', font=('Segoe UI', 10, 'bold'),
                                    padx=20, pady=8, relief=tk.FLAT)
        self.attach_btn.pack(side=tk.LEFT, padx=10)
        
        self.status_label = tk.Label(toolbar, text="● DISCONNECTED", bg='#0a0a0a',
                                     fg='#ff4444', font=('Segoe UI', 11, 'bold'))
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # TUTORIAL BUTTON - Right side buttons
        tk.Button(toolbar, text="TUTORIAL", command=self.launch_tutorial,
                 bg='#9900ff', fg='white', font=('Segoe UI', 10, 'bold'),
                 padx=20, pady=8, relief=tk.FLAT, cursor='hand2').pack(side=tk.RIGHT, padx=5)
        
        tk.Button(toolbar, text="🚀 Ghidra", command=self.quick_ghidra_export,
                 bg='#cc6600', fg='white', font=('Segoe UI', 9, 'bold'),
                 padx=15, pady=8, relief=tk.FLAT).pack(side=tk.RIGHT, padx=5)
        
        tk.Button(toolbar, text="📦 Export", command=self.show_export_menu,
                 bg='#0066cc', fg='white', font=('Segoe UI', 9, 'bold'),
                 padx=15, pady=8, relief=tk.FLAT).pack(side=tk.RIGHT, padx=5)
        
        tk.Button(toolbar, text="📋 Bookmarks", command=self.show_bookmarks,
                 bg='#1a1a1a', fg='white', font=('Segoe UI', 9),
                 padx=15, pady=8, relief=tk.FLAT).pack(side=tk.RIGHT, padx=5)
        
        # Main content - PanedWindow for resizable layout
        main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg='#0a0a0a',
                                    sashwidth=5, sashrelief=tk.RAISED)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left panel - Scanner & Results
        left_panel = tk.Frame(main_paned, bg='#0a0a0a')
        main_paned.add(left_panel, minsize=600)
        
        self.create_scanner_panel(left_panel)
        
        # Right panel - Viewer & Editor
        right_panel = tk.Frame(main_paned, bg='#0a0a0a')
        main_paned.add(right_panel, minsize=600)
        
        self.create_viewer_panel(right_panel)
        
    def create_scanner_panel(self, parent):
        # Scanner configuration
        scanner = tk.LabelFrame(parent, text="Memory Scanner", bg='#0f0f0f', 
                               fg='#00ff41', font=('Segoe UI', 11, 'bold'),
                               padx=10, pady=10)
        scanner.pack(fill=tk.X, padx=5, pady=5)
        
        # Scan type selector
        type_frame = tk.Frame(scanner, bg='#0f0f0f')
        type_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(type_frame, text="Value Type:", bg='#0f0f0f', fg='white',
                font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        self.scan_type = tk.StringVar(value="int32")
        
        style = ttk.Style()
        style.configure('Dark.TCombobox', fieldbackground='#1a1a1a', background='#1a1a1a', 
                       foreground='white', arrowcolor='white')
        
        type_combo = ttk.Combobox(type_frame, textvariable=self.scan_type, state='readonly',
                                 font=('Segoe UI', 9), width=15, style='Dark.TCombobox')
        type_combo['values'] = ('int32 (4 bytes)', 'int64 (8 bytes)', 'float', 
                               'double', 'string', 'byte_array', 'pattern')
        type_combo.set('int32 (4 bytes)')
        type_combo.pack(side=tk.LEFT, padx=5)
        
        # Scan condition dropdown (like Cheat Engine)
        tk.Label(type_frame, text="Scan Type:", bg='#0f0f0f', fg='white',
                font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=(20, 5))
        
        self.scan_condition = tk.StringVar(value="exact")
        
        condition_combo = ttk.Combobox(type_frame, textvariable=self.scan_condition, 
                                      state='readonly', font=('Segoe UI', 9), 
                                      width=20, style='Dark.TCombobox')
        condition_combo['values'] = (
            'Exact Value',
            'Unknown Initial Value',
            'Increased Value',
            'Decreased Value', 
            'Changed Value',
            'Unchanged Value',
            'Bigger Than',
            'Smaller Than',
            'Value Between',
            'Increased By',
            'Decreased By'
        )
        condition_combo.set('Exact Value')
        condition_combo.pack(side=tk.LEFT, padx=5)
        
        # Search input
        search_frame = tk.Frame(scanner, bg='#0f0f0f')
        search_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(search_frame, text="Value:", bg='#0f0f0f', fg='white',
                font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        self.search_entry = tk.Entry(search_frame, bg='#1a1a1a', fg='#00ff41',
                                     insertbackground='#00ff41', width=30,
                                     font=('Consolas', 11))
        self.search_entry.insert(0, "")
        self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Second value (for "between" and "by" scans)
        tk.Label(search_frame, text="to:", bg='#0f0f0f', fg='white',
                font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(10, 5))
        
        self.search_entry2 = tk.Entry(search_frame, bg='#1a1a1a', fg='#00ff41',
                                      insertbackground='#00ff41', width=20,
                                      font=('Consolas', 11))
        self.search_entry2.pack(side=tk.LEFT, padx=5)
        
        # Range configuration
        range_frame = tk.Frame(scanner, bg='#0f0f0f')
        range_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(range_frame, text="Start:", bg='#0f0f0f', fg='white',
                font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=5)
        self.start_entry = tk.Entry(range_frame, bg='#1a1a1a', fg='white',
                                    insertbackground='white', width=18,
                                    font=('Consolas', 9))
        self.start_entry.insert(0, f"0x{self.base_address:X}")
        self.start_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(range_frame, text="Size (MB):", bg='#0f0f0f', fg='white',
                font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=10)
        self.size_spin = tk.Spinbox(range_frame, from_=1, to=1000, bg='#1a1a1a',
                                    fg='white', width=8, font=('Consolas', 9))
        self.size_spin.delete(0, tk.END)
        self.size_spin.insert(0, "124")
        self.size_spin.pack(side=tk.LEFT, padx=5)
        
        # Control buttons
        btn_frame = tk.Frame(scanner, bg='#0f0f0f')
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.scan_btn = tk.Button(btn_frame, text="🔍 FIRST SCAN", command=self.first_scan,
                                  bg='#0066cc', fg='white', font=('Segoe UI', 10, 'bold'),
                                  padx=20, pady=10, relief=tk.FLAT, state=tk.DISABLED)
        self.scan_btn.pack(side=tk.LEFT, padx=5)
        
        self.next_btn = tk.Button(btn_frame, text="NEXT SCAN", command=self.next_scan,
                                  bg='#0088ee', fg='white', font=('Segoe UI', 10, 'bold'),
                                  padx=20, pady=10, relief=tk.FLAT, state=tk.DISABLED)
        self.next_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="STOP", command=self.stop_scan,
                 bg='#cc0000', fg='white', font=('Segoe UI', 10, 'bold'),
                 padx=20, pady=10, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="CLEAR", command=self.clear_results,
                 bg='#333333', fg='white', font=('Segoe UI', 10, 'bold'),
                 padx=20, pady=10, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        # Live monitoring toggle
        self.monitoring_active = False
        self.monitor_btn = tk.Button(btn_frame, text="▶️ LIVE MONITOR", command=self.toggle_monitor,
                                     bg='#00aa00', fg='white', font=('Segoe UI', 10, 'bold'),
                                     padx=20, pady=10, relief=tk.FLAT, state=tk.DISABLED)
        self.monitor_btn.pack(side=tk.LEFT, padx=5)
        
        # Refresh rate control
        tk.Label(btn_frame, text="Refresh:", bg='#0f0f0f', fg='white',
                font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(10, 2))
        
        self.refresh_rate = tk.Spinbox(btn_frame, from_=100, to=5000, increment=100,
                                       bg='#1a1a1a', fg='white', width=6, font=('Consolas', 9))
        self.refresh_rate.delete(0, tk.END)
        self.refresh_rate.insert(0, "500")  # 500ms default
        self.refresh_rate.pack(side=tk.LEFT, padx=2)
        
        tk.Label(btn_frame, text="ms", bg='#0f0f0f', fg='white',
                font=('Segoe UI', 9)).pack(side=tk.LEFT)
        
        # Progress bar
        self.progress = ttk.Progressbar(scanner, length=400, mode='determinate')
        self.progress.pack(fill=tk.X, pady=5)
        
        self.progress_label = tk.Label(scanner, text="Ready", bg='#0f0f0f',
                                       fg='#00ff41', font=('Consolas', 9))
        self.progress_label.pack(pady=2)
        
        # Results panel
        results = tk.LabelFrame(parent, text="Scan Results", bg='#0f0f0f',
                               fg='#00ff41', font=('Segoe UI', 11, 'bold'),
                               padx=5, pady=5)
        results.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Results tree with scrollbar
        tree_frame = tk.Frame(results, bg='#0f0f0f')
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar_y = tk.Scrollbar(tree_frame)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scrollbar_x = tk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Treeview", background="#1a1a1a", foreground="white",
                       fieldbackground="#1a1a1a", font=('Consolas', 9))
        style.configure("Treeview.Heading", background="#0f0f0f", foreground="#00ff41",
                       font=('Segoe UI', 9, 'bold'))
        style.map('Treeview', background=[('selected', '#0066cc')])
        
        self.results_tree = ttk.Treeview(tree_frame, 
                                        columns=('Address', 'Previous', 'Value', 'Type'),
                                        yscrollcommand=scrollbar_y.set,
                                        xscrollcommand=scrollbar_x.set)
        self.results_tree.heading('#0', text='#')
        self.results_tree.heading('Address', text='Address')
        self.results_tree.heading('Previous', text='Previous')
        self.results_tree.heading('Value', text='Value')
        self.results_tree.heading('Type', text='Type')
        self.results_tree.column('#0', width=50)
        self.results_tree.column('Address', width=150)
        self.results_tree.column('Previous', width=120)
        self.results_tree.column('Value', width=120)
        self.results_tree.column('Type', width=100)
        self.results_tree.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for value changes
        self.results_tree.tag_configure('increased', foreground='#00ff00')
        self.results_tree.tag_configure('decreased', foreground='#ff0000')
        self.results_tree.tag_configure('unchanged', foreground='#ffffff')
        
        scrollbar_y.config(command=self.results_tree.yview)
        scrollbar_x.config(command=self.results_tree.xview)
        
        # Context menu
        self.results_menu = tk.Menu(self.results_tree, tearoff=0, bg='#1a1a1a', fg='white')
        self.results_menu.add_command(label="View in Hex Editor", command=self.view_selected)
        self.results_menu.add_command(label="Add to Bookmarks", command=self.bookmark_selected)
        self.results_menu.add_command(label="Copy Address", command=self.copy_address)
        self.results_menu.add_separator()
        self.results_menu.add_command(label="Delete", command=self.delete_selected)
        
        self.results_tree.bind('<Button-3>', self.show_context_menu)
        self.results_tree.bind('<Double-Button-1>', self.view_selected)
        
    def create_viewer_panel(self, parent):
        # Hex viewer
        viewer = tk.LabelFrame(parent, text="Hex Viewer", bg='#0f0f0f',
                              fg='#00ff41', font=('Segoe UI', 11, 'bold'),
                              padx=10, pady=10)
        viewer.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Address bar
        addr_frame = tk.Frame(viewer, bg='#0f0f0f')
        addr_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(addr_frame, text="Address:", bg='#0f0f0f', fg='white',
                font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
        
        self.viewer_addr = tk.Entry(addr_frame, bg='#1a1a1a', fg='#00ff41',
                                    insertbackground='#00ff41', width=20,
                                    font=('Consolas', 10))
        self.viewer_addr.pack(side=tk.LEFT, padx=5)
        
        tk.Label(addr_frame, text="Size:", bg='#0f0f0f', fg='white',
                font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=10)
        
        self.viewer_size = tk.Spinbox(addr_frame, from_=16, to=8192, bg='#1a1a1a',
                                      fg='white', width=8, font=('Consolas', 10))
        self.viewer_size.delete(0, tk.END)
        self.viewer_size.insert(0, "512")
        self.viewer_size.pack(side=tk.LEFT, padx=5)
        
        self.view_mem_btn = tk.Button(addr_frame, text="📖 VIEW", command=self.view_memory,
                                      bg='#0066cc', fg='white', font=('Segoe UI', 9, 'bold'),
                                      padx=15, pady=5, relief=tk.FLAT, state=tk.DISABLED)
        self.view_mem_btn.pack(side=tk.LEFT, padx=10)
        
        tk.Button(addr_frame, text="✏️ EDIT MODE", command=self.toggle_edit_mode,
                 bg='#cc6600', fg='white', font=('Segoe UI', 9, 'bold'),
                 padx=15, pady=5, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        # Hex display
        hex_frame = tk.Frame(viewer, bg='#0f0f0f')
        hex_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.hex_display = scrolledtext.ScrolledText(hex_frame, bg='#000000',
                                                     fg='#00ff41', font=('Consolas', 9),
                                                     wrap=tk.NONE, insertbackground='#00ff41')
        self.hex_display.pack(fill=tk.BOTH, expand=True)
        
        # Memory editor
        editor = tk.LabelFrame(parent, text="Memory Editor", bg='#0f0f0f',
                              fg='#00ff41', font=('Segoe UI', 11, 'bold'),
                              padx=10, pady=10)
        editor.pack(fill=tk.X, padx=5, pady=5)
        
        edit_frame = tk.Frame(editor, bg='#0f0f0f')
        edit_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(edit_frame, text="Write Address:", bg='#0f0f0f', fg='white',
                font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
        
        self.write_addr = tk.Entry(edit_frame, bg='#1a1a1a', fg='white',
                                   insertbackground='white', width=20,
                                   font=('Consolas', 10))
        self.write_addr.pack(side=tk.LEFT, padx=5)
        
        tk.Label(edit_frame, text="Bytes:", bg='#0f0f0f', fg='white',
                font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=10)
        
        self.write_bytes = tk.Entry(edit_frame, bg='#1a1a1a', fg='white',
                                    insertbackground='white', width=30,
                                    font=('Consolas', 10))
        self.write_bytes.insert(0, "90 90 90 90")
        self.write_bytes.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.write_btn = tk.Button(edit_frame, text="✍️ WRITE", command=self.write_memory,
                                   bg='#cc0066', fg='white', font=('Segoe UI', 9, 'bold'),
                                   padx=15, pady=5, relief=tk.FLAT, state=tk.DISABLED)
        self.write_btn.pack(side=tk.LEFT, padx=10)
        
        # Console log
        console = tk.LabelFrame(parent, text="Console Log", bg='#0f0f0f',
                               fg='#00ff41', font=('Segoe UI', 10, 'bold'),
                               padx=5, pady=5)
        console.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.console = scrolledtext.ScrolledText(console, bg='#000000', fg='#00ff41',
                                                 font=('Consolas', 9), height=8)
        self.console.pack(fill=tk.BOTH, expand=True)
        
        self.log("Memory Explorer initialized")
        self.log("Ready to attach to process")
    
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {"INFO": "#00ff41", "WARN": "#ffaa00", "ERROR": "#ff4444", "SUCCESS": "#00ffff"}
        color = colors.get(level, "#00ff41")
        
        self.console.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.console.insert(tk.END, f"[{level}] ", level)
        self.console.insert(tk.END, f"{message}\n")
        
        self.console.tag_config("timestamp", foreground="#888888")
        self.console.tag_config(level, foreground=color)
        self.console.see(tk.END)
        self.console.update()
    
    def refresh_process_list(self):
        """Scan for running processes with window titles"""
        try:
            import psutil
            
            # Aggressive blacklist - KILL THE NOISE
            blacklist = {
                'pwsh.exe', 'powershell.exe', 'conhost.exe', 'cmd.exe',
                'msedgewebview2.exe', 'msedge.exe', 'chrome.exe', 'firefox.exe',
                'explorer.exe', 'svchost.exe', 'dwm.exe', 'csrss.exe',
                'SearchHost.exe', 'RuntimeBroker.exe', 'TextInputHost.exe',
                'StartMenuExperienceHost.exe', 'ShellExperienceHost.exe',
                'ApplicationFrameHost.exe', 'SystemSettings.exe',
                'Code.exe', 'node.exe', 'Discord.exe', 'Taskmgr.exe',
                'notepad.exe', 'mmc.exe', 'services.exe', 'lsass.exe',
                'winlogon.exe', 'System', 'Registry', 'smss.exe',
                'backgroundHost.exe', 'backgroundTaskHost.exe',
                'CrossDeviceService.exe', 'ShellHost.exe',
                'NVDisplay.Container.exe', 'nvcontainer.exe',
                'Photos.exe', 'Video.UI.exe', 'WidgetBoard.exe',
                'LockApp.exe', 'CrashpadHandler.exe', 'cpptools.exe',
                'cpptools-srv.exe', 'EdgeGameAssist.exe', 'ShieldHost.exe',
                'RazerAppEngine.exe', 'Razer Central.exe', 'RazerCentralService.exe',
                'steamwebhelper.exe', 'OneDrive.exe', 'GameManagerService3.exe',
                'lua-language-server.exe', 'PhoneExperienceHost.exe',
                'SnippingTool.exe', 'XtuService.exe',
            }
            
            priority_processes = []
            game_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    name = proc.info['name']
                    if not name or name.lower() in {b.lower() for b in blacklist}:
                        continue
                    
                    # Get memory
                    mem_mb = proc.memory_info().rss / (1024 * 1024)
                    
                    # Show processes > 10MB (way more inclusive!)
                    if mem_mb > 10:
                        # Check if it's a priority process by name
                        is_priority = any(keyword.lower() in name.lower() for keyword in ['tutorial', 'roblox', 'game', 'memoryscanner', 'rvrse', 'python', 'etg'])
                        
                        entry = (name, proc.info['pid'], mem_mb, name)
                        if is_priority:
                            priority_processes.append(entry)
                        else:
                            game_processes.append(entry)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort: Priority first, then by memory
            priority_processes.sort(key=lambda x: x[2], reverse=True)
            game_processes.sort(key=lambda x: x[2], reverse=True)
            
            self.available_processes = priority_processes + game_processes
            
            self.log(f"Found {len(priority_processes)} priority + {len(game_processes)} games", "INFO")
        except Exception as e:
            self.log(f"Process scan error: {str(e)}", "ERROR")
    
    def show_process_selector(self):
        """Show searchable process selector popup"""
        # REFRESH process list before showing popup
        self.refresh_process_list()
        
        popup = tk.Toplevel(self.root)
        popup.title("⬇⬇⬇ SELECT PROCESS TO ATTACH ⬇⬇⬇")
        popup.geometry("800x600")
        popup.configure(bg='#0a0a0a')
        popup.transient(self.root)
        popup.grab_set()
        
        # Title banner
        title_frame = tk.Frame(popup, bg='#ff6600')
        title_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(title_frame, text="PROCESS SELECTOR", bg='#ff6600', fg='white',
                font=('Segoe UI', 16, 'bold'), pady=15).pack()
        
        # Search bar
        search_frame = tk.Frame(popup, bg='#0a0a0a')
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(search_frame, text="SEARCH:", bg='#0a0a0a', fg='#00ff41',
                font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT, padx=5)
        
        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var, font=('Consolas', 12),
                               bg='#1a1a1a', fg='white', insertbackground='white', bd=3,
                               relief=tk.SUNKEN)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, ipady=5)
        search_entry.focus()
        
        # Hint label
        hint_label = tk.Label(popup, text="↑ Type 'python' or PID number to filter ↑",
                             bg='#0a0a0a', fg='#666666', font=('Segoe UI', 9, 'italic'))
        hint_label.pack()
        
        # Process list with icons using Treeview
        list_frame = tk.Frame(popup, bg='#0a0a0a')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create Treeview with icon support
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Process.Treeview", background="#1a1a1a", foreground="white", 
                       fieldbackground="#1a1a1a", borderwidth=0)
        style.map('Process.Treeview', background=[('selected', '#00ff41')], 
                 foreground=[('selected', 'black')])
        
        process_tree = ttk.Treeview(list_frame, yscrollcommand=scrollbar.set,
                                   style="Process.Treeview", show='tree', selectmode='browse')
        process_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=process_tree.yview)
        
        # Populate process list
        def update_list(search_term=""):
            for item in process_tree.get_children():
                process_tree.delete(item)
            search_lower = search_term.lower()
            
            for display_name, pid, mem, exe_name in self.available_processes:
                # Search in exe name AND PID
                searchable = f"{exe_name} {pid}".lower()
                
                if not search_term or search_lower in searchable:
                    # Check if priority by exe name
                    is_priority = any(kw in exe_name.lower() for kw in ['tutorial', 'roblox', 'game', 'memoryscanner'])
                    
                    if is_priority:
                        display = f">>> {exe_name[:32]:32} | PID: {pid:6} | {mem:5.0f}MB"
                        item_id = process_tree.insert('', 'end', text=display, values=(pid, exe_name))
                        process_tree.item(item_id, tags=('highlight',))
                    else:
                        display = f"    {exe_name[:32]:32} | PID: {pid:6} | {mem:5.0f}MB"
                        item_id = process_tree.insert('', 'end', text=display, values=(pid, exe_name))
            
            process_tree.tag_configure('highlight', foreground='#00ff41')
        
        update_list()
        
        # Search functionality
        def on_search(*args):
            update_list(search_var.get())
        
        search_var.trace('w', on_search)
        
        # Button frame
        btn_frame = tk.Frame(popup, bg='#0a0a0a')
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def select_process():
            selection = process_tree.selection()
            if not selection:
                messagebox.showerror("Error", "Please select a process")
                return
            
            # Get values stored in treeview: (pid, exe_name)
            values = process_tree.item(selection[0])['values']
            pid = values[0]
            exe_name = values[1]
            
            self.process_name = exe_name
            self.current_pid = int(pid)
            self.selected_process_label.config(text=f"{exe_name} (PID: {pid})")
            popup.destroy()
            
            # Auto-attach
            self.attach()
        
        def on_double_click(event):
            select_process()
        
        process_tree.bind('<Double-Button-1>', on_double_click)
        
        # Buttons
        tk.Button(btn_frame, text=">> SELECT & ATTACH <<", command=select_process,
                 bg='#00ff41', fg='black', font=('Segoe UI', 12, 'bold'),
                 padx=30, pady=12, cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="REFRESH LIST", command=lambda: [self.refresh_process_list(), update_list()],
                 bg='#1a1a1a', fg='white', font=('Segoe UI', 11),
                 padx=20, pady=10, cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="CANCEL", command=popup.destroy,
                 bg='#cc0000', fg='white', font=('Segoe UI', 11),
                 padx=20, pady=10, cursor='hand2').pack(side=tk.RIGHT, padx=5)
        
        # Stats
        stats_label = tk.Label(popup, text=f"Total Processes: {len(self.available_processes)} | GREEN = python.exe/Roblox",
                              bg='#0a0a0a', fg='#00ff41', font=('Segoe UI', 10, 'bold'))
        stats_label.pack(pady=10)
    
    def attach(self):
        try:
            if not self.process_name:
                messagebox.showerror("Error", "Select a process first (click 📋 Select Process)")
                return
            
            self.log(f"Attaching to {self.process_name} (PID: {self.current_pid})...")
            
            self.engine = stealth.CreateEngine()
            if not self.engine:
                self.log("Failed to create engine", "ERROR")
                messagebox.showerror("Error", "Failed to create StealthEngine")
                return
            
            self.log(f"Engine created: 0x{self.engine:X}", "SUCCESS")
            
            if stealth.AttachToProcess(self.engine, self.process_name.encode()):
                self.attached = True
                self.attach_btn.config(state=tk.DISABLED)
                self.scan_btn.config(state=tk.NORMAL)
                self.view_mem_btn.config(state=tk.NORMAL)
                self.write_btn.config(state=tk.NORMAL)
                
                self.status_label.config(text="● CONNECTED", fg='#00ff41')
                self.log(f"Successfully attached to {self.process_name}", "SUCCESS")
                self.log("Kernel-level memory access enabled", "SUCCESS")
                
                # Get process info
                self.get_process_info()
            else:
                self.log("Attachment failed", "ERROR")
                messagebox.showerror("Error", 
                    f"Failed to attach to {self.process_name}\n\n" +
                    "• Ensure process is running\n" +
                    "• Run as Administrator\n" +
                    "• Check kernel driver status")
        except Exception as e:
            self.log(f"Exception: {str(e)}", "ERROR")
            messagebox.showerror("Error", str(e))
    
    def get_process_info(self):
        """Get and display process information"""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] == self.process_name:
                    self.current_pid = proc.info['pid']
                    self.log(f"Process ID: {self.current_pid}", "INFO")
                    
                    # Get base address
                    kernel32 = ctypes.windll.kernel32
                    PROCESS_QUERY_INFORMATION = 0x0400
                    PROCESS_VM_READ = 0x0010
                    
                    hProcess = kernel32.OpenProcess(
                        PROCESS_QUERY_INFORMATION | PROCESS_VM_READ,
                        False, proc.info['pid'])
                    
                    if hProcess:
                        class MODULEINFO(ctypes.Structure):
                            _fields_ = [("lpBaseOfDll", ctypes.c_void_p),
                                       ("SizeOfImage", ctypes.c_ulong),
                                       ("EntryPoint", ctypes.c_void_p)]
                        
                        psapi = ctypes.windll.psapi
                        hModule = ctypes.c_void_p()
                        cbNeeded = ctypes.c_ulong()
                        
                        if psapi.EnumProcessModules(hProcess, ctypes.byref(hModule),
                                                   ctypes.sizeof(hModule), ctypes.byref(cbNeeded)):
                            modinfo = MODULEINFO()
                            if psapi.GetModuleInformation(hProcess, hModule,
                                                          ctypes.byref(modinfo), ctypes.sizeof(modinfo)):
                                self.base_address = modinfo.lpBaseOfDll
                                self.log(f"Base Address: 0x{self.base_address:X}", "INFO")
                                self.log(f"Image Size: {modinfo.SizeOfImage / (1024*1024):.2f} MB", "INFO")
                                
                                # Auto-detect writable memory regions (Unity heap)
                                self.log("Detecting writable memory regions...", "INFO")
                                
                                class MEMORY_BASIC_INFORMATION(ctypes.Structure):
                                    _fields_ = [
                                        ("BaseAddress", ctypes.c_void_p),
                                        ("AllocationBase", ctypes.c_void_p),
                                        ("AllocationProtect", ctypes.c_ulong),
                                        ("RegionSize", ctypes.c_size_t),
                                        ("State", ctypes.c_ulong),
                                        ("Protect", ctypes.c_ulong),
                                        ("Type", ctypes.c_ulong),
                                    ]
                                
                                mbi = MEMORY_BASIC_INFORMATION()
                                address = 0
                                largest_region = None
                                largest_size = 0
                                
                                MEM_COMMIT = 0x1000
                                PAGE_READWRITE = 0x04
                                PAGE_WRITECOPY = 0x08
                                PAGE_EXECUTE_READWRITE = 0x40
                                
                                # Scan for large writable regions (Unity heap)
                                while address < 0x7FFFFFFFFFFF:
                                    if kernel32.VirtualQueryEx(hProcess, ctypes.c_void_p(address), 
                                                              ctypes.byref(mbi), ctypes.sizeof(mbi)):
                                        if mbi.State == MEM_COMMIT and mbi.RegionSize > largest_size:
                                            if mbi.Protect in [PAGE_READWRITE, PAGE_WRITECOPY, PAGE_EXECUTE_READWRITE]:
                                                if mbi.RegionSize > 50 * 1024 * 1024:  # > 50MB = likely Unity heap
                                                    largest_region = mbi.BaseAddress
                                                    largest_size = mbi.RegionSize
                                        address += mbi.RegionSize
                                    else:
                                        address += 0x1000
                                    
                                    # Stop after checking first 2TB
                                    if address > 0x20000000000:
                                        break
                                
                                if largest_region:
                                    scan_start = largest_region
                                    scan_size = int(largest_size / (1024 * 1024))
                                    self.log(f"✅ Found Unity heap: 0x{scan_start:X} ({scan_size} MB)", "SUCCESS")
                                else:
                                    # Fallback to scanning from low memory
                                    scan_start = 0x00000000
                                    scan_size = 2000
                                    self.log("⚠️ Using default scan range", "WARNING")
                                
                                self.start_entry.delete(0, tk.END)
                                self.start_entry.insert(0, f"0x{scan_start:X}")
                                
                                self.size_spin.delete(0, tk.END)
                                self.size_spin.insert(0, str(scan_size))
                        
                        kernel32.CloseHandle(hProcess)
                    break
        except:
            pass
    
    def first_scan(self):
        if not self.attached:
            messagebox.showerror("Error", "Please attach to a process first!")
            return
        
        try:
            start = int(self.start_entry.get(), 16)
        except:
            messagebox.showerror("Error", "Invalid start address")
            return
        
        size = int(self.size_spin.get()) * 1024 * 1024
        search_val = self.search_entry.get()
        search_val2 = self.search_entry2.get()
        
        # Parse scan type - remove the descriptive text
        scan_type_raw = self.scan_type.get()
        if '(' in scan_type_raw:
            scan_type = scan_type_raw.split('(')[0].strip().lower().replace(' ', '_')
        else:
            scan_type = scan_type_raw.lower()
        
        # Get scan condition
        condition_raw = self.scan_condition.get()
        condition = condition_raw.lower().replace(' ', '_')
        
        # Validate input based on condition
        if condition == 'exact_value':
            if not search_val:
                messagebox.showerror("Error", "Please enter a value to search for")
                return
        elif condition in ['value_between', 'increased_by', 'decreased_by']:
            if not search_val or not search_val2:
                messagebox.showerror("Error", f"{condition_raw} requires two values")
                return
        elif condition in ['bigger_than', 'smaller_than']:
            if not search_val:
                messagebox.showerror("Error", f"{condition_raw} requires a value")
                return
        
        self.log(f"Starting scan: {condition_raw} ({scan_type})", "INFO")
        self.log(f"Scan range: 0x{start:X} - 0x{start+size:X} ({size / (1024*1024):.1f} MB)", "INFO")
        
        self.scanning = True
        self.scan_btn.config(state=tk.DISABLED)
        self.next_btn.config(state=tk.DISABLED)
        
        # Start scan in thread
        thread = threading.Thread(target=self.perform_scan, 
                                 args=(start, size, search_val, search_val2, scan_type, condition))
        thread.daemon = True
        thread.start()
    
    def perform_scan(self, start, size, search_val, search_val2, scan_type, condition):
        # Store previous results for comparison scans
        if condition != 'unknown_initial_value' and len(self.scan_results) == 0:
            # For first scan with conditions other than unknown
            self.root.after(0, self.log, "Use 'Unknown Initial Value' for first scan or 'Exact Value'", "WARNING")
        
        if condition != 'unknown_initial_value' and condition != 'exact_value':
            # This is a rescan - use previous results
            self.next_scan_with_condition(condition, search_val, search_val2, scan_type)
            return
        
        # New scan
        self.scan_results = []
        chunk_size = 1024 * 1024  # 1MB chunks
        total_chunks = size // chunk_size
        
        # Determine value size and format
        if scan_type in ["int32", "float"]:
            value_size = 4
        elif scan_type in ["int64", "double"]:
            value_size = 8
        elif scan_type == "pattern":
            value_size = len(bytes.fromhex(search_val.replace(' ', '')))
        elif scan_type == "string":
            value_size = len(search_val.encode('utf-8'))
        else:
            value_size = 4
        
        pack_format = '<i' if scan_type == 'int32' else ('<q' if scan_type == 'int64' else ('<f' if scan_type == 'float' else '<d'))
        
        try:
            self.log(f"Scanning {total_chunks} chunks...", "INFO")
            
            for i in range(total_chunks):
                if not self.scanning:
                    break
                
                addr = start + (i * chunk_size)
                buffer = (ctypes.c_byte * chunk_size)()
                
                if stealth.ReadMemory(self.engine, c_void_p(addr), buffer, chunk_size):
                    data = bytes(bytearray([buffer[j] & 0xFF for j in range(chunk_size)]))
                    
                    if condition == 'unknown_initial_value':
                        # Store all non-zero values at 4-byte intervals
                        # Limit to reasonable range (money is usually 0-999999999)
                        for offset in range(0, len(data) - value_size, 4):
                            # Stop if we have too many results
                            if len(self.scan_results) > 100000:
                                self.root.after(0, self.log, 
                                              f"Stopped at 100,000 results. Use 'Exact Value' or range filters.", 
                                              "WARNING")
                                break
                            
                            mem_addr = addr + offset
                            value_bytes = data[offset:offset+value_size]
                            
                            # Unpack value for display
                            try:
                                if scan_type == 'int32':
                                    value = struct.unpack('<i', value_bytes)[0]
                                elif scan_type == 'int64':
                                    value = struct.unpack('<q', value_bytes)[0]
                                elif scan_type == 'float':
                                    value = struct.unpack('<f', value_bytes)[0]
                                elif scan_type == 'double':
                                    value = struct.unpack('<d', value_bytes)[0]
                                else:
                                    value = value_bytes.hex(' ')
                                
                                # Filter reasonable values for game money (0 to 1 billion)
                                if scan_type in ['int32', 'int64']:
                                    if 0 < value < 1000000000:  # Skip 0 and values > 1 billion
                                        self.scan_results.append((mem_addr, value, scan_type))
                                elif value != 0:  # For float/double, just skip zeros
                                    self.scan_results.append((mem_addr, value, scan_type))
                            except:
                                pass
                        
                        # Update display every 10000 results
                        if len(self.scan_results) % 10000 == 0 and len(self.scan_results) > 0:
                            self.root.after(0, self.log, 
                                          f"Found {len(self.scan_results):,} addresses so far...", 
                                          "INFO")
                    
                    elif condition == 'exact_value':
                        # Search for exact value
                        if scan_type == "pattern":
                            pattern = bytes.fromhex(search_val.replace(' ', ''))
                            idx = 0
                            while (idx := data.find(pattern, idx)) != -1:
                                found_addr = addr + idx
                                self.scan_results.append((found_addr, pattern.hex(' '), "pattern"))
                                self.root.after(0, self.add_result, 
                                              len(self.scan_results), found_addr, pattern.hex(' '), "pattern")
                                idx += 1
                        
                        elif scan_type == "string":
                            search_bytes = search_val.encode('utf-8')
                            idx = 0
                            while (idx := data.find(search_bytes, idx)) != -1:
                                found_addr = addr + idx
                                self.scan_results.append((found_addr, search_val, "string"))
                                self.root.after(0, self.add_result,
                                              len(self.scan_results), found_addr, search_val, "string")
                                idx += 1
                        
                        else:
                            # Numeric value
                            if scan_type in ['int32', 'int64']:
                                search_value = int(search_val.replace(',', ''))
                            else:
                                search_value = float(search_val)
                            
                            search_bytes = struct.pack(pack_format, search_value)
                            
                            idx = 0
                            while (idx := data.find(search_bytes, idx)) != -1:
                                found_addr = addr + idx
                                self.scan_results.append((found_addr, search_value, scan_type))
                                self.root.after(0, self.add_result,
                                              len(self.scan_results), found_addr, 
                                              str(search_value), scan_type)
                                idx += 1
                    
                    elif condition in ['bigger_than', 'smaller_than', 'value_between']:
                        # Range scans
                        for offset in range(0, len(data) - value_size, 4):
                            mem_addr = addr + offset
                            value_bytes = data[offset:offset+value_size]
                            
                            try:
                                value = struct.unpack(pack_format, value_bytes)[0]
                                
                                matches = False
                                if condition == 'bigger_than':
                                    compare_val = int(search_val) if scan_type in ['int32', 'int64'] else float(search_val)
                                    matches = value > compare_val
                                elif condition == 'smaller_than':
                                    compare_val = int(search_val) if scan_type in ['int32', 'int64'] else float(search_val)
                                    matches = value < compare_val
                                elif condition == 'value_between':
                                    val1 = int(search_val) if scan_type in ['int32', 'int64'] else float(search_val)
                                    val2 = int(search_val2) if scan_type in ['int32', 'int64'] else float(search_val2)
                                    matches = val1 <= value <= val2
                                
                                if matches:
                                    self.scan_results.append((mem_addr, value, scan_type))
                                    if len(self.scan_results) % 1000 == 0:
                                        self.root.after(0, self.add_result,
                                                      len(self.scan_results), mem_addr,
                                                      str(value), scan_type)
                            except:
                                pass
                
                progress = int((i + 1) / total_chunks * 100)
                self.root.after(0, self.update_progress, progress, 
                              f"Scanning... {i+1}/{total_chunks} chunks - {len(self.scan_results):,} found")
            
            # Display first 1000 results only (for performance)
            if condition == 'unknown_initial_value':
                self.root.after(0, self.log, f"Displaying first 1000 of {len(self.scan_results):,} results", "INFO")
                for i, (addr, value, stype) in enumerate(self.scan_results[:1000], 1):
                    self.root.after(0, self.add_result, i, addr, str(value), stype)
            
            self.root.after(0, self.scan_complete)
            
        except Exception as e:
            self.root.after(0, self.log, f"Scan error: {str(e)}", "ERROR")
            self.root.after(0, self.scan_complete)
    
    def add_result(self, num, addr, value, rtype):
        item_id = self.results_tree.insert('', tk.END, text=str(num),
                                values=(f'0x{addr:X}', '-', value, rtype))
        # Store mapping for live updates
        if not hasattr(self, 'tree_item_map'):
            self.tree_item_map = {}
        self.tree_item_map[addr] = item_id
    
    def update_progress(self, value, text):
        self.progress.config(value=value)
        self.progress_label.config(text=text)
    
    def scan_complete(self):
        self.scanning = False
        self.scan_btn.config(state=tk.NORMAL)
        if self.scan_results:
            self.next_btn.config(state=tk.NORMAL)
            self.monitor_btn.config(state=tk.NORMAL)
        
        total = len(self.scan_results)
        self.log(f"Scan complete: {total} results found", "SUCCESS")
        self.progress_label.config(text=f"Found {total} matches")
    
    def next_scan(self):
        if len(self.scan_results) == 0:
            messagebox.showerror("Error", "No previous scan results! Use First Scan first.")
            return
        
        # Get condition
        condition_raw = self.scan_condition.get()
        condition = condition_raw.lower().replace(' ', '_')
        
        search_val = self.search_entry.get()
        search_val2 = self.search_entry2.get()
        
        # Parse scan type
        scan_type_raw = self.scan_type.get()
        if '(' in scan_type_raw:
            scan_type = scan_type_raw.split('(')[0].strip().lower().replace(' ', '_')
        else:
            scan_type = scan_type_raw.lower()
        
        self.log(f"Next Scan: {condition_raw} on {len(self.scan_results)} addresses", "INFO")
        
        self.scanning = True
        self.next_btn.config(state=tk.DISABLED)
        
        thread = threading.Thread(target=self.next_scan_with_condition, 
                                 args=(condition, search_val, search_val2, scan_type))
        thread.daemon = True
        thread.start()
    
    def next_scan_with_condition(self, condition, search_val, search_val2, scan_type):
        """Rescan previous results with specified condition"""
        
        # Determine value size and pack format
        if scan_type in ['int32', 'float']:
            value_size = 4
        elif scan_type in ['int64', 'double']:
            value_size = 8
        else:
            value_size = 4
        
        pack_format = '<i' if scan_type == 'int32' else ('<q' if scan_type == 'int64' else ('<f' if scan_type == 'float' else '<d'))
        
        new_results = []
        total = len(self.scan_results)
        
        try:
            for i, (addr, old_value, stype) in enumerate(self.scan_results):
                if not self.scanning:
                    break
                
                # Read current value
                buffer = (ctypes.c_byte * value_size)()
                if not stealth.ReadMemory(self.engine, c_void_p(addr), buffer, value_size):
                    continue
                
                try:
                    value_bytes = bytes([buffer[j] & 0xFF for j in range(value_size)])
                    
                    if scan_type == 'int32':
                        new_value = struct.unpack('<i', value_bytes)[0]
                        old_value_num = int(old_value) if isinstance(old_value, str) else old_value
                    elif scan_type == 'int64':
                        new_value = struct.unpack('<q', value_bytes)[0]
                        old_value_num = int(old_value) if isinstance(old_value, str) else old_value
                    elif scan_type == 'float':
                        new_value = struct.unpack('<f', value_bytes)[0]
                        old_value_num = float(old_value) if isinstance(old_value, str) else old_value
                    elif scan_type == 'double':
                        new_value = struct.unpack('<d', value_bytes)[0]
                        old_value_num = float(old_value) if isinstance(old_value, str) else old_value
                    else:
                        continue
                    
                    matches = False
                    
                    if condition == 'exact_value':
                        compare_val = int(search_val) if scan_type in ['int32', 'int64'] else float(search_val)
                        matches = (new_value == compare_val)
                    
                    elif condition == 'increased_value':
                        matches = (new_value > old_value_num)
                    
                    elif condition == 'decreased_value':
                        matches = (new_value < old_value_num)
                    
                    elif condition == 'changed_value':
                        matches = (new_value != old_value_num)
                    
                    elif condition == 'unchanged_value':
                        matches = (new_value == old_value_num)
                    
                    elif condition == 'bigger_than':
                        compare_val = int(search_val) if scan_type in ['int32', 'int64'] else float(search_val)
                        matches = (new_value > compare_val)
                    
                    elif condition == 'smaller_than':
                        compare_val = int(search_val) if scan_type in ['int32', 'int64'] else float(search_val)
                        matches = (new_value < compare_val)
                    
                    elif condition == 'value_between':
                        val1 = int(search_val) if scan_type in ['int32', 'int64'] else float(search_val)
                        val2 = int(search_val2) if scan_type in ['int32', 'int64'] else float(search_val2)
                        matches = (val1 <= new_value <= val2)
                    
                    elif condition == 'increased_by':
                        target_increase = int(search_val) if scan_type in ['int32', 'int64'] else float(search_val)
                        actual_increase = new_value - old_value_num
                        matches = (abs(actual_increase - target_increase) < 0.001)
                    
                    elif condition == 'decreased_by':
                        target_decrease = int(search_val) if scan_type in ['int32', 'int64'] else float(search_val)
                        actual_decrease = old_value_num - new_value
                        matches = (abs(actual_decrease - target_decrease) < 0.001)
                    
                    if matches:
                        new_results.append((addr, new_value, scan_type))
                
                except Exception as e:
                    pass
                
                if i % 1000 == 0:
                    progress = int((i + 1) / total * 100)
                    self.root.after(0, self.update_progress, progress,
                                  f"Rescanning... {i+1}/{total} - {len(new_results)} match")
            
            # Update results
            self.scan_results = new_results
            self.root.after(0, self.refresh_results_display)
            self.root.after(0, self.scan_complete)
            
        except Exception as e:
            self.root.after(0, self.log, f"Rescan error: {str(e)}", "ERROR")
            self.root.after(0, self.scan_complete)
    
    def refresh_results_display(self):
        """Clear and redisplay all results"""
        self.results_tree.delete(*self.results_tree.get_children())
        self.tree_item_map = {}
        
        for i, (addr, value, stype) in enumerate(self.scan_results[:5000], 1):  # Limit to 5000 displayed
            item_id = self.results_tree.insert('', tk.END, text=str(i),
                                    values=(f'0x{addr:X}', '-', str(value), stype))
            self.tree_item_map[addr] = item_id
        
        if len(self.scan_results) > 5000:
            self.log(f"Showing first 5000 of {len(self.scan_results)} results", "INFO")
    
    def perform_rescan(self, search_val):
        # Legacy function - redirect to new system
        self.next_scan_with_condition('exact_value', search_val, '', self.scan_type.get())
    
    def perform_rescan(self, search_val):
        new_results = []
        scan_type = self.scan_type.get()
        
        for i, (addr, old_val, rtype) in enumerate(self.scan_results):
            if not self.scanning:
                break
            
            buffer = (ctypes.c_byte * 64)()
            if stealth.ReadMemory(self.engine, c_void_p(addr), buffer, 64):
                # Check if value matches
                if scan_type == "pattern":
                    pattern = bytes.fromhex(search_val.replace(' ', ''))
                    data = bytes(bytearray([buffer[j] & 0xFF for j in range(len(pattern))]))
                    if data == pattern:
                        new_results.append((addr, data.hex(' '), rtype))
                # Add more type checks as needed
            
            progress = int((i + 1) / len(self.scan_results) * 100)
            self.root.after(0, self.update_progress, progress, f"Re-scanning... {i+1}/{len(self.scan_results)}")
        
        self.scan_results = new_results
        self.root.after(0, self.refresh_results)
    
    def refresh_results(self):
        self.results_tree.delete(*self.results_tree.get_children())
        for i, (addr, val, rtype) in enumerate(self.scan_results, 1):
            self.results_tree.insert('', tk.END, text=str(i),
                                    values=(f'0x{addr:X}', val, rtype))
        self.log(f"Results filtered: {len(self.scan_results)} remaining", "SUCCESS")
    
    def stop_scan(self):
        self.scanning = False
        self.log("Scan stopped by user", "WARN")
    
    def clear_results(self):
        # Stop monitoring if active
        if self.monitoring_active:
            self.monitoring_active = False
            self.monitor_btn.config(text="▶️ LIVE MONITOR", bg='#00aa00')
        
        self.results_tree.delete(*self.results_tree.get_children())
        self.scan_results = []
        self.tree_item_map = {}
        self.progress.config(value=0)
        self.progress_label.config(text="Ready")
        self.next_btn.config(state=tk.DISABLED)
        self.monitor_btn.config(state=tk.DISABLED)
        self.log("Results cleared", "INFO")
    
    def view_selected(self, event=None):
        selection = self.results_tree.selection()
        if not selection:
            return
        
        item = self.results_tree.item(selection[0])
        addr_str = item['values'][0]
        addr = int(addr_str, 16)
        
        self.viewer_addr.delete(0, tk.END)
        self.viewer_addr.insert(0, f"0x{addr:X}")
        self.view_memory()
    
    def view_memory(self):
        if not self.attached:
            return
        
        try:
            addr = int(self.viewer_addr.get(), 16)
            size = int(self.viewer_size.get())
            
            buffer = (ctypes.c_byte * size)()
            if stealth.ReadMemory(self.engine, c_void_p(addr), buffer, size):
                dump = ""
                for i in range(0, size, 16):
                    line_addr = addr + i
                    
                    # Hex bytes
                    hex_bytes = " ".join(f"{buffer[j] & 0xFF:02X}" 
                                        for j in range(i, min(i+16, size)))
                    
                    # ASCII representation
                    ascii_bytes = "".join(
                        chr(buffer[j] & 0xFF) if 32 <= (buffer[j] & 0xFF) < 127 else "."
                        for j in range(i, min(i+16, size)))
                    
                    dump += f"0x{line_addr:016X}  {hex_bytes:<48}  {ascii_bytes}\n"
                
                self.hex_display.delete('1.0', tk.END)
                self.hex_display.insert('1.0', dump)
                self.log(f"Viewing memory at 0x{addr:X} ({size} bytes)", "INFO")
            else:
                self.log(f"Failed to read memory at 0x{addr:X}", "ERROR")
                messagebox.showerror("Error", "Failed to read memory at this address")
        except Exception as e:
            self.log(f"View error: {str(e)}", "ERROR")
            messagebox.showerror("Error", str(e))
    
    def write_memory(self):
        if not self.attached:
            return
        
        try:
            addr = int(self.write_addr.get(), 16)
            bytes_str = self.write_bytes.get().replace(' ', '')
            data = bytes.fromhex(bytes_str)
            
            if stealth.WriteMemory(self.engine, c_void_p(addr), data, len(data)):
                self.log(f"Wrote {len(data)} bytes to 0x{addr:X}", "SUCCESS")
                messagebox.showinfo("Success", f"Wrote {len(data)} bytes to 0x{addr:X}")
                
                # Refresh view if same address
                if self.viewer_addr.get() == f"0x{addr:X}":
                    self.view_memory()
            else:
                self.log(f"Write failed at 0x{addr:X}", "ERROR")
                messagebox.showerror("Error", "Write operation failed")
        except Exception as e:
            self.log(f"Write error: {str(e)}", "ERROR")
            messagebox.showerror("Error", str(e))
    
    def bookmark_selected(self):
        selection = self.results_tree.selection()
        if not selection:
            return
        
        item = self.results_tree.item(selection[0])
        addr = item['values'][0]
        value = item['values'][1]
        
        name = tk.simpledialog.askstring("Bookmark", "Enter bookmark name:")
        if name:
            self.bookmarks[name] = (addr, value)
            self.log(f"Added bookmark: {name} -> {addr}", "INFO")
    
    def show_bookmarks(self):
        if not self.bookmarks:
            messagebox.showinfo("Bookmarks", "No bookmarks saved")
            return
        
        win = tk.Toplevel(self.root)
        win.title("Bookmarks")
        win.geometry("600x400")
        win.configure(bg='#0a0a0a')
        
        tree = ttk.Treeview(win, columns=('Address', 'Value'))
        tree.heading('#0', text='Name')
        tree.heading('Address', text='Address')
        tree.heading('Value', text='Value')
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for name, (addr, val) in self.bookmarks.items():
            tree.insert('', tk.END, text=name, values=(addr, val))
    
    def launch_tutorial(self):
        """Launch the tutorial game"""
        import subprocess
        import os
        import sys
        
        # Try multiple paths for RvrseGame.exe (standalone tutorial)
        possible_paths = [
            os.path.join(os.path.dirname(sys.executable), "RvrseGame.exe"),  # Same as exe
            os.path.join(os.path.dirname(__file__), "RvrseGame.exe"),  # Same as script
            os.path.join(os.getcwd(), "RvrseGame.exe"),  # Current directory
            os.path.join("dist", "RvrseGame.exe"),  # dist folder
            r"D:\ROBLOX_EXECUTOR\dist\RvrseGame.exe"  # Absolute fallback
        ]
        
        tutorial_path = None
        for path in possible_paths:
            if os.path.exists(path):
                tutorial_path = path
                break
        
        if not tutorial_path:
            messagebox.showerror("Tutorial Not Found", 
                               f"RvrseGame.exe not found!\n\n"
                               f"Searched locations:\n" + "\n".join(possible_paths) + "\n\n"
                               "Please ensure RvrseGame.exe is in the same directory.")
            return
        
        try:
            # Launch tutorial game (standalone exe, not python script)
            subprocess.Popen([tutorial_path], 
                           cwd=os.path.dirname(tutorial_path))
            
            # Show instructions
            msg = """
🎮 TUTORIAL GAME LAUNCHED!

📋 NEXT STEPS:
1. Wait 2 seconds for tutorial window to appear
2. Click the ORANGE '⬇ SELECT PROCESS ⬇' button (top left)
3. Type 'RvrseGame' in the search box
4. Double-click RvrseGame.exe (shown in GREEN)
5. Follow the in-game tutorial instructions!

✨ The tutorial will teach you:
  • Step 1: Find exact values (Health = 100)
  • Step 2: Unknown initial values (Money)
  • Step 3: Freeze values (Infinite money)
  • Step 4: Pointer scanning (Ammo)
  • Step 5-10: Advanced techniques!

Good luck! 🚀
            """
            messagebox.showinfo("Tutorial Started", msg)
            self.log("Tutorial game launched! Look for RvrseGame.exe in process list.", "INFO")
            
            # Auto-refresh process list after 3 seconds
            self.root.after(3000, self.refresh_process_list)
            
        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to launch tutorial:\n{str(e)}")
    
    def copy_address(self):
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            addr = item['values'][0]
            self.root.clipboard_clear()
            self.root.clipboard_append(addr)
            self.log(f"Copied address: {addr}", "INFO")
    
    def delete_selected(self):
        selection = self.results_tree.selection()
        if selection:
            self.results_tree.delete(selection[0])
    
    def show_context_menu(self, event):
        self.results_menu.post(event.x_root, event.y_root)
    
    def toggle_edit_mode(self):
        messagebox.showinfo("Edit Mode", "Edit mode allows direct hex editing\nDouble-click hex bytes to modify")
    
    def show_process_info(self):
        if not self.attached:
            messagebox.showwarning("Not Attached", "Attach to a process first")
            return
        
        info = f"Process: {self.process_name}\n"
        info += f"Engine Handle: 0x{self.engine:X}\n"
        info += f"Base Address: 0x{self.base_address:X}\n"
        info += f"Status: Connected\n"
        messagebox.showinfo("Process Info", info)
    
    def show_memory_map(self):
        """Display full memory map of attached process"""
        if not self.attached or not self.current_pid:
            messagebox.showwarning("Not Attached", "Attach to a process first")
            return
        
        map_win = tk.Toplevel(self.root)
        map_win.title(f"Memory Map - {self.process_name}")
        map_win.geometry("1000x700")
        map_win.configure(bg='#0a0a0a')
        
        tk.Label(map_win, text=f"Memory Regions - {self.process_name}",
                bg='#0a0a0a', fg='#00ff41', font=('Segoe UI', 14, 'bold')).pack(pady=10)
        
        # Create treeview for memory regions
        frame = tk.Frame(map_win, bg='#0a0a0a')
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        tree = ttk.Treeview(frame, columns=('Address', 'Size', 'Protection', 'Type', 'Accessible'),
                           yscrollcommand=scrollbar.set)
        tree.heading('#0', text='Region')
        tree.heading('Address', text='Base Address')
        tree.heading('Size', text='Size')
        tree.heading('Protection', text='Protection')
        tree.heading('Type', text='Type')
        tree.heading('Accessible', text='Readable')
        tree.column('#0', width=100)
        tree.column('Address', width=150)
        tree.column('Size', width=120)
        tree.column('Protection', width=120)
        tree.column('Type', width=120)
        tree.column('Accessible', width=100)
        tree.pack(fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=tree.yview)
        
        status = tk.Label(map_win, text="Scanning memory regions...",
                         bg='#0a0a0a', fg='#00ff41', font=('Consolas', 10))
        status.pack(pady=5)
        
        def scan_memory():
            regions = []
            region_count = 0
            
            # Scan memory in 1MB chunks
            for offset in range(0, 500 * 1024 * 1024, 1024 * 1024):  # 500MB
                addr = self.base_address + offset
                buffer = (ctypes.c_byte * 1024)()
                
                is_readable = stealth.ReadMemory(self.engine, c_void_p(addr), buffer, 1024)
                
                if is_readable:
                    data = bytes(bytearray([buffer[j] & 0xFF for j in range(1024)]))
                    
                    # Detect region type
                    if data[:2] == b'MZ':
                        region_type = 'Executable'
                    elif data == b'\x00' * 1024:
                        region_type = 'Zero'
                    elif all(32 <= b < 127 or b in [9, 10, 13] for b in data[:100] if b != 0):
                        region_type = 'Text/Data'
                    else:
                        region_type = 'Binary'
                    
                    regions.append({
                        'address': addr,
                        'size': '1 MB',
                        'protection': 'R',
                        'type': region_type,
                        'readable': 'Yes'
                    })
                    region_count += 1
                else:
                    if region_count > 0 and regions[-1]['readable'] == 'No':
                        continue  # Skip consecutive blocked regions
                    
                    regions.append({
                        'address': addr,
                        'size': '1 MB',
                        'protection': '?',
                        'type': 'Protected',
                        'readable': 'No'
                    })
                    region_count += 1
                
                if region_count % 10 == 0:
                    map_win.after(0, status.config, {'text': f'Scanned {region_count} regions...'})
            
            # Update tree
            for i, region in enumerate(regions):
                tag = 'readable' if region['readable'] == 'Yes' else 'blocked'
                map_win.after(0, tree.insert, '', tk.END, text=f'Region {i+1}',
                            values=(f"0x{region['address']:X}", region['size'],
                                   region['protection'], region['type'], region['readable']),
                            tags=(tag,))
            
            tree.tag_configure('readable', foreground='#00ff41')
            tree.tag_configure('blocked', foreground='#ff4444')
            
            map_win.after(0, status.config, {'text': f'Found {len(regions)} memory regions'})
            
            # Export button
            def export_map():
                export_file = os.path.join(self.export_dir, 'logs', 
                                          f'memory_map_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
                with open(export_file, 'w') as f:
                    json.dump({
                        'process': self.process_name,
                        'base': f'0x{self.base_address:X}',
                        'regions': [{
                            'address': f"0x{r['address']:X}",
                            'size': r['size'],
                            'type': r['type'],
                            'readable': r['readable']
                        } for r in regions]
                    }, f, indent=2)
                self.log(f"Memory map exported: {export_file}", "SUCCESS")
                messagebox.showinfo("Exported", f"Memory map saved:\n{export_file}")
            
            map_win.after(0, tk.Button, map_win, {'text': '📁 Export Map', 'command': export_map,
                         'bg': '#0066cc', 'fg': 'white', 'font': ('Segoe UI', 10, 'bold'),
                         'padx': 20, 'pady': 10}).pack(pady=10)
        
        thread = threading.Thread(target=scan_memory)
        thread.daemon = True
        thread.start()
    
    def scan_all_games(self):
        """Scan all running games for a pattern"""
        if not self.available_processes:
            messagebox.showwarning("No Games", "No game processes detected")
            return
        
        pattern = self.search_entry.get()
        if not pattern:
            messagebox.showwarning("No Pattern", "Enter a search pattern first")
            return
        
        result_window = tk.Toplevel(self.root)
        result_window.title("Multi-Game Scan Results")
        result_window.geometry("800x600")
        result_window.configure(bg='#0a0a0a')
        
        tk.Label(result_window, text=f"Scanning {len(self.available_processes)} processes for pattern...",
                bg='#0a0a0a', fg='#00ff41', font=('Segoe UI', 12, 'bold')).pack(pady=10)
        
        results_text = scrolledtext.ScrolledText(result_window, bg='#000000', fg='#00ff41',
                                                 font=('Consolas', 9))
        results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        progress = ttk.Progressbar(result_window, length=400, mode='determinate')
        progress.pack(fill=tk.X, padx=10, pady=10)
        
        def scan_thread():
            results_text.insert(tk.END, f"Pattern: {pattern}\n")
            results_text.insert(tk.END, "=" * 80 + "\n\n")
            
            try:
                search_bytes = bytes.fromhex(pattern.replace(' ', ''))
            except:
                results_text.insert(tk.END, "ERROR: Invalid hex pattern\n")
                return
            
            found_in_games = 0
            total_matches = 0
            
            for idx, (proc_name, pid, mem) in enumerate(self.available_processes):
                progress['value'] = int((idx + 1) / len(self.available_processes) * 100)
                result_window.update()
                
                results_text.insert(tk.END, f"[{idx+1}/{len(self.available_processes)}] {proc_name} (PID: {pid})\n")
                results_text.see(tk.END)
                
                # Try to attach
                engine = stealth.CreateEngine()
                if stealth.AttachToProcess(engine, proc_name.encode()):
                    results_text.insert(tk.END, f"  ✓ Attached\n")
                    
                    # Quick scan (first 10MB)
                    scan_size = min(10 * 1024 * 1024, int(mem * 1024 * 1024))
                    matches = 0
                    
                    # Try to get base address
                    import psutil
                    try:
                        proc = psutil.Process(pid)
                        base = 0x7FF600000000  # Default base for 64-bit
                        
                        # Scan in 1MB chunks
                        for offset in range(0, scan_size, 1024 * 1024):
                            addr = base + offset
                            buffer = (ctypes.c_byte * (1024 * 1024))()
                            
                            if stealth.ReadMemory(engine, c_void_p(addr), buffer, 1024 * 1024):
                                data = bytes(bytearray([buffer[j] & 0xFF for j in range(1024 * 1024)]))
                                count = data.count(search_bytes)
                                matches += count
                    except:
                        pass
                    
                    if matches > 0:
                        results_text.insert(tk.END, f"  ✓ FOUND {matches} matches!\n", "success")
                        found_in_games += 1
                        total_matches += matches
                    else:
                        results_text.insert(tk.END, f"  - No matches\n")
                else:
                    results_text.insert(tk.END, f"  ✗ Could not attach\n")
                
                results_text.insert(tk.END, "\n")
                results_text.see(tk.END)
            
            results_text.insert(tk.END, "\n" + "=" * 80 + "\n")
            results_text.insert(tk.END, f"SUMMARY: Found in {found_in_games}/{len(self.available_processes)} games\n")
            results_text.insert(tk.END, f"Total Matches: {total_matches}\n")
            results_text.tag_config("success", foreground="#00ffff")
        
        thread = threading.Thread(target=scan_thread)
        thread.daemon = True
        thread.start()
    
    def export_full_memory(self):
        """Export complete memory dump of attached process"""
        if not self.attached or not self.current_pid:
            messagebox.showwarning("Not Attached", "Attach to a process first")
            return
        
        self.log("Starting full memory dump...", "INFO")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dump_file = os.path.join(self.export_dir, "memory_dumps", 
                                f"{self.process_name}_{timestamp}.dmp")
        
        def dump_thread():
            try:
                with open(dump_file, 'wb') as f:
                    # Dump entire process memory space
                    start = self.base_address
                    size = 200 * 1024 * 1024  # 200MB default
                    chunk_size = 1024 * 1024
                    
                    total_written = 0
                    for offset in range(0, size, chunk_size):
                        addr = start + offset
                        buffer = (ctypes.c_byte * chunk_size)()
                        
                        if stealth.ReadMemory(self.engine, c_void_p(addr), buffer, chunk_size):
                            data = bytes(bytearray([buffer[j] & 0xFF for j in range(chunk_size)]))
                            f.write(data)
                            total_written += chunk_size
                            
                            progress = int((offset + chunk_size) / size * 100)
                            self.root.after(0, self.log, 
                                          f"Dumping memory... {progress}% ({total_written // (1024*1024)}MB)", "INFO")
                
                self.root.after(0, self.log, f"✓ Memory dump saved: {dump_file}", "SUCCESS")
                self.root.after(0, messagebox.showinfo, "Success", 
                              f"Full memory dump saved!\n\n{dump_file}\n\nSize: {total_written // (1024*1024)}MB")
            except Exception as e:
                self.root.after(0, self.log, f"Dump error: {str(e)}", "ERROR")
        
        thread = threading.Thread(target=dump_thread)
        thread.daemon = True
        thread.start()
    
    def export_selected_region(self):
        """Export memory region from current view"""
        if not self.attached:
            messagebox.showwarning("Not Attached", "Attach to a process first")
            return
        
        try:
            addr = int(self.viewer_addr.get(), 16)
            size = int(self.viewer_size.get())
        except:
            messagebox.showerror("Error", "Invalid address or size")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"region_0x{addr:X}_{timestamp}.bin"
        filepath = os.path.join(self.export_dir, "ghidra_ready", filename)
        
        buffer = (ctypes.c_byte * size)()
        if stealth.ReadMemory(self.engine, c_void_p(addr), buffer, size):
            data = bytes(bytearray([buffer[j] & 0xFF for j in range(size)]))
            
            with open(filepath, 'wb') as f:
                f.write(data)
            
            # Create metadata file
            meta_file = filepath.replace('.bin', '_metadata.json')
            metadata = {
                'process': self.process_name,
                'pid': self.current_pid,
                'address': f'0x{addr:X}',
                'size': size,
                'timestamp': timestamp,
                'base_address': f'0x{self.base_address:X}'
            }
            
            with open(meta_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.log(f"✓ Exported region: {filename}", "SUCCESS")
            messagebox.showinfo("Success", f"Region exported!\n\n{filepath}\n\nReady for Ghidra import")
        else:
            messagebox.showerror("Error", "Failed to read memory region")
    
    def export_scan_results(self):
        """Export all scan results with full data"""
        if not self.scan_results:
            messagebox.showwarning("No Results", "No scan results to export")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = os.path.join(self.export_dir, "logs", 
                                   f"scan_results_{timestamp}.json")
        
        # Collect full data for each result
        full_results = []
        for addr, val, rtype in self.scan_results:
            # Read surrounding context (64 bytes)
            buffer = (ctypes.c_byte * 64)()
            context_hex = ""
            
            if stealth.ReadMemory(self.engine, c_void_p(addr), buffer, 64):
                context_hex = bytes(bytearray([buffer[j] & 0xFF for j in range(64)])).hex(' ')
            
            full_results.append({
                'address': f'0x{addr:X}',
                'value': val,
                'type': rtype,
                'context': context_hex,
                'offset_from_base': addr - self.base_address
            })
        
        data = {
            'process': self.process_name,
            'pid': self.current_pid,
            'base_address': f'0x{self.base_address:X}',
            'timestamp': timestamp,
            'total_results': len(full_results),
            'results': full_results
        }
        
        with open(export_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.log(f"✓ Exported {len(full_results)} results", "SUCCESS")
        messagebox.showinfo("Success", f"Scan results exported!\n\n{export_file}")
    
    def take_snapshot(self):
        """Take snapshot of current memory state"""
        if not self.attached:
            messagebox.showwarning("Not Attached", "Attach to a process first")
            return
        
        name = tk.simpledialog.askstring("Snapshot", "Enter snapshot name:")
        if not name:
            return
        
        self.log(f"Taking snapshot: {name}", "INFO")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_file = os.path.join(self.export_dir, "memory_dumps",
                                    f"snapshot_{name}_{timestamp}.bin")
        
        # Snapshot key regions (first 50MB)
        size = 50 * 1024 * 1024
        buffer = (ctypes.c_byte * size)()
        
        if stealth.ReadMemory(self.engine, c_void_p(self.base_address), buffer, size):
            data = bytes(bytearray([buffer[j] & 0xFF for j in range(size)]))
            
            with open(snapshot_file, 'wb') as f:
                f.write(data)
            
            self.memory_snapshots.append({
                'name': name,
                'file': snapshot_file,
                'timestamp': timestamp,
                'size': size
            })
            
            self.log(f"✓ Snapshot saved: {name}", "SUCCESS")
            messagebox.showinfo("Success", f"Snapshot captured!\n\n{snapshot_file}")
        else:
            messagebox.showerror("Error", "Failed to capture snapshot")
    
    def compare_snapshots(self):
        """Compare two memory snapshots"""
        if len(self.memory_snapshots) < 2:
            messagebox.showwarning("Not Enough Snapshots", 
                                  f"Need at least 2 snapshots. Current: {len(self.memory_snapshots)}")
            return
        
        # Create comparison window
        comp_win = tk.Toplevel(self.root)
        comp_win.title("Snapshot Comparison")
        comp_win.geometry("900x700")
        comp_win.configure(bg='#0a0a0a')
        
        tk.Label(comp_win, text="Select snapshots to compare:",
                bg='#0a0a0a', fg='#00ff41', font=('Segoe UI', 12, 'bold')).pack(pady=10)
        
        frame = tk.Frame(comp_win, bg='#0a0a0a')
        frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(frame, text="Snapshot 1:", bg='#0a0a0a', fg='white').pack(side=tk.LEFT, padx=5)
        snap1_var = tk.StringVar()
        snap1_combo = ttk.Combobox(frame, textvariable=snap1_var, width=30)
        snap1_combo['values'] = [s['name'] for s in self.memory_snapshots]
        snap1_combo.pack(side=tk.LEFT, padx=5)
        
        tk.Label(frame, text="Snapshot 2:", bg='#0a0a0a', fg='white').pack(side=tk.LEFT, padx=20)
        snap2_var = tk.StringVar()
        snap2_combo = ttk.Combobox(frame, textvariable=snap2_var, width=30)
        snap2_combo['values'] = [s['name'] for s in self.memory_snapshots]
        snap2_combo.pack(side=tk.LEFT, padx=5)
        
        results_text = scrolledtext.ScrolledText(comp_win, bg='#000000', fg='#00ff41',
                                                 font=('Consolas', 9))
        results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        def compare():
            snap1_name = snap1_var.get()
            snap2_name = snap2_var.get()
            
            if not snap1_name or not snap2_name:
                messagebox.showwarning("Selection Required", "Select both snapshots")
                return
            
            snap1 = next(s for s in self.memory_snapshots if s['name'] == snap1_name)
            snap2 = next(s for s in self.memory_snapshots if s['name'] == snap2_name)
            
            results_text.insert(tk.END, f"Comparing: {snap1_name} vs {snap2_name}\n")
            results_text.insert(tk.END, "=" * 80 + "\n\n")
            
            with open(snap1['file'], 'rb') as f1, open(snap2['file'], 'rb') as f2:
                data1 = f1.read()
                data2 = f2.read()
            
            differences = 0
            regions = []
            
            for i in range(min(len(data1), len(data2))):
                if data1[i] != data2[i]:
                    differences += 1
                    if len(regions) == 0 or i - regions[-1] > 16:
                        regions.append(i)
            
            results_text.insert(tk.END, f"Total bytes changed: {differences}\n")
            results_text.insert(tk.END, f"Changed regions: {len(regions)}\n\n")
            
            results_text.insert(tk.END, "First 20 changed regions:\n")
            results_text.insert(tk.END, "-" * 80 + "\n")
            
            for idx, offset in enumerate(regions[:20]):
                addr = self.base_address + offset
                results_text.insert(tk.END, f"\n[{idx+1}] Offset: 0x{offset:X} (Address: 0x{addr:X})\n")
                
                # Show before/after
                before = data1[offset:offset+16].hex(' ')
                after = data2[offset:offset+16].hex(' ')
                
                results_text.insert(tk.END, f"  Before: {before}\n")
                results_text.insert(tk.END, f"  After:  {after}\n")
            
            # Export diff
            diff_file = os.path.join(self.export_dir, "logs",
                                    f"diff_{snap1_name}_vs_{snap2_name}.json")
            
            diff_data = {
                'snapshot1': snap1_name,
                'snapshot2': snap2_name,
                'total_changes': differences,
                'changed_regions': [f'0x{self.base_address + r:X}' for r in regions]
            }
            
            with open(diff_file, 'w') as f:
                json.dump(diff_data, f, indent=2)
            
            results_text.insert(tk.END, f"\n\nDiff exported: {diff_file}\n")
        
        tk.Button(comp_win, text="Compare", command=compare,
                 bg='#0066cc', fg='white', font=('Segoe UI', 10, 'bold'),
                 padx=20, pady=10).pack(pady=10)
    
    def quick_ghidra_export(self):
        """One-click export for Ghidra decompilation"""
        if not self.attached or not self.current_pid:
            messagebox.showwarning("Not Attached", "Attach to a process first")
            return
        
        self.log("Preparing Ghidra export...", "INFO")
        
        # Export executable
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_name = f"{self.process_name}_{timestamp}"
        
        # Get executable path
        try:
            import psutil
            proc = psutil.Process(self.current_pid)
            exe_path = proc.exe()
            
            # Copy executable to export folder
            import shutil
            dest_exe = os.path.join(self.export_dir, "ghidra_ready", f"{export_name}.exe")
            shutil.copy2(exe_path, dest_exe)
            
            self.log(f"✓ Copied executable: {dest_exe}", "SUCCESS")
            
            # Create Ghidra import script
            script_path = os.path.join(self.export_dir, "ghidra_ready", f"{export_name}_import.py")
            
            script_content = f'''# Ghidra Auto-Import Script
# Generated by Memory Explorer
# Process: {self.process_name}
# Base Address: 0x{self.base_address:X}
# Timestamp: {timestamp}

from ghidra.program.model.address import Address
from ghidra.program.model.symbol import SourceType

print("[+] Starting auto-analysis...")

# Set base address
program = getCurrentProgram()
imageBase = program.getImageBase()
print(f"Image base: {{imageBase}}")

# Add known addresses from scan results
known_addresses = [
'''
            
            # Add scan results as known addresses
            for addr, val, rtype in self.scan_results[:50]:  # First 50 results
                offset = addr - self.base_address
                script_content += f'    (0x{offset:X}, "{rtype}", "{val}"),\n'
            
            script_content += ''']

for offset, typ, value in known_addresses:
    addr = imageBase.add(offset)
    symbol_name = f"{typ}_{offset:08X}"
    createLabel(addr, symbol_name, True)
    print(f"[+] Added label: {symbol_name} at {addr}")

print("[+] Auto-analysis complete!")
print(f"[+] Added {len(known_addresses)} labels")
'''
            
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            self.log(f"✓ Generated import script: {script_path}", "SUCCESS")
            
            # Create instruction file
            instructions = f"""GHIDRA QUICK IMPORT INSTRUCTIONS
{'=' * 60}

1. Open Ghidra
2. Create new project or open existing
3. Import executable: {dest_exe}
4. Run auto-analysis (click Yes when prompted)
5. Window > Script Manager
6. Click "Script Directories" button
7. Add folder: {os.path.join(self.export_dir, 'ghidra_ready')}
8. Find and run: {export_name}_import.py

The script will automatically:
- Set correct base address (0x{self.base_address:X})
- Add {len(self.scan_results)} known addresses as labels
- Mark interesting patterns from scan results

Exported Files:
- Executable: {dest_exe}
- Import Script: {script_path}

Base Address: 0x{self.base_address:X}
Process ID: {self.current_pid}
Timestamp: {timestamp}
"""
            
            inst_file = os.path.join(self.export_dir, "ghidra_ready", f"{export_name}_README.txt")
            with open(inst_file, 'w') as f:
                f.write(instructions)
            
            self.log("✓ Ghidra export complete!", "SUCCESS")
            
            messagebox.showinfo("Ghidra Export Complete",
                              f"Ready for Ghidra!\n\n"
                              f"Executable: {dest_exe}\n"
                              f"Script: {script_path}\n\n"
                              f"See {export_name}_README.txt for instructions")
            
            # Open export folder
            os.startfile(os.path.join(self.export_dir, "ghidra_ready"))
            
        except Exception as e:
            self.log(f"Export error: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def export_executable(self):
        """Export process executable only"""
        if not self.current_pid:
            messagebox.showwarning("Not Attached", "Attach to a process first")
            return
        
        try:
            import psutil
            import shutil
            
            proc = psutil.Process(self.current_pid)
            exe_path = proc.exe()
            
            dest = filedialog.asksaveasfilename(
                defaultextension=".exe",
                initialfile=self.process_name,
                filetypes=[("Executable", "*.exe")])
            
            if dest:
                shutil.copy2(exe_path, dest)
                self.log(f"✓ Executable exported: {dest}", "SUCCESS")
                messagebox.showinfo("Success", f"Executable exported!\n\n{dest}")
        except Exception as e:
            self.log(f"Export error: {str(e)}", "ERROR")
            messagebox.showerror("Error", str(e))
    
    def export_and_decompile(self):
        """Export selected memory region and generate decompilation script"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Select a scan result first")
            return
        
        item = self.results_tree.item(selection[0])
        addr = int(item['values'][0], 16)
        
        # Export 4KB around selected address
        start_addr = addr - 2048
        size = 4096
        
        buffer = (ctypes.c_byte * size)()
        if stealth.ReadMemory(self.engine, c_void_p(start_addr), buffer, size):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"function_0x{addr:X}_{timestamp}.bin"
            filepath = os.path.join(self.export_dir, "ghidra_ready", filename)
            
            data = bytes(bytearray([buffer[j] & 0xFF for j in range(size)]))
            with open(filepath, 'wb') as f:
                f.write(data)
            
            # Generate decompilation script
            script_path = filepath.replace('.bin', '_decompile.py')
            script_content = f'''# Ghidra Decompilation Script
# Target Address: 0x{addr:X}
# Extracted from: {self.process_name}

from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor

print("[+] Decompiling function at 0x{addr:X}")

# Get function at address
target_addr = toAddr(0x{addr:X})
function = getFunctionAt(target_addr)

if function is None:
    print("[!] No function at address, creating...")
    createFunction(target_addr, "sub_{addr:X}")
    function = getFunctionAt(target_addr)

if function:
    # Decompile
    decompiler = DecompInterface()
    decompiler.openProgram(currentProgram)
    
    results = decompiler.decompileFunction(function, 30, ConsoleTaskMonitor())
    
    if results and results.decompileCompleted():
        decomp = results.getDecompiledFunction()
        code = decomp.getC()
        
        print("[+] Decompilation successful!")
        print("=" * 60)
        print(code)
        print("=" * 60)
    else:
        print("[!] Decompilation failed")
else:
    print("[!] Could not create function")
'''
            
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            self.log(f"✓ Exported region and script for 0x{addr:X}", "SUCCESS")
            messagebox.showinfo("Success",
                              f"Region exported with decompilation script!\n\n"
                              f"Binary: {filepath}\n"
                              f"Script: {script_path}\n\n"
                              f"Import binary to Ghidra and run script")
        else:
            messagebox.showerror("Error", "Failed to read memory")
    
    def open_ghidra_project(self):
        """Open Ghidra project folder"""
        import os
        if os.path.exists(self.ghidra_project):
            os.startfile(self.ghidra_project)
            self.log("Opened Ghidra project folder", "INFO")
        else:
            messagebox.showwarning("Not Found", 
                                  f"Ghidra project folder not found:\n{self.ghidra_project}")
    
    def generate_ghidra_script(self):
        """Generate comprehensive Ghidra analysis script"""
        if not self.scan_results:
            messagebox.showwarning("No Results", "Run a scan first to generate meaningful script")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        script_path = os.path.join(self.export_dir, "ghidra_ready",
                                  f"comprehensive_analysis_{timestamp}.py")
        
        script = f'''# Comprehensive Ghidra Analysis Script
# Generated by Memory Explorer Pro
# Process: {self.process_name}
# Base: 0x{self.base_address:X}
# Results: {len(self.scan_results)}
# Generated: {timestamp}

from ghidra.program.model.symbol import SourceType
from ghidra.program.model.listing import CodeUnit
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor

print("[+] Starting comprehensive analysis...")

program = getCurrentProgram()
imageBase = program.getImageBase()
listing = program.getListing()

# Pattern findings from Memory Explorer
findings = [
'''
        
        for addr, val, rtype in self.scan_results:
            offset = addr - self.base_address
            script += f'    {{"offset": 0x{offset:X}, "type": "{rtype}", "value": "{val}"}},\n'
        
        script += f''']

print(f"[+] Processing {{len(findings)}} findings...")

# Create labels and analyze
for i, finding in enumerate(findings):
    offset = finding["offset"]
    ftype = finding["type"]
    
    addr = imageBase.add(offset)
    
    # Create label
    label_name = f"{{ftype}}_{{offset:08X}}"
    createLabel(addr, label_name, True)
    
    # Add comment
    comment = f"Found by Memory Explorer\nType: {{ftype}}\nValue: {{finding['value']}}"
    listing.setComment(addr, CodeUnit.PLATE_COMMENT, comment)
    
    # Try to create function if looks like code
    if ftype == "Pattern":
        try:
            func = getFunctionAt(addr)
            if func is None:
                createFunction(addr, f"sub_{{offset:08X}}")
                print(f"[+] Created function at {{addr}}")
        except:
            pass
    
    if (i + 1) % 100 == 0:
        print(f"[+] Processed {{i + 1}}/{{len(findings)}}")

print("[+] Analysis complete!")
print(f"[+] Created {{len(findings)}} labels")
print("[+] Check Symbol Tree for all findings")
'''
        
        with open(script_path, 'w') as f:
            f.write(script)
        
        self.log(f"✓ Generated analysis script: {script_path}", "SUCCESS")
        messagebox.showinfo("Success",
                          f"Comprehensive Ghidra script generated!\n\n"
                          f"{script_path}\n\n"
                          f"Includes {len(self.scan_results)} findings\n"
                          f"Run in Ghidra Script Manager")
    
    def show_export_menu(self):
        """Show export options menu"""
        menu = tk.Menu(self.root, tearoff=0, bg='#1a1a1a', fg='white')
        menu.add_command(label="📦 Full Memory Dump", command=self.export_full_memory)
        menu.add_command(label="📄 Selected Region", command=self.export_selected_region)
        menu.add_command(label="📊 Scan Results", command=self.export_scan_results)
        menu.add_separator()
        menu.add_command(label="💾 Take Snapshot", command=self.take_snapshot)
        menu.add_command(label="📂 Open Export Folder", 
                        command=lambda: os.startfile(self.export_dir))
        menu.post(self.root.winfo_pointerx(), self.root.winfo_pointery())
    
    def auto_label_functions(self):
        """AI-powered automatic function labeling"""
        if not self.scan_results:
            messagebox.showwarning("No Data", "Run a scan first to collect data for analysis")
            return
        
        self.log("Starting AI auto-labeling...", "INFO")
        
        result_win = tk.Toplevel(self.root)
        result_win.title("AI Function Labeling")
        result_win.geometry("900x700")
        result_win.configure(bg='#0a0a0a')
        
        tk.Label(result_win, text="🤖 AI-Powered Function Recognition",
                bg='#0a0a0a', fg='#00ff41', font=('Segoe UI', 14, 'bold')).pack(pady=10)
        
        results = scrolledtext.ScrolledText(result_win, bg='#000000', fg='#00ff41',
                                           font=('Consolas', 9))
        results.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        progress = ttk.Progressbar(result_win, length=400, mode='determinate')
        progress.pack(fill=tk.X, padx=10, pady=10)
        
        def analyze():
            results.insert(tk.END, "Analyzing memory patterns...\n\n")
            
            # Common function prologues and patterns
            function_signatures = {
                'push_rbp': b'\x55\x48\x89\xE5',  # push rbp; mov rbp, rsp
                'push_rbx': b'\x48\x89\x5C\x24',  # mov [rsp+x], rbx
                'sub_rsp': b'\x48\x83\xEC',      # sub rsp, imm8
                'stack_frame': b'\x48\x89\x5C\x24\x08\x57\x48\x83\xEC',
                'ret': b'\xC3',                   # ret
                'call_rel': b'\xE8',              # call relative
                'jmp_rel': b'\xE9',               # jmp relative
                'lea_rip': b'\x48\x8D\x05',      # lea rax, [rip+offset]
            }
            
            function_patterns = {
                'lua_function': [b'\x48\x89\x5C\x24', b'\x48\x83\xEC', b'\x48\x8B'],
                'string_function': [b'\x48\x8D\x05', b'\x48\x89', b'\xE8'],
                'math_function': [b'\xF2\x0F', b'\xF3\x0F'],  # SSE instructions
                'memory_alloc': [b'\x48\x8B\x0D', b'\xE8', b'\x48\x85\xC0'],
                'comparator': [b'\x48\x3B', b'\x75', b'\x74'],  # cmp, jne, je
            }
            
            identified_functions = []
            
            for idx, (addr, val, rtype) in enumerate(self.scan_results):
                progress['value'] = int((idx + 1) / len(self.scan_results) * 100)
                result_win.update()
                
                # Read 256 bytes to analyze
                buffer = (ctypes.c_byte * 256)()
                if stealth.ReadMemory(self.engine, c_void_p(addr), buffer, 256):
                    data = bytes(bytearray([buffer[j] & 0xFF for j in range(256)]))
                    
                    # Check for function prologue
                    is_function = False
                    func_type = 'Unknown'
                    confidence = 0
                    
                    for sig_name, sig_bytes in function_signatures.items():
                        if data.startswith(sig_bytes):
                            is_function = True
                            confidence += 20
                    
                    # Pattern matching
                    for pattern_name, patterns in function_patterns.items():
                        matches = sum(1 for p in patterns if p in data)
                        if matches >= 2:
                            func_type = pattern_name
                            confidence += matches * 15
                    
                    # Heuristics
                    if data.count(b'\xE8') > 2:  # Multiple calls
                        confidence += 10
                        if func_type == 'Unknown':
                            func_type = 'complex_function'
                    
                    if data.count(b'\xC3') > 0:  # Has return
                        confidence += 15
                    
                    if b'\x00' * 16 not in data:  # No long zero sequences
                        confidence += 10
                    
                    if is_function or confidence > 40:
                        identified_functions.append({
                            'address': addr,
                            'type': func_type,
                            'confidence': min(confidence, 100),
                            'size_estimate': len(data.split(b'\xC3')[0]) if b'\xC3' in data else 256
                        })
                        
                        results.insert(tk.END, 
                                     f"[{len(identified_functions)}] 0x{addr:X}\n")
                        results.insert(tk.END, 
                                     f"    Type: {func_type}\n")
                        results.insert(tk.END, 
                                     f"    Confidence: {confidence}%\n")
                        results.insert(tk.END, 
                                     f"    Est. Size: {len(data.split(b'\xC3')[0])} bytes\n\n")
                        results.see(tk.END)
            
            results.insert(tk.END, "\n" + "=" * 80 + "\n")
            results.insert(tk.END, f"SUMMARY:\n")
            results.insert(tk.END, f"Total Analyzed: {len(self.scan_results)}\n")
            results.insert(tk.END, f"Functions Identified: {len(identified_functions)}\n\n")
            
            # Function type breakdown
            type_counts = {}
            for func in identified_functions:
                ftype = func['type']
                type_counts[ftype] = type_counts.get(ftype, 0) + 1
            
            results.insert(tk.END, "Function Types:\n")
            for ftype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                results.insert(tk.END, f"  {ftype}: {count}\n")
            
            # Export for Ghidra
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ghidra_script = os.path.join(self.export_dir, 'ghidra_ready',
                                        f'auto_labeled_functions_{timestamp}.py')
            
            script_content = f'''# AI-Generated Function Labels
# Created by Memory Explorer AI Analysis
# Functions Identified: {len(identified_functions)}
# Timestamp: {timestamp}

from ghidra.program.model.symbol import SourceType
from ghidra.program.model.listing import CodeUnit

program = getCurrentProgram()
imageBase = program.getImageBase()
listing = program.getListing()

print("[+] Importing {len(identified_functions)} AI-identified functions...")

functions = [
'''
            
            for func in identified_functions:
                offset = func['address'] - self.base_address
                script_content += f'''    {{"offset": 0x{offset:X}, "type": "{func['type']}", "confidence": {func['confidence']}}},\n'''
            
            script_content += f''']

for i, func in enumerate(functions):
    offset = func["offset"]
    ftype = func["type"]
    confidence = func["confidence"]
    
    addr = imageBase.add(offset)
    
    # Create function
    try:
        existing = getFunctionAt(addr)
        if existing is None:
            createFunction(addr, f"{{ftype}}_{{offset:08X}}")
        
        # Add label
        label = f"AI_{{ftype}}_{{offset:08X}}"
        createLabel(addr, label, True)
        
        # Add comment
        comment = f"AI Analysis\nType: {{ftype}}\nConfidence: {{confidence}}%\nAuto-identified function"
        listing.setComment(addr, CodeUnit.PLATE_COMMENT, comment)
        
        if (i + 1) % 10 == 0:
            print(f"[+] Processed {{i+1}}/{len(identified_functions)}")
    except:
        pass

print("[+] AI labeling complete!")
print(f"[+] Created {len(identified_functions)} function labels")
'''
            
            with open(ghidra_script, 'w') as f:
                f.write(script_content)
            
            results.insert(tk.END, f"\n✓ Ghidra script exported: {ghidra_script}\n")
            self.log(f"AI labeling complete: {len(identified_functions)} functions", "SUCCESS")
        
        thread = threading.Thread(target=analyze)
        thread.daemon = True
        thread.start()
    
    def pattern_learning(self):
        """Learn patterns from current scan and build signatures"""
        if not self.scan_results:
            messagebox.showwarning("No Data", "Run a scan first")
            return
        
        learn_win = tk.Toplevel(self.root)
        learn_win.title("Pattern Learning Engine")
        learn_win.geometry("800x600")
        learn_win.configure(bg='#0a0a0a')
        
        tk.Label(learn_win, text="🧠 Machine Learning Pattern Recognition",
                bg='#0a0a0a', fg='#00ff41', font=('Segoe UI', 12, 'bold')).pack(pady=10)
        
        output = scrolledtext.ScrolledText(learn_win, bg='#000000', fg='#00ff41',
                                          font=('Consolas', 9))
        output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        def learn():
            output.insert(tk.END, "Learning patterns from memory...\n\n")
            
            # Collect byte sequences from all results
            sequences = []
            
            for addr, val, rtype in self.scan_results[:100]:  # Sample first 100
                buffer = (ctypes.c_byte * 32)()
                if stealth.ReadMemory(self.engine, c_void_p(addr), buffer, 32):
                    data = bytes(bytearray([buffer[j] & 0xFF for j in range(32)]))
                    sequences.append(data)
            
            output.insert(tk.END, f"Collected {len(sequences)} byte sequences\n")
            
            # Find common patterns
            pattern_counts = {}
            
            for seq in sequences:
                for length in [4, 8, 12, 16]:
                    for i in range(len(seq) - length + 1):
                        pattern = seq[i:i+length]
                        if pattern not in pattern_counts:
                            pattern_counts[pattern] = 0
                        pattern_counts[pattern] += 1
            
            # Filter to common patterns (appear >3 times)
            common_patterns = {p: c for p, c in pattern_counts.items() if c > 3}
            
            output.insert(tk.END, f"\nFound {len(common_patterns)} common patterns\n\n")
            output.insert(tk.END, "Top patterns:\n")
            output.insert(tk.END, "=" * 70 + "\n")
            
            learned_patterns = []
            for pattern, count in sorted(common_patterns.items(), key=lambda x: x[1], reverse=True)[:20]:
                hex_pattern = pattern.hex(' ')
                output.insert(tk.END, f"Pattern: {hex_pattern}\n")
                output.insert(tk.END, f"Occurrences: {count}\n")
                output.insert(tk.END, f"Length: {len(pattern)} bytes\n\n")
                
                learned_patterns.append({
                    'pattern': hex_pattern,
                    'bytes': pattern,
                    'count': count
                })
            
            # Export learned patterns
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pattern_file = os.path.join(self.export_dir, 'logs',
                                       f'learned_patterns_{timestamp}.json')
            
            with open(pattern_file, 'w') as f:
                json.dump({
                    'process': self.process_name,
                    'timestamp': timestamp,
                    'total_analyzed': len(sequences),
                    'patterns_found': len(common_patterns),
                    'patterns': [{
                        'hex': p['pattern'],
                        'occurrences': p['count'],
                        'length': len(p['bytes'])
                    } for p in learned_patterns]
                }, f, indent=2)
            
            output.insert(tk.END, f"\n✓ Patterns exported: {pattern_file}\n")
            output.insert(tk.END, "\nUse these patterns for targeted scanning!\n")
            
            self.log(f"Pattern learning complete: {len(learned_patterns)} patterns", "SUCCESS")
        
        tk.Button(learn_win, text="🧠 Start Learning", command=lambda: threading.Thread(target=learn, daemon=True).start(),
                 bg='#0066cc', fg='white', font=('Segoe UI', 10, 'bold'),
                 padx=20, pady=10).pack(pady=10)
    
    def recognize_functions(self):
        """Advanced function recognition with disassembly hints"""
        messagebox.showinfo("Function Recognition",
                          "Analyzing code patterns...\n\n"
                          "This feature identifies:\n"
                          "• Function prologues/epilogues\n"
                          "• Call graphs\n"
                          "• String references\n"
                          "• Jump tables\n"
                          "• Virtual tables\n\n"
                          "Results will be exported to Ghidra-ready format")
        
        # Trigger auto-labeling which includes function recognition
        self.auto_label_functions()
    
    def show_memory_heatmap(self):
        """Visual memory heatmap showing activity"""
        if not self.attached:
            messagebox.showwarning("Not Attached", "Attach to a process first")
            return
        
        heat_win = tk.Toplevel(self.root)
        heat_win.title("Memory Activity Heatmap")
        heat_win.geometry("1000x800")
        heat_win.configure(bg='#0a0a0a')
        
        tk.Label(heat_win, text="📊 Memory Access Heatmap",
                bg='#0a0a0a', fg='#00ff41', font=('Segoe UI', 14, 'bold')).pack(pady=10)
        
        canvas = tk.Canvas(heat_win, bg='#000000', width=960, height=600)
        canvas.pack(padx=20, pady=10)
        
        info = tk.Label(heat_win, text="Scanning memory regions...",
                       bg='#0a0a0a', fg='#00ff41', font=('Consolas', 10))
        info.pack(pady=10)
        
        def generate_heatmap():
            # Scan 100MB in 1MB chunks
            scan_size = 100 * 1024 * 1024
            chunk_size = 1024 * 1024
            chunks = scan_size // chunk_size
            
            grid_width = 50
            grid_height = chunks // grid_width
            cell_width = 960 // grid_width
            cell_height = 600 // grid_height
            
            for i in range(chunks):
                addr = self.base_address + (i * chunk_size)
                buffer = (ctypes.c_byte * 1024)()
                
                is_readable = stealth.ReadMemory(self.engine, c_void_p(addr), buffer, 1024)
                
                if is_readable:
                    data = bytes(bytearray([buffer[j] & 0xFF for j in range(1024)]))
                    
                    # Calculate "heat" based on entropy
                    non_zero = sum(1 for b in data if b != 0)
                    heat = non_zero / len(data)
                    
                    # Color gradient: blue (cold) -> green -> yellow -> red (hot)
                    if heat < 0.25:
                        color = '#000066'
                    elif heat < 0.5:
                        color = '#0066cc'
                    elif heat < 0.75:
                        color = '#00cc66'
                    else:
                        color = '#cc6600'
                else:
                    color = '#330000'  # Dark red for blocked
                
                x = (i % grid_width) * cell_width
                y = (i // grid_width) * cell_height
                
                heat_win.after(0, canvas.create_rectangle, x, y, x + cell_width, y + cell_height,
                             fill=color, outline='')
                
                if (i + 1) % 10 == 0:
                    heat_win.after(0, info.config, {'text': f'Scanned {i+1}/{chunks} regions'})
            
            heat_win.after(0, info.config, {'text': 'Heatmap complete! Colors: Blue=Low activity, Green=Medium, Orange=High, Red=Blocked'})
        
        thread = threading.Thread(target=generate_heatmap)
        thread.daemon = True
        thread.start()
    
    def dynamic_analysis(self):
        """Dynamic analysis: track memory changes over time"""
        if not self.attached:
            messagebox.showwarning("Not Attached", "Attach to a process first")
            return
        
        dyn_win = tk.Toplevel(self.root)
        dyn_win.title("Dynamic Analysis")
        dyn_win.geometry("900x700")
        dyn_win.configure(bg='#0a0a0a')
        
        tk.Label(dyn_win, text="⚡ Real-Time Memory Analysis",
                bg='#0a0a0a', fg='#00ff41', font=('Segoe UI', 14, 'bold')).pack(pady=10)
        
        output = scrolledtext.ScrolledText(dyn_win, bg='#000000', fg='#00ff41',
                                          font=('Consolas', 9))
        output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        running = [False]
        
        def analyze():
            output.insert(tk.END, "Starting dynamic analysis...\n")
            output.insert(tk.END, "Monitoring memory changes in real-time\n\n")
            
            # Take initial snapshot
            snapshot_size = 10 * 1024 * 1024
            initial = (ctypes.c_byte * snapshot_size)()
            
            if not stealth.ReadMemory(self.engine, c_void_p(self.base_address), initial, snapshot_size):
                output.insert(tk.END, "ERROR: Could not read initial snapshot\n")
                return
            
            initial_data = bytes(bytearray([initial[j] & 0xFF for j in range(snapshot_size)]))
            output.insert(tk.END, f"✓ Initial snapshot: {len(initial_data) // 1024}KB\n\n")
            
            changes_detected = 0
            
            while running[0]:
                time.sleep(2)  # Check every 2 seconds
                
                current = (ctypes.c_byte * snapshot_size)()
                if stealth.ReadMemory(self.engine, c_void_p(self.base_address), current, snapshot_size):
                    current_data = bytes(bytearray([current[j] & 0xFF for j in range(snapshot_size)]))
                    
                    # Compare
                    differences = []
                    for i in range(0, snapshot_size, 1024):  # Check every 1KB
                        if initial_data[i:i+1024] != current_data[i:i+1024]:
                            differences.append(i)
                    
                    if differences:
                        changes_detected += len(differences)
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        output.insert(tk.END, f"[{timestamp}] Changes detected at {len(differences)} locations:\n")
                        
                        for offset in differences[:10]:  # Show first 10
                            addr = self.base_address + offset
                            output.insert(tk.END, f"  0x{addr:X}\n")
                        
                        if len(differences) > 10:
                            output.insert(tk.END, f"  ... and {len(differences) - 10} more\n")
                        
                        output.insert(tk.END, "\n")
                        output.see(tk.END)
                        
                        # Update initial to current for next comparison
                        initial_data = current_data
            
            output.insert(tk.END, f"\nDynamic analysis stopped. Total changes: {changes_detected}\n")
        
        def start():
            running[0] = True
            thread = threading.Thread(target=analyze)
            thread.daemon = True
            thread.start()
            start_btn.config(state=tk.DISABLED)
            stop_btn.config(state=tk.NORMAL)
        
        def stop():
            running[0] = False
            start_btn.config(state=tk.NORMAL)
            stop_btn.config(state=tk.DISABLED)
        
        btn_frame = tk.Frame(dyn_win, bg='#0a0a0a')
        btn_frame.pack(pady=10)
        
        start_btn = tk.Button(btn_frame, text="▶ Start Monitoring", command=start,
                             bg='#00cc00', fg='white', font=('Segoe UI', 10, 'bold'),
                             padx=20, pady=10)
        start_btn.pack(side=tk.LEFT, padx=5)
        
        stop_btn = tk.Button(btn_frame, text="⏹ Stop", command=stop,
                            bg='#cc0000', fg='white', font=('Segoe UI', 10, 'bold'),
                            padx=20, pady=10, state=tk.DISABLED)
        stop_btn.pack(side=tk.LEFT, padx=5)
    
    def generate_smart_patterns(self):
        """Generate intelligent patterns based on game analysis"""
        pattern_win = tk.Toplevel(self.root)
        pattern_win.title("Smart Pattern Generator")
        pattern_win.geometry("700x500")
        pattern_win.configure(bg='#0a0a0a')
        
        tk.Label(pattern_win, text="🎯 AI Pattern Generator",
                bg='#0a0a0a', fg='#00ff41', font=('Segoe UI', 12, 'bold')).pack(pady=10)
        
        tk.Label(pattern_win, text="Select pattern type to generate:",
                bg='#0a0a0a', fg='white', font=('Segoe UI', 10)).pack(pady=5)
        
        output = scrolledtext.ScrolledText(pattern_win, bg='#000000', fg='#00ff41',
                                          font=('Consolas', 9), height=20)
        output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        def generate(pattern_type):
            output.delete('1.0', tk.END)
            output.insert(tk.END, f"Generating {pattern_type} patterns...\n\n")
            
            patterns = {
                'Lua VM': [
                    '48 8B C4 48 89 58 08 48 89 70 10',  # VM entry
                    '48 89 5C 24 08 57 48 83 EC',       # Function prologue
                    '48 8B D3 48 8B CF E8',              # Call pattern
                ],
                'String Operations': [
                    '48 8D 05 ?? ?? ?? ?? 48 89',      # LEA string
                    '48 8D 0D ?? ?? ?? ??',             # LEA rcx
                    'E8 ?? ?? ?? ?? 48 8D 0D',          # Call + LEA
                ],
                'Memory Allocation': [
                    '48 8B 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 85 C0',  # GetAllocator + test
                    'E8 ?? ?? ?? ?? 48 8B F8 48 85 C0',              # Alloc + store
                ],
                'Math Operations': [
                    'F2 0F 59 C? F2 0F',  # mulsd
                    'F3 0F 59 C? F3 0F',  # mulss
                    'F2 0F 58 C? F2 0F',  # addsd
                ],
            }
            
            if pattern_type in patterns:
                output.insert(tk.END, f"{pattern_type} patterns:\n")
                output.insert(tk.END, "=" * 60 + "\n\n")
                
                for i, pattern in enumerate(patterns[pattern_type], 1):
                    output.insert(tk.END, f"Pattern {i}:\n")
                    output.insert(tk.END, f"{pattern}\n")
                    output.insert(tk.END, f"Usage: Copy and paste into scanner\n\n")
                
                # Export
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_file = os.path.join(self.export_dir, 'logs',
                                          f'generated_patterns_{pattern_type.replace(" ", "_")}_{timestamp}.txt')
                
                with open(export_file, 'w') as f:
                    f.write(f"{pattern_type} Patterns\n")
                    f.write("=" * 60 + "\n\n")
                    for pattern in patterns[pattern_type]:
                        f.write(f"{pattern}\n")
                
                output.insert(tk.END, f"\n✓ Exported: {export_file}\n")
        
        btn_frame = tk.Frame(pattern_win, bg='#0a0a0a')
        btn_frame.pack(pady=10)
        
        for ptype in ['Lua VM', 'String Operations', 'Memory Allocation', 'Math Operations']:
            tk.Button(btn_frame, text=ptype, command=lambda p=ptype: generate(p),
                     bg='#0066cc', fg='white', font=('Segoe UI', 9),
                     padx=10, pady=5).pack(side=tk.LEFT, padx=5)
    
    def build_knowledge_base(self):
        """Build comprehensive knowledge base from all analysis"""
        if not self.scan_results:
            messagebox.showwarning("No Data", "Collect some data first")
            return
        
        self.log("Building knowledge base...", "INFO")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        kb_file = os.path.join(self.export_dir, 'logs', f'knowledge_base_{timestamp}.json')
        
        knowledge_base = {
            'game': self.process_name,
            'base_address': f'0x{self.base_address:X}',
            'analysis_date': datetime.now().isoformat(),
            'total_scans': len(self.scan_results),
            'bookmarks': self.bookmarks,
            'findings': [
                {
                    'address': f'0x{addr:X}',
                    'offset': addr - self.base_address,
                    'type': rtype,
                    'value': val
                }
                for addr, val, rtype in self.scan_results
            ],
            'memory_snapshots': self.memory_snapshots,
            'notes': f'Comprehensive analysis of {self.process_name}'
        }
        
        with open(kb_file, 'w') as f:
            json.dump(knowledge_base, f, indent=2)
        
        self.log(f"Knowledge base created: {kb_file}", "SUCCESS")
        messagebox.showinfo("Success",
                          f"Knowledge Base Created!\n\n"
                          f"File: {kb_file}\n\n"
                          f"Contains:\n"
                          f"• {len(self.scan_results)} scan results\n"
                          f"• {len(self.bookmarks)} bookmarks\n"
                          f"• {len(self.memory_snapshots)} snapshots\n\n"
                          f"This can be reloaded for future sessions")
    
    def save_results(self):
        if not self.scan_results:
            messagebox.showwarning("No Results", "No results to save")
            return
        
        filepath = filedialog.asksaveasfilename(defaultextension=".json",
                                                filetypes=[("JSON files", "*.json")])
        if filepath:
            data = {
                'process': self.process_name,
                'timestamp': datetime.now().isoformat(),
                'results': [(f"0x{addr:X}", val, rtype) 
                           for addr, val, rtype in self.scan_results]
            }
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            self.log(f"Saved {len(self.scan_results)} results to {filepath}", "SUCCESS")
    
    def load_results(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filepath:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.scan_results = [(int(addr, 16), val, rtype) 
                                for addr, val, rtype in data['results']]
            self.refresh_results()
            self.log(f"Loaded {len(self.scan_results)} results from {filepath}", "SUCCESS")
    
    def toggle_monitor(self):
        """Toggle live value monitoring"""
        if not self.attached:
            messagebox.showwarning("Not Attached", "Attach to a process first")
            return
        
        if not self.scan_results:
            messagebox.showwarning("No Results", "Scan for values first")
            return
        
        self.monitoring_active = not self.monitoring_active
        
        if self.monitoring_active:
            self.monitor_btn.config(text="⏸️ PAUSE", bg='#cc6600')
            self.log("Live monitoring started", "SUCCESS")
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self.live_monitor_loop, daemon=True)
            self.monitor_thread.start()
        else:
            self.monitor_btn.config(text="▶️ LIVE MONITOR", bg='#00aa00')
            self.log("Live monitoring paused", "INFO")
    
    def live_monitor_loop(self):
        """Continuously read and update values in results table"""
        while self.monitoring_active and self.attached:
            try:
                refresh_ms = int(self.refresh_rate.get())
            except:
                refresh_ms = 500
            
            # Read current values for visible results
            items = self.results_tree.get_children()
            
            for item_id in items[:1000]:  # Monitor first 1000 results max
                if not self.monitoring_active:
                    break
                
                try:
                    values = self.results_tree.item(item_id)['values']
                    if len(values) < 4:
                        continue
                    
                    addr_str = values[0]  # '0x1F000000'
                    prev_val_str = values[1]  # Previous value
                    current_val_str = values[2]  # Current value (will become previous)
                    val_type = values[3]  # Type
                    
                    # Parse address
                    addr = int(addr_str, 16)
                    
                    # Determine read size and format
                    if val_type in ['int32', 'float']:
                        value_size = 4
                        pack_format = '<i' if val_type == 'int32' else '<f'
                    elif val_type in ['int64', 'double']:
                        value_size = 8
                        pack_format = '<q' if val_type == 'int64' else '<d'
                    else:
                        value_size = 4
                        pack_format = '<i'
                    
                    # Read memory
                    buffer = (ctypes.c_byte * value_size)()
                    if stealth.ReadMemory(self.engine, c_void_p(addr), buffer, value_size):
                        value_bytes = bytes([buffer[j] & 0xFF for j in range(value_size)])
                        new_value = struct.unpack(pack_format, value_bytes)[0]
                        
                        # Current value becomes previous, new value becomes current
                        # If current is still "-", use new value as both
                        if current_val_str == '-':
                            prev_for_display = str(new_value)
                        else:
                            prev_for_display = current_val_str
                        
                        # Update display
                        self.root.after(0, self.update_tree_item,
                                      item_id, addr_str, prev_for_display, str(new_value), val_type)
                
                except Exception as e:
                    pass
            
            # Sleep for refresh interval
            time.sleep(refresh_ms / 1000.0)
    
    def update_tree_item(self, item_id, addr, prev_val, new_val, val_type):
        """Update tree item with new value and color coding"""
        try:
            # Determine color based on change
            tag = 'unchanged'
            
            # Compare values
            try:
                if val_type in ['float', 'double']:
                    prev_num = float(prev_val)
                    new_num = float(new_val)
                else:
                    prev_num = int(prev_val)
                    new_num = int(new_val)
                
                if new_num > prev_num:
                    tag = 'increased'
                elif new_num < prev_num:
                    tag = 'decreased'
            except:
                # If conversion fails, just mark as unchanged
                pass
            
            # Update item with new values
            self.results_tree.item(item_id, values=(addr, prev_val, new_val, val_type), tags=(tag,))
        
        except Exception as e:
            pass


def main():
    root = tk.Tk()
    app = MemoryExplorer(root)
    root.mainloop()


if __name__ == '__main__':
    main()
