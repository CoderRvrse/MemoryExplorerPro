# Changelog

All notable changes to Memory Explorer Pro will be documented in this file.

## [2.0.0] - 2025-11-15

### 🎯 Major Improvements
- **Enhanced Memory Scanning Algorithm** - Professional-grade region validation
- **Advanced Region Detection** - MEM_PRIVATE, MEM_IMAGE, and MEM_MAPPED classification
- **Better Game Compatibility** - Works with Unity, Unreal, Native, and all game engines
- **Improved Protection Filtering** - Advanced writable/executable/copyonwrite detection

### ✨ Features
- Multi-type memory region prioritization (PRIVATE → IMAGE → MAPPED)
- Smart protection flag filtering (PAGE_GUARD, PAGE_NOCACHE exclusion)
- Comprehensive region enumeration across full address space
- Real-time region scanning with progress updates

### 🔧 Technical
- Enhanced VirtualQueryEx validation logic
- Proper MEM_COMMIT state checking
- Advanced protection bit masking
- Optimized region enumeration (up to 128TB address space)

### 📈 Performance
- Faster region detection
- More accurate memory filtering
- Better scan result quality

## [1.0.0] - 2025-11-14

### Initial Release
- Kernel-level memory access via StealthEngine
- Process attachment and memory scanning
- Hex viewer/editor
- Live value monitoring
- Export capabilities (DMP, JSON)
- Ghidra integration
- AI-assisted analysis
