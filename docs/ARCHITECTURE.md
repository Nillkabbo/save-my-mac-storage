# Architecture Documentation

## Overview

The macOS Cleaner is designed as a modular, extensible system for disk usage analysis with a focus on safety and security. The architecture follows a layered approach with clear separation of concerns and a modern plugin-based design.

## Phase 3: Enhanced Architecture (Latest)

### New Plugin-Based Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interfaces Layer                      │
├─────────────────┬─────────────────┬─────────────────────────┤
│   CLI Interface  │   Web Interface  │   GUI Interface          │
│   (cli.py)       │   (web_gui.py)   │   (gui_cleaner.py)       │
│   Enhanced       │   Enhanced       │   Enhanced               │
└─────────────────┴─────────────────┴─────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                Enhanced Plugin Architecture                    │
├─────────────────┬─────────────────┬─────────────────────────┤
│  Enhanced       │  Enhanced        │  Enhanced Built-in       │
│  Plugin Manager │  Plugin Base     │  Plugins                 │
│  (interfaces.py)│  Classes         │  (plugins.py)            │
│  + Registry     │  + Safety Levels  │  + Priorities            │
│  + Discovery    │  + Config        │  + Validation            │
└─────────────────┴─────────────────┴─────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Enhanced Core Layer                       │
├─────────────────┬─────────────────┬─────────────────────────┤
│  Enhanced        │  Configuration  │  Legacy Components       │
│  Cleaner         │  Manager        │  (mac_cleaner.py)        │
│  (enhanced_      │  (config_       │  (space_analyzer.py)     │
│  cleaner.py)     │  manager.py)    │  (safety_manager.py)     │
└─────────────────┴─────────────────┴─────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Security & Utilities                       │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Enhanced       │  Enhanced        │  File Analyzer          │
│   Security       │  Config         │  (file_analyzer.py)      │
│   (security.py)  │  Interfaces      │                          │
└─────────────────┴─────────────────┴─────────────────────────┘
```

## Enhanced Components (Phase 3)

### 1. Enhanced Interface Pattern

#### New Interfaces (`interfaces.py`)
```python
# Enhanced enums for better type safety
class OperationMode(Enum):
    ANALYZE = "analyze"
    DRY_RUN = "dry_run"
    CLEAN = "clean"

class SafetyLevel(Enum):
    CRITICAL = "critical"      # Never clean
    IMPORTANT = "important"    # Require confirmation
    MODERATE = "moderate"      # Generally safe
    SAFE = "safe"              # Safe to clean
    VERY_SAFE = "very_safe"    # Always safe

# Enhanced dataclasses for structured data
@dataclass
class CleaningResult:
    path: str
    operation: str
    success: bool
    size_freed: int = 0
    safety_level: SafetyLevel = SafetyLevel.SAFE

@dataclass
class AnalysisResult:
    path: str
    size_bytes: int
    file_count: int
    safety_level: SafetyLevel
    last_modified: Optional[str] = None

# Enhanced interfaces with better abstractions
class CleanerInterface(Protocol):
    def analyze(self, paths: Optional[List[str]] = None) -> Dict[str, Any]
    def clean(self, dry_run: bool = True, paths: Optional[List[str]] = None) -> Dict[str, Any]
    def get_safety_info(self, path: str) -> SafetyLevel
    def validate_operation(self, operation: OperationMode, paths: List[str]) -> bool

class ConfigInterface(Protocol):
    def get(self, key: str, default: Any = None) -> Any
    def set(self, key: str, value: Any) -> None
    def load(self, source: Union[str, Dict[str, Any]]) -> None
    def save(self, target: Optional[str] = None) -> None
    def validate(self) -> bool

class SecurityInterface(Protocol):
    def validate_path(self, path: str, allowed_prefixes: List[str]) -> bool
    def sanitize_input(self, input_str: str) -> str
    def check_privileges(self, path: str) -> bool
    def is_protected_path(self, path: str) -> bool
```

#### Enhanced Plugin Base Class
```python
class CleanerPlugin(ABC):
    """Enhanced base class for cleaner plugins"""
    
    def __init__(self, config: Optional[ConfigInterface] = None):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def author(self) -> str:
        return "macOS Cleaner contributors"
    
    @property
    def enabled(self) -> bool:
        return True
    
    @property
    def priority(self) -> int:
        return 50  # Higher = runs first
    
    def get_safety_level(self, path: str) -> SafetyLevel:
        """Enhanced safety level determination"""
        
    def can_handle_path(self, path: str) -> bool:
        """Check if plugin can handle the given path"""
        
    def validate_paths(self, paths: List[str]) -> List[str]:
        """Validate and filter paths"""
```

### 2. Enhanced Plugin Manager

#### New Features
```python
class PluginManager:
    """Enhanced manager for loading and running plugins"""
    
    def __init__(self, config: Optional[ConfigInterface] = None):
        self.config = config
        self.plugins: Dict[str, CleanerPlugin] = {}
        self.categories: Dict[str, List[CleanerPlugin]] = {}
        self.plugin_registry: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    # Enhanced registration with validation
    def register_plugin(self, plugin: CleanerPlugin) -> bool:
        """Register a plugin with validation"""
        
    # Plugin lifecycle management
    def unregister_plugin(self, name: str) -> bool:
    def enable_plugin(self, name: str) -> bool:
    def disable_plugin(self, name: str) -> bool:
    
    # Enhanced discovery system
    def discover_plugins(self, plugin_paths: Optional[List[str]] = None) -> int:
        """Discover and load plugins from specified paths"""
    
    # Registry and information
    def get_plugin_info(self, name: str) -> Optional[Dict[str, Any]]:
    def get_all_plugin_info(self) -> Dict[str, Dict[str, Any]]:
    
    # Enhanced analysis and cleaning
    def analyze_all(self, categories: Optional[List[str]] = None, 
                   paths: Optional[List[str]] = None) -> Dict[str, Any]:
    def clean_all(self, categories: Optional[List[str]] = None,
                  paths: Optional[List[str]] = None, dry_run: bool = True) -> Dict[str, Any]:
```

### 3. Enhanced Configuration Management

#### New Configuration System (`core/config_manager.py`)
```python
# Structured configuration dataclasses
@dataclass
class SecurityConfig:
    require_confirmation: bool = True
    allow_system_paths: bool = False
    max_file_size_mb: int = 1000
    protected_paths: List[str] = field(default_factory=lambda: [
        "/System", "/usr/bin", "/Library/Keychains", "/etc", "/var/root"
    ])

@dataclass
class BackupConfig:
    enabled: bool = True
    backup_dir: str = "~/.mac_cleaner_backup"
    max_backup_age_days: int = 30
    auto_cleanup: bool = True

@dataclass
class PluginConfig:
    enabled_plugins: List[str] = field(default_factory=list)
    disabled_plugins: List[str] = field(default_factory=list)
    plugin_directories: List[str] = field(default_factory=lambda: [
        "src.mac_cleaner.plugins", "mac_cleaner_plugins"
    ])
    auto_discover: bool = True

# Enhanced configuration manager implementing ConfigInterface
class ConfigurationManager(ConfigInterface):
    """Enhanced configuration manager implementing ConfigInterface"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self._get_default_config_file()
        self.config = CleanerConfig()
        self._dirty = False
    
    # Dot notation access
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation"""
    
    # Multiple format support (YAML, JSON)
    def load(self, source: Union[str, Dict[str, Any]]) -> None:
    def save(self, target: Optional[str] = None) -> None:
    
    # Validation and merging
    def validate(self) -> bool:
    def merge(self, other_config: Union['ConfigurationManager', Dict[str, Any]]) -> None:
```

### 4. Enhanced Cleaner Implementation

#### New Enhanced Cleaner (`core/enhanced_cleaner.py`)
```python
class EnhancedCleaner(CleanerInterface):
    """Enhanced cleaner implementation using plugin architecture"""
    
    def __init__(self, config: Optional[ConfigInterface] = None):
        self.config = config or get_config()
        self.plugin_manager = PluginManager(self.config)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Register built-in plugins
        register_builtin_plugins(self.plugin_manager)
        
        # Discover additional plugins if enabled
        if self.config.get('plugins.auto_discover', True):
            self.plugin_manager.discover_plugins()
    
    # Enhanced analysis with recommendations
    def analyze(self, paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyze what can be cleaned using all plugins"""
        results = self.plugin_manager.analyze_all(paths=paths)
        
        # Add summary information
        results['summary'] = {
            'total_categories': len(results['categories']),
            'total_plugins': results['plugins_analyzed'],
            'safety_breakdown': self._get_safety_breakdown(results),
            'recommendations': self._get_recommendations(results)
        }
        
        return results
    
    # Enhanced cleaning with validation
    def clean(self, dry_run: bool = True, paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """Perform cleaning operation using all plugins"""
        
    # Safety and validation
    def get_safety_info(self, path: str) -> SafetyLevel:
    def validate_operation(self, operation: OperationMode, paths: List[str]) -> bool:
    
    # Plugin management
    def get_plugin_info(self) -> Dict[str, Any]:
    def get_categories(self) -> List[str]:
    def analyze_category(self, category: str) -> Dict[str, Any]:
    def clean_category(self, category: str, dry_run: bool = True) -> Dict[str, Any]:
```

### 5. Enhanced Built-in Plugins

#### Updated Plugins with Safety Levels and Priorities
```python
class BrowserCacheCleaner(CleanerPlugin):
    @property
    def priority(self) -> int:
        return 80  # High priority - safe and effective
    
    def get_safety_level(self, path: str) -> SafetyLevel:
        return SafetyLevel.VERY_SAFE

class SystemCacheCleaner(CleanerPlugin):
    @property
    def priority(self) -> int:
        return 30  # Lower priority - more cautious
    
    def get_safety_level(self, path: str) -> SafetyLevel:
        if path.startswith("/System/Library/Caches"):
            return SafetyLevel.CRITICAL
        elif path.startswith("/Library/Caches"):
            return SafetyLevel.IMPORTANT
        else:
            return SafetyLevel.SAFE

class DownloadsCleaner(CleanerPlugin):
    @property
    def priority(self) -> int:
        return 20  # Low priority - requires manual review
    
    def get_safety_level(self, path: str) -> SafetyLevel:
        return SafetyLevel.IMPORTANT  # Requires manual review
```

## Key Improvements in Phase 3

### 1. **Better Type Safety**
- Enums for operation modes and safety levels
- Dataclasses for structured data
- Protocol-based interfaces
- Comprehensive type hints

### 2. **Enhanced Plugin System**
- Plugin registry with metadata
- Plugin validation and discovery
- Priority-based execution
- Lifecycle management (enable/disable)
- Configuration integration

### 3. **Improved Configuration Management**
- Structured configuration with dataclasses
- Dot notation access
- Multiple format support (YAML/JSON)
- Configuration validation
- Runtime updates

### 4. **Enhanced Safety Features**
- Granular safety levels
- Path-specific safety determination
- Operation validation
- Privilege checking
- Comprehensive error handling

### 5. **Better Architecture**
- Clear separation of concerns
- Interface-based design
- Dependency injection
- Plugin-based extensibility
- Comprehensive logging

## Migration from Legacy to Enhanced Architecture

### Backward Compatibility
- Legacy components remain functional
- Gradual migration path
- Feature flags for new functionality
- Deprecation warnings for old APIs

### Migration Steps
1. **Update Configuration**: Use new ConfigurationManager
2. **Update Plugins**: Implement enhanced plugin base class
3. **Update CLI**: Use EnhancedCleaner instead of MacCleaner
4. **Update Tests**: Add tests for new architecture
5. **Update Documentation**: Reflect new architecture

## Testing the Enhanced Architecture

### Architecture Test Script
```bash
python test_architecture.py
```

### Expected Output
```
✅ Successfully imported enhanced architecture components
🔧 Testing Configuration Manager...
  ✅ Config manager initialized
  ✅ Default dry_run: True
  ✅ Security max_file_size: 1000MB
🔌 Testing Plugin Manager...
  ✅ Plugin manager initialized
  ✅ Built-in plugins registered
  ✅ Found 7 plugins:
    - Browser Cache Cleaner (category: cache, priority: 80)
    - System Cache Cleaner (category: cache, priority: 30)
    - Log File Cleaner (category: logs, priority: 40)
    - Temporary File Cleaner (category: temp, priority: 70)
    - Xcode Cleaner (category: development, priority: 60)
    - Docker Cleaner (category: development, priority: 50)
    - Downloads Cleaner (category: user, priority: 20)
🧹 Testing Enhanced Cleaner...
  ✅ Enhanced cleaner initialized
  ✅ Plugin info retrieved: 7 plugins
  ✅ Categories found: cache, logs, temp, development, user
🔍 Testing Analysis (dry run)...
  ✅ Analysis completed
  ✅ Total space analyzed: 22.4 GB
  ✅ Total files found: 283,545
  ✅ Plugins used: 7
  ✅ Categories analyzed: 5
  ✅ Recommendations: 2
🎉 All architecture tests passed!
```

## Future Enhancements

### Phase 4: Advanced Features
- Async plugin execution
- Plugin marketplace
- Advanced analytics
- Machine learning integration

### Phase 5: Distribution
- PyPI package with enhanced architecture
- Plugin distribution system
- Enhanced documentation
- Performance optimization

This enhanced architecture provides a solid foundation for future development while maintaining backward compatibility and improving safety, extensibility, and maintainability.

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
