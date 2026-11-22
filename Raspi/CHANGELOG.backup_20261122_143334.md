# Software Changelog

All notable changes to the ONYX-Pro Raspberry Pi software are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows Semantic Versioning.

## [Unreleased]

### Added
- Implemented en passant capture-square detection in `game.py`.
- Added physical coordinate mirroring for captured and attacking squares.
- Extended robot capture commands to transmit the captured square, attacker starting square and destination square.
- Integrated the three-coordinate `REMOVE` command into the Raspberry Pi robot-control workflow.
- Added an optional maintenance mode accessible through the `--maintenance` startup argument.
- Added an interactive maintenance console available during human turns.
- Added `XYOFF` and `XYON` commands to disable and enable the XY motor drivers.
- Added `HELP` command to display available maintenance commands.
- Added `EXIT` command to deactivate the maintenance console.

### Changed
- User button pin configuration: `BUTTON_PIN = 26`.
- Updated `run_with_log.sh` to forward command-line arguments to `main.py`.
- Preserved standard gameplay behavior when maintenance mode is not enabled.

### Fixed
- Starting a new game after ending the previous game with a 1-second button press.
- Shutting down the Raspberry Pi after ending a game with a button press longer than 5 seconds.

### Removed
- 

### Security
- 

---

## [1.0.0] - 2026-11-15

### Added
- Initial public software release.
- Stockfish chess engine integration.
- Chess game management using python-chess.
- Raspberry Pi communication with RP2040.
- MCP23017 I2C sensor management.
- Magnetic chess piece detection.
- Robot movement coordination.