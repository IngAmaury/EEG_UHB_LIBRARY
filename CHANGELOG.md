# EEG_UHB Library - Changelog

All notable changes to this project will be documented in this file.  
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]
### Added
- Support for multiple EEG devices (experimental)

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