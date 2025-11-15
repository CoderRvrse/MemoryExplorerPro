# Memory Explorer Pro

Professional memory analysis and reverse engineering tool with kernel-level access via StealthEngine.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

## 🎯 Features

### Core Functionality
- **Kernel-Level Memory Access** - Undetected memory operations via StealthEngine driver
- **Process Attachment** - Attach to any running process with admin privileges
- **Memory Scanner** - Advanced scanning with multiple condition types
- **Hex Viewer/Editor** - View and edit raw memory in real-time
- **Live Monitoring** - Continuous value monitoring with configurable refresh rates

### Advanced Features
- **Multi-Condition Scanning**:
  - Exact Value
  - Unknown Initial Value
  - Increased/Decreased Value
  - Changed/Unchanged Value
  - Value Between Range
  - Bigger Than / Smaller Than
  - Increased/Decreased By Amount

- **Data Types**:
  - int32 (4 bytes)
  - int64 (8 bytes)
  - float
  - double
  - string
  - byte_array
  - pattern (AOB)

- **Export Capabilities**:
  - Full memory dumps (.dmp)
  - Selected region export
  - Scan results to JSON
  - Memory snapshots
  - Snapshot comparison

- **Ghidra Integration**:
  - Quick export for decompilation
  - Executable extraction
  - Auto-generate analysis scripts
  - Region export with metadata

- **AI-Assisted Analysis**:
  - Auto-label functions
  - Pattern learning mode
  - Function recognition
  - Memory heat maps
  - Dynamic analysis
  - Knowledge base building

## 🚀 Quick Start

### Installation

1. **Clone or extract** this project:
```bash
git clone https://github.com/yourusername/MemoryExplorerPro.git
cd MemoryExplorerPro
```

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Ensure StealthEngine is present**:
   - `StealthEngine/StealthEngine.dll` should exist
   - Run as Administrator for kernel driver access

### Launch

**Windows (double-click)**:
- `LAUNCH.bat`

**Command line**:
```bash
python MemoryExplorer.py
```

**PowerShell**:
```powershell
.\LAUNCH.ps1
```

## 📖 Usage Guide

### Basic Workflow

1. **Select Process**:
   - Click orange `⬇ SELECT PROCESS ⬇` button
   - Type process name or PID in search box
   - Double-click to attach

2. **First Scan**:
   - Choose value type (int32, float, etc.)
   - Select scan type (Exact Value, Unknown Initial Value, etc.)
   - Enter value if needed
   - Click `🔍 FIRST SCAN`

3. **Narrow Results**:
   - Change value in target game
   - Update scan condition (Increased Value, Changed Value, etc.)
   - Click `NEXT SCAN`
   - Repeat until < 100 results

4. **View/Edit Memory**:
   - Double-click result to view in hex editor
   - Use Memory Editor section to write bytes
   - Enable `▶️ LIVE MONITOR` to track value changes

### Advanced Techniques

#### Unknown Initial Value Scan
Perfect for finding values you don't know:
1. First Scan → "Unknown Initial Value"
2. Change value in game (spend money, take damage)
3. Next Scan → "Decreased Value" or "Increased Value"
4. Repeat until narrowed down

#### Pattern (AOB) Scanning
Find code signatures:
```
Pattern: 48 8B 05 ?? ?? ?? ?? 48 85 C0
```
- `??` represents wildcards
- Useful for code injection and hooking

#### Memory Snapshots
Track changes over time:
1. Export → "💾 Take Memory Snapshot" (before)
2. Perform action in game
3. Export → "💾 Take Memory Snapshot" (after)
4. Export → "📈 Compare Snapshots"

## 🛠️ Project Structure

```
MemoryExplorerPro/
├── MemoryExplorer.py          # Main application
├── StealthEngine/
│   └── StealthEngine.dll      # Kernel driver
├── Exports/
│   ├── memory_dumps/          # Full dumps (.dmp)
│   ├── ghidra_ready/          # Exported regions
│   └── logs/                  # Scan results, diffs
├── GhidraProjects/            # Auto-created
├── requirements.txt           # Python dependencies
├── .gitignore                 # Git exclusions
├── LAUNCH.bat                 # Windows launcher
├── LAUNCH.ps1                 # PowerShell launcher
└── README.md                  # This file
```

## 🔧 Configuration

### Scan Range
Default: Auto-detects Unity heap or uses base address
- Start: `0x7FF600000000` (typical 64-bit base)
- Size: Auto-detected (50-200 MB)

### Performance Settings
- Chunk size: 1 MB (adjust for speed vs accuracy)
- Max results: 100,000 (prevents UI freeze)
- Refresh rate: 500ms (for live monitoring)

## 🎮 Example: Find Game Money

1. **Attach** to game process
2. **First Scan** → Value Type: `int32`, Scan Type: `Exact Value`, Value: `1000` (your current money)
3. **Spend/earn money** in game
4. **Next Scan** → Value Type: `int32`, Scan Type: `Exact Value`, Value: `950` (new amount)
5. Repeat until **< 10 results**
6. **Double-click** each result to verify in hex viewer
7. **Write memory** to set custom value

## 🚨 Troubleshooting

### "Failed to create StealthEngine"
- Run as Administrator
- Ensure `StealthEngine/StealthEngine.dll` exists
- Check Windows Defender exclusions

### "Failed to attach to process"
- Process must be running
- Requires admin privileges
- Some processes have anti-cheat protection

### "No results found"
- Value type mismatch (try int64 or float)
- Value stored in different region (increase scan range)
- Value is calculated/cached elsewhere

### Slow scanning
- Reduce scan range (Start + Size)
- Use "Unknown Initial Value" first, then narrow
- Close other applications

## 🔒 Legal Disclaimer

This tool is for **educational and research purposes only**. Use only on:
- Games you own
- Software you have permission to analyze
- Your own applications for debugging

**DO NOT USE** for:
- Online multiplayer games (violates ToS)
- Bypassing DRM or copy protection
- Cheating in competitive games
- Any illegal activity

The developers are not responsible for misuse.

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📜 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🙏 Credits

- **StealthEngine** - Kernel-level memory driver
- **Cheat Engine** - Inspiration for scan techniques
- **Ghidra** - Integration for reverse engineering

## 📞 Support

- Issues: [GitHub Issues](https://github.com/yourusername/MemoryExplorerPro/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/MemoryExplorerPro/discussions)

---

Made with ❤️ by the Memory Explorer Pro team
