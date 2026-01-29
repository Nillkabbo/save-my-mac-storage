#!/usr/bin/env python3
"""
Setup script for macOS Cleaner distribution.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

from setuptools import setup, find_packages
import sys
from pathlib import Path

# Read version from __version__.py
version_file = Path(__file__).parent / "src" / "mac_cleaner" / "__version__.py"
exec(version_file.read_text())

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Requirements
requirements = [
    "psutil>=5.9.0",
    "send2trash>=1.8.2",
    "flask>=2.3.0",
    "flask-wtf>=1.1.1",
    "flask-limiter>=3.5.0",
    "click>=8.1.0",
    "pyyaml>=6.0",
]

# Optional requirements
extras_require = {
    "dev": [
        "pytest>=7.4.0",
        "pytest-cov>=4.1.0",
        "pytest-mock>=3.11.0",
        "black>=23.0.0",
        "mypy>=1.5.0",
        "flake8>=6.0.0",
        "bandit>=1.7.0",
        "safety>=2.3.0",
        "build>=0.10.0",
        "twine>=4.0.0",
    ],
    "web": [
        "gunicorn>=21.0.0",
        "flask-cors>=4.0.0",
    ],
    "app": [
        "py2app>=0.28.6",
    ],
    "scheduler": [
        "apscheduler>=3.10.0",
    ],
    "notifications": [
        "pync>=1.8.0",
        "requests>=2.31.0",
    ],
    "test": [
        "pytest>=7.4.0",
        "pytest-cov>=4.1.0",
        "pytest-mock>=3.11.0",
        "pytest-xdist>=3.3.0",
    ],
    "all": [
        "py2app>=0.28.6",
        "apscheduler>=3.10.0",
        "pync>=1.8.0",
        "requests>=2.31.0",
        "gunicorn>=21.0.0",
        "flask-cors>=4.0.0",
    ]
}

setup(
    name="macos-cleaner",
    version=__version__,
    author="macOS Cleaner contributors",
    author_email="contributors@mac-cleaner.local",
    description="Safe and comprehensive macOS system cleaner",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mac-cleaner/macos-cleaner",
    project_urls={
        "Homepage": "https://github.com/mac-cleaner/macos-cleaner",
        "Documentation": "https://github.com/mac-cleaner/macos-cleaner/blob/main/README.md",
        "Repository": "https://github.com/mac-cleaner/macos-cleaner.git",
        "Bug Tracker": "https://github.com/mac-cleaner/macos-cleaner/issues",
        "Changelog": "https://github.com/mac-cleaner/macos-cleaner/blob/main/CHANGELOG.md",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Filesystems",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
        "Environment :: Console",
        "Security",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "mac-cleaner=mac_cleaner.cli:main",
            "mac-cleaner-gui=mac_cleaner.gui:main",
            "mac-cleaner-web=mac_cleaner.web_gui:main",
        ],
    },
    package_data={
        "mac_cleaner": [
            "*.yaml",
            "*.yml", 
            "templates/*",
            "static/*"
        ]
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "macos",
        "cleaner", 
        "disk-space",
        "system-maintenance",
        "security",
        "async",
        "analytics"
    ],
    license="MIT",
    platforms=["macOS"],
)
