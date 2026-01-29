# Security Policy

## Supported Versions

Only the latest release is supported with security updates.

## Reporting a Vulnerability

If you discover a security issue, please report it privately.

- **Email**: security@mac-cleaner.local
- **GitHub**: Create a private security advisory on the GitHub repository
- **Include**: Steps to reproduce, affected versions, and impact assessment

We will respond within 7 days and provide a fix timeline.

## Security Features

### Path Validation
- All file paths are validated against allowed prefixes
- Path traversal attacks are prevented (`../`, symbolic links)
- System-critical paths are protected by default

### Input Sanitization
- All user inputs are sanitized before shell execution
- Shell injection attacks are prevented using `shlex.quote()`
- File names and paths are validated for safe characters

### Web Interface Security
- CSRF protection enabled on all forms
- Rate limiting to prevent abuse
- Localhost-only access by default
- No remote file operations

### Backup & Recovery
- Automatic backup creation before any file operations
- SHA-256 checksums for file integrity verification
- One-click restore functionality

## Protected Paths

The following paths are **never** allowed for cleaning operations:

### System Paths
- `/System` - macOS system files
- `/usr` - Unix system utilities
- `/bin`, `/sbin` - Essential binaries
- `/etc` - System configuration
- `/var/root` - Root user directory

### User Data
- `~/Documents` - User documents
- `~/Desktop` - Desktop files
- `~/Downloads` - Downloaded files (require explicit confirmation)
- `~/Library/Keychains` - Keychain access
- `~/.ssh` - SSH keys
- `~/.gnupg` - GPG keys

### Application Data
- `/Applications` - Installed applications
- `/Library/Preferences` - System preferences
- `/Library/Keychains` - System keychains

## Security Best Practices

1. **Always use dry-run mode first** to preview what will be cleaned
2. **Review the analysis** before confirming any cleaning operations
3. **Keep backups** enabled for important files
4. **Run as standard user**, never as root/administrator
5. **Verify file paths** before allowing access

## Vulnerability Disclosure Process

1. **Report**: Send detailed vulnerability report to security@mac-cleaner.local
2. **Acknowledgment**: We'll confirm receipt within 48 hours
3. **Assessment**: We'll investigate and assess the impact
4. **Fix Timeline**: We'll provide a timeline for the fix
5. **Disclosure**: We'll coordinate public disclosure after the fix is released

## Security Updates

Security updates are released as:
- Patch releases (x.y.Z) for critical vulnerabilities
- Minor releases (x.Y.0) for security improvements
- Major releases (X.0.0) for security architecture changes

Users are encouraged to:
- Enable automatic updates where possible
- Monitor release notes for security updates
- Update to the latest version promptly

## Security Testing

The project uses automated security scanning:
- **Bandit** for Python security issues
- **Safety** for dependency vulnerability scanning
- **CodeQL** for advanced static analysis

All security tools are integrated into the CI/CD pipeline.
