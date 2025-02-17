# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

### Fixed

- Fixed some typos, improve coding style

- Fixed MSVC runtime issue that lead to a crash in the standalone and packaged version on Windows.
  PyQt5 embed its own version of Qt (via `PyQt5-qt5`) which bundle a MSVC runtime incompatible with 
  `pgeof` and `dendroptimized` when they are compiled with an aggressive set of optimizations.
  CC plugin was not affected, because in this specific context PyQT5 load the MSVC RT and Qt5 libs 
  included into CC.

### Added

- Include the 3DFin version number in "automatic" Github issue reporting.

- Now depends on `dendromatics` with `dendroptimized` support for massive runtime improvements.

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
