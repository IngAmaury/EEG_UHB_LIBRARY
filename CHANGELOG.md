# EEG_UHB Library - Changelog

All notable changes to this project will be documented in this file.  
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]
### Added
- Support for multiple EEG devices (experimental)

## [0.1.9] - 2025-06-25
### Fixed
- Added `numpy==1.26.4` and `packaging>=20.0` to resolve runtime errors related to binary compatibility and missing dependencies.

## [0.1.8] - 2025-06-25
### Fixed
- Installation error on Python 3.12 due to missing `distutils`
- Ensured cross-platform installation without requiring compilation

## [0.1.7] - 2024-07-18
### Fixed
- Added missing `networkx` dependency required by `scikit-fuzzy`
- Corrected resource loading in Windows environments

## [0.1.6] - 2024-07-18
### Fixed
- Critical resource loading issue for `.pkl` files
- Proper package data inclusion in wheel distribution
### Changed
- Migrated from `pkg_resources` to modern `importlib.resources` API
- Restructured project layout for better resource management

## [0.1.5] - 2024-07-17
### Fixed
- Windows-specific installation path issues
- Missing resource files in final package
### Added
- Proper MANIFEST.in configuration for non-Python files

## [0.1.4] - 2024-07-16
### Fixed
- Dependency conflicts with NumPy/Numba versions
- Twine upload authentication issues
### Changed
- Improved package metadata in pyproject.toml

## [0.1.3] - 2024-07-15
### Added
- Initial resource management system
- Basic stress detection functionality
### Fixed
- LSL stream connection stability issues

## [0.1.2] - 2024-07-15
### Fixed
- Enforced NumPy<1.25 compatibility to resolve Numba conflicts (#12)
- Fixed module import errors in Jupyter environments (#15)

## [0.1.1] - 2024-07-10
### Added
- Initial PyPI release
- Core acquisition methods:
  - `start_acquisition()` with LSL stream support
  - Real-time data saving capability
- Basic documentation
### Changed
- Improved error handling in device connection