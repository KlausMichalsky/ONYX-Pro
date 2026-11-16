
# Software Changelog

All notable changes to the ONYX-Pro Raspberry Pi software are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows Semantic Versioning.

## [Unreleased]

### Added
- Changelog added

### Changed
- User button pin configuration: BUTTON_PIN = 26.

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

