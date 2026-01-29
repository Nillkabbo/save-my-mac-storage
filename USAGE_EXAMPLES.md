# 🍎 macOS Cleaner - Usage Examples

## 📊 Detailed Analysis GUI (NEW!)

The new Detailed Analysis GUI provides precise control and visibility into your storage:

### Launch Options
```bash
# Quick launcher (recommended)
./run_cleaner.sh
# Choose option 2 for Detailed Analysis GUI

# Direct launch
mac-cleaner detailed-gui
```

### Key Features

#### 1. **Directory Selection**
- Browse any directory on your system
- Quick access buttons for common locations:
  - 📁 Caches
  - 📝 Logs  
  - 🗑️ Trash
  - 🌐 Browser Cache

#### 2. **File Analysis**
For each file, you'll see:
- **Exact Path**: Full file location
- **Size**: Human-readable size (B, KB, MB, GB)
- **Modified Date**: Last modification time
- **Safety Level**: Critical, Important, Moderate, Safe, Very Safe
- **Recommendation**: Keep, Review, Delete, Skip
- **Full Path**: Complete file path for manual navigation

#### 3. **Safety Scoring System**
Files are scored 0-100 based on:
- File extension importance
- File age (older = less important)
- File size
- Hidden status
- Location (system vs user directories)

#### 4. **Color-Coded Safety Levels**
- 🔴 **Critical** (80-100): System files, important documents
- 🟠 **Important** (60-79): User documents, preferences
- 🟡 **Moderate** (40-59): Unknown importance
- 🟢 **Safe** (20-39): Temporary files, old data
- 🔵 **Very Safe** (0-19): Cache, temp files

#### 5. **Finder Integration**
- **"Open in Finder"** button for selected directory
- **Double-click** any file to open its location in Finder
- **Right-click** context menu coming soon

#### 6. **Filtering Options**
Filter files by safety level:
- All files
- Very Safe only
- Safe only  
- Moderate only
- Important only
- Critical only

#### 7. **Special Analysis Tools**
- **📊 Top Space Consumers**: Shows largest files first
- **📅 Old Files**: Files older than 30 days
- **💾 Export Analysis**: Save detailed analysis to JSON

## 🎯 Real-World Usage Scenarios

### Scenario 1: Storage Almost Full
**Problem**: Your Mac is running out of space and applications are slowing down.

**Solution**:
1. Launch Detailed Analysis GUI
2. Select your user directory: `/Users/yourname`
3. Click "Analyze"
4. Filter by "Very Safe" and "Safe"
5. Sort by size (largest first)
6. Double-click large files to open in Finder
7. Manually review and delete what you don't need

### Scenario 2: Application Memory Issues
**Problem**: Applications pause during work due to memory pressure.

**Solution**:
1. Click "📁 Caches" quick access button
2. Analyze the cache directory
3. Look for large cache files (often browser caches)
4. Open in Finder and manually delete
5. Repeat for "🌐 Browser Cache"

### Scenario 3: Finding Large Hidden Files
**Problem**: You suspect large hidden files are consuming space.

**Solution**:
1. Browse to root directory or user directory
2. Analyze and look for files with high size but "Safe" rating
3. Use "📊 Top Space Consumers" to find largest files
4. Open in Finder to investigate

### Scenario 4: Cleaning Old Downloads
**Problem**: Downloads folder has accumulated old files.

**Solution**:
1. Browse to `/Users/yourname/Downloads`
2. Analyze the directory
3. Use "📅 Old Files" to find files older than 30 days
4. Review safety ratings and recommendations
5. Open in Finder to manually clean

## 📋 File Safety Examples

### ✅ Safe to Delete (Usually)
```
/Users/yourname/Library/Caches/com.apple.Safari/
/Users/yourname/Library/Caches/Google/Chrome/
/tmp/tempfile123.tmp
/Users/yourname/.Trash/
/Users/yourname/Downloads/old-installer.dmg
```

### ⚠️ Review Before Deleting
```
/Users/yourname/Documents/old-project/
/Users/yourname/Library/Preferences/com.apple.someapp.plist
/Users/yourname/Library/Application Support/old-app/
```

### 🚫 Do Not Delete
```
/System/Library/
/Library/Keychains/
/Users/yourname/Library/Keychains/
/Users/yourname/Documents/current-work/
```

## 🔍 Manual Investigation Workflow

### Step 1: Identify Problem Areas
```bash
# Check overall disk usage
df -h

# Find large directories
du -sh /Users/yourname/* | sort -hr | head -10
```

### Step 2: Use Detailed Analysis GUI
1. Launch the GUI
2. Select the large directory found above
3. Analyze and filter by safety level
4. Export analysis for record-keeping

### Step 3: Manual Cleanup
1. Use "Open in Finder" to navigate
2. Review files manually
3. Delete what you're comfortable removing
4. Empty Trash when confident

## 📊 Understanding File Analysis

### Example File Analysis Output
```json
{
  "path": "/Users/yourname/Library/Caches/com.apple.Safari/Cache.db",
  "name": "Cache.db",
  "size": 52428800,
  "size_human": "50.00 MB",
  "modified": "2023-12-01 10:30:45",
  "safety_level": "very_safe",
  "recommendation": "delete",
  "importance_score": 15
}
```

### Safety Level Determination
- **File Extension**: `.cache`, `.tmp`, `.log` = Lower importance
- **Location**: `/Library/Caches/`, `/tmp/` = Lower importance  
- **Age**: Files older than 30 days = Lower importance
- **Size**: Very small files (< 1KB) = Lower importance

## 🛠️ Advanced Usage

### Export Analysis for Review
```bash
# Analysis exported to JSON
{
  "files": [...],
  "summary": {
    "total_files": 1500,
    "total_size": "2.5 GB",
    "deletable_size": "1.8 GB"
  }
}
```

### Command Line Analysis (for scripts)
```python
from mac_cleaner.file_analyzer import FileAnalyzer

analyzer = FileAnalyzer()
summary = analyzer.get_directory_summary('/Users/yourname/Library/Caches')
print(f"Deletable: {analyzer.format_bytes(summary['deletable_size'])}")
```

## ⚡ Quick Tips

1. **Start with Safe Areas**: Always begin with Caches and Trash
2. **Check File Size**: Large files with low safety scores are good candidates
3. **Use Finder Integration**: Double-click to verify file location manually
4. **Export Before Deleting**: Keep a record of what you plan to remove
5. **Work in Sections**: Clean one directory at a time to avoid mistakes

## 🆚 Comparison with Other Cleaners

| Feature | Other Cleaners | macOS Cleaner (Detailed) |
|---------|----------------|---------------------------|
| File Visibility | Limited | Full paths and details |
| User Control | Automatic | Manual decision making |
| Safety | Basic | Advanced scoring system |
| Finder Integration | No | Yes (double-click) |
| Export Analysis | No | Yes (JSON export) |
| Precise Control | No | Yes (file-by-file) |

## 📞 Getting Help

If you're unsure about a file:
1. Check its safety level and recommendation
2. Double-click to open in Finder
3. Search online for the filename/path
4. When in doubt, don't delete it

Remember: **You are in control** - this tool provides information, but you make the decisions!
