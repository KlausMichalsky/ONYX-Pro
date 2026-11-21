#line 1 "C:\\Users\\Klaus\\Documents\\ONYX-Pro\\Zero\\CHANGELOG.md"

# Firmware Changelog

All notable changes to the ONYX-Pro RP2040 firmware are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows Semantic Versioning.

## [Unreleased]

### Added
- Implemented the three-coordinate `REMOVE` command.
- Added a complete capture sequence state machine.
- Added automatic transfer of captured pieces to the Capture Board.
- Added automatic pickup and placement of the attacking piece at its destination.
- Implemented a single HOME return after the complete capture and attacking-piece movement sequence.
- Added serial command reception diagnostics (`RX=[...]`).
- Dedicated Z-axis game speed and acceleration parameters.


### Changed
- Increased motor speeds.
- Adjusted motor acceleration values.
- Updated Z-axis mechanical reduction configuration to 2:1 (reference only).

### Fixed
- 

### Removed
- 

### Security
- 

---

## [1.0.0] - 2026-11-15

### Added
- Initial public firmware release.
- RP2040 motor control.
- Stepper motor control and homing.
- Robot movement and positioning commands.
- Serial communication with Raspberry Pi.

