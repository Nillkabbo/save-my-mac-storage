# Architecture Documentation

## Overview

The macOS Cleaner is designed as a modular, extensible system for disk usage analysis with a focus on safety and security. The architecture follows a layered approach with clear separation of concerns.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interfaces Layer                      │
├─────────────────┬─────────────────┬─────────────────────────┤
│   CLI Interface  │   Web Interface  │   GUI Interface          │
│   (cli.py)       │   (web_gui.py)   │   (gui_cleaner.py)       │
└─────────────────┴─────────────────┴─────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Plugin Architecture                        │
├─────────────────────────────────────────────────────────────┤
│  Plugin Manager  │  Plugin Base    │  Built-in Plugins       │
│  (interfaces.py)  │  Classes        │  (plugins.py)            │
└─────────────────┴─────────────────┴─────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Core Services Layer                       │
├─────────────────┬─────────────────┬─────────────────────────┤
│   MacCleaner     │  SpaceAnalyzer  │  SafetyManager           │
│   (mac_cleaner)  │  (space_analyzer)│  (safety_manager.py)     │
└─────────────────┴─────────────────┴─────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Security & Utilities                       │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Security       │  Config Manager │  File Analyzer          │
│   (security.py)  │  (config_manager)│  (file_analyzer.py)      │
└─────────────────┴─────────────────┴─────────────────────────┘
```

## Core Components

### 1. User Interfaces Layer

#### CLI Interface (`cli.py`)
- **Purpose**: Command-line interface for scripting and automation
- **Framework**: Click-based CLI with subcommands
- **Features**:
  - Plugin-based analysis
  - JSON output support
  - Configuration file support
  - Comprehensive help system

#### Web Interface (`web_gui.py`)
- **Purpose**: Browser-based interface for remote access
- **Framework**: Flask web application
- **Features**:
  - RESTful API endpoints
  - CSRF protection
  - Rate limiting
  - Real-time status updates

#### GUI Interface (`gui_cleaner.py`, `detailed_gui.py`)
- **Purpose**: Native desktop interface
- **Framework**: Tkinter-based GUI
- **Features**:
  - Interactive file analysis
  - Progress indicators
  - Finder integration

### 2. Plugin Architecture

#### Plugin Manager (`interfaces.py`)
```python
class PluginManager:
    """Central plugin management system"""
    
    def register_plugin(self, plugin: CleanerPlugin)
    def get_plugin(self, name: str) -> CleanerPlugin
    def get_plugins_by_category(self, category: str)
    def analyze_all(self) -> Dict
    def clean_all(self, categories: List[str]) -> Dict
```

#### Plugin Base Classes
```python
class CleanerPlugin(ABC):
    """Abstract base class for all plugins"""
    
    @property
    @abstractmethod
    def name(self) -> str
    
    @property
    @abstractmethod
    def category(self) -> str
    
    @abstractmethod
    def get_cleanable_paths(self) -> List[str]
    
    @abstractmethod
    def is_safe_to_clean(self, path: str) -> bool
```

#### Built-in Plugins (`plugins.py`)
- **Browser Cache Cleaner**: Chrome, Safari, Firefox caches
- **System Cache Cleaner**: System-level caches
- **Log File Cleaner**: Application and system logs
- **Temporary File Cleaner**: Temp directories
- **Xcode Cleaner**: Development artifacts
- **Docker Cleaner**: Container resources
- **Downloads Cleaner**: User downloads analysis

### 3. Core Services Layer

#### MacCleaner (`mac_cleaner.py`)
```python
class MacCleaner:
    """Main analysis engine"""
    
    def __init__(self)
    def get_system_info(self) -> Dict
    def analyze_category(self, category: str) -> Dict
    def clean_category(self, category: str, dry_run: bool) -> Dict
    def clean_all(self, dry_run: bool) -> Dict
```

**Key Features:**
- Read-only analysis mode
- Path validation and safety checks
- Comprehensive logging
- Progress tracking

#### SpaceAnalyzer (`space_analyzer.py`)
```python
class SpaceAnalyzer:
    """Comprehensive disk usage analyzer"""
    
    def generate_report(self) -> Dict
    def analyze_user_directories(self) -> Dict
    def find_large_files(self, limit: int) -> List
    def find_old_files(self, days: int) -> List
    def analyze_system_caches(self) -> Dict
```

**Analysis Capabilities:**
- Disk usage breakdown
- Large file identification
- Old file detection
- Cache analysis
- Recommendation engine

#### SafetyManager (`safety_manager.py`)
```python
class SafetyManager:
    """Safety and backup management"""
    
    def create_backup(self, path: str) -> bool
    def restore_backup(self, backup_name: str) -> bool
    def list_backups(self) -> List[Dict]
    def is_path_safe(self, path: str) -> bool
    def cleanup_old_backups(self, days: int)
```

**Safety Features:**
- Automatic backup creation
- Path safety validation
- Backup restoration
- Cleanup management

### 4. Security & Utilities

#### Security Module (`security.py`)
```python
def sanitize_shell_input(value: str) -> str
def validate_finder_path(path: str, allowed_roots: List[str]) -> Tuple[bool, str, str]
def is_path_within(path: str, allowed_roots: List[str]) -> bool
```

**Security Features:**
- Input sanitization
- Path traversal prevention
- Command injection protection
- Access control

#### Configuration Manager (`config_manager.py`)
```python
@dataclass
class MacCleanerConfig:
    cleaner: CleanerConfig
    security: SecurityConfig
    web: WebConfig
    logging: LoggingConfig
```

**Configuration Features:**
- YAML-based configuration
- Environment variable overrides
- Validation and defaults
- Runtime updates

#### File Analyzer (`file_analyzer.py`)
```python
class FileAnalyzer:
    """Detailed file analysis and scoring"""
    
    def analyze_file(self, path: str) -> Dict
    def calculate_importance_score(self, path: str) -> int
    def get_safety_level(self, path: str) -> str
    def get_deletion_recommendation(self, path: str) -> str
```

## Data Flow

### Analysis Flow
```
1. User Request (CLI/Web/GUI)
       ↓
2. Input Validation & Security Check
       ↓
3. Plugin Selection (if specified)
       ↓
4. Path Analysis (read-only)
       ↓
5. Results Aggregation
       ↓
6. Report Generation
       ↓
7. User Interface Update
```

### Plugin Execution Flow
```
1. Plugin Registration
       ↓
2. Path Discovery
       ↓
3. Safety Validation
       ↓
4. Size Calculation
       ↓
5. File Counting
       ↓
6. Result Formatting
       ↓
7. Return to Manager
```

## Security Architecture

### Defense in Depth

1. **Input Layer**
   - Command injection prevention
   - Path traversal protection
   - Input sanitization

2. **Application Layer**
   - CSRF protection (web)
   - Rate limiting (web)
   - Permission checks

3. **Data Layer**
   - Read-only operations only
   - Path validation
   - Safe file access

### Security Controls

```python
# Path validation
def validate_path(path: str, allowed_prefixes: List[str]) -> bool:
    real_path = os.path.realpath(path)
    return any(real_path.startswith(prefix) for prefix in allowed_prefixes)

# Input sanitization
def sanitize_input(input_str: str) -> str:
    return shlex.quote(input_str)

# Access control
def is_path_safe(path: str) -> bool:
    return not any(path.startswith(protected) for protected in PROTECTED_PATHS)
```

## Configuration Architecture

### Configuration Hierarchy
```
1. Default Values (built-in)
       ↓
2. Configuration File (YAML)
       ↓
3. Environment Variables
       ↓
4. Command Line Arguments
```

### Configuration Structure
```yaml
cleaner:
  protected_paths: [...]
  backup_enabled: true
  dry_run_default: true

security:
  require_confirmation: true
  allow_system_paths: false
  csrf_enabled: true

web:
  host: "127.0.0.1"
  port: 5000
  csrf_enabled: true

logging:
  level: "INFO"
  file_enabled: true
  console_enabled: true
```

## Testing Architecture

### Test Structure
```
tests/
├── unit/                    # Unit tests
│   ├── test_cleaner.py
│   ├── test_analyzer.py
│   └── test_plugins.py
├── integration/             # Integration tests
│   ├── test_web_api.py
│   └── test_cli.py
├── fixtures/                # Test data
└── conftest.py             # Test configuration
```

### Testing Strategy

1. **Unit Tests**
   - Individual component testing
   - Mock external dependencies
   - Fast execution

2. **Integration Tests**
   - Component interaction testing
   - Real filesystem usage
   - API endpoint testing

3. **Security Tests**
   - Input validation testing
   - Path traversal testing
   - CSRF protection testing

## Performance Considerations

### Optimization Strategies

1. **Lazy Loading**
   - Load plugins on demand
   - Delay expensive operations

2. **Caching**
   - Cache system information
   - Cache analysis results

3. **Async Operations**
   - Background analysis
   - Non-blocking UI updates

4. **Memory Management**
   - Stream large file processing
   - Limit concurrent operations

### Performance Metrics

```python
# Analysis performance
def analyze_directory(path: Path) -> Dict:
    start_time = time.time()
    result = _perform_analysis(path)
    duration = time.time() - start_time
    
    return {
        **result,
        "analysis_time": duration,
        "files_per_second": len(result["files"]) / duration
    }
```

## Error Handling Architecture

### Error Categories

1. **User Errors**
   - Invalid input
   - Permission denied
   - Path not found

2. **System Errors**
   - Disk full
   - Network issues
   - Resource exhaustion

3. **Application Errors**
   - Plugin failures
   - Configuration errors
   - Internal exceptions

### Error Handling Strategy

```python
try:
    result = perform_operation()
except ValidationError as e:
    return {"success": False, "error": str(e), "type": "validation"}
except PermissionError as e:
    return {"success": False, "error": str(e), "type": "permission"}
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return {"success": False, "error": "Internal error", "type": "internal"}
```

## Extensibility Architecture

### Plugin Development

1. **Plugin Interface**
   - Implement `CleanerPlugin` base class
   - Define metadata and methods
   - Register with plugin manager

2. **Plugin Distribution**
   - Separate plugin packages
   - Plugin discovery mechanism
   - Version compatibility

3. **Custom Configuration**
   - Plugin-specific settings
   - Configuration validation
   - Runtime configuration

### Extension Points

1. **Analysis Plugins**
   - Custom file type analysis
   - Specialized directory handling
   - Application-specific logic

2. **Output Plugins**
   - Custom report formats
   - Integration with external tools
   - Notification systems

3. **Interface Plugins**
   - Custom UI components
   - Alternative interfaces
   - Integration platforms

## Deployment Architecture

### Deployment Options

1. **Development**
   - Local installation
   - Virtual environment
   - Development server

2. **Production**
   - Package installation
   - System service
   - Container deployment

3. **Distribution**
   - PyPI package
   - Homebrew formula
   - Docker image

### Deployment Considerations

1. **Security**
   - Read-only operation mode
   - Minimal permissions
   - Sandboxed execution

2. **Performance**
   - Resource limits
   - Timeout handling
   - Memory constraints

3. **Reliability**
   - Error recovery
   - Graceful degradation
   - Logging and monitoring

## Future Architecture Evolution

### Planned Enhancements

1. **Microservices Architecture**
   - Separate analysis services
   - API gateway
   - Service discovery

2. **Cloud Integration**
   - Cloud storage analysis
   - Remote analysis services
   - Distributed processing

3. **AI/ML Integration**
   - Intelligent recommendations
   - Pattern recognition
   - Predictive analysis

### Migration Strategy

1. **Backward Compatibility**
   - Maintain existing APIs
   - Gradual migration path
   - Deprecation notices

2. **Incremental Updates**
   - Feature flags
   - A/B testing
   - Canary deployments

This architecture provides a solid foundation for the macOS Cleaner's current functionality while allowing for future growth and enhancement. The modular design ensures maintainability, extensibility, and security throughout the system's lifecycle.
