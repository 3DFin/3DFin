# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

## [0.4.1]  2024-06-28

### Added

- This changelog file!
- Support of macOS (see `Changed` section)
- Handling of out of memory errors.

### Changed

- Now depends on `dendromatics` 0.5.0 which notably now use `pgeof` instead of `jakteristics` for feature computation.
3Fin should be faster and is compatible with macOS out of the box.

### Fixed

- Add a fix for multiprocessing in a frozen context (standalone).
