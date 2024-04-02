# Changelog for Operation Bot

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
The project uses semantic versioning (see [SemVer](https://semver.org)).

## [Unreleased]

## v0.46.0 - 2024-04-02

## v0.45.2 - 2024-04-02

### Fixed

- Do not try to read non-existent message in `on_error`. The error handler does
  not actually receive a full context, this was a result of a confusingly named
  variable.

## v0.45.1 - 2024-04-02

### Fixed

- Use a placeholder message if a command error doesn't include one. This
  should fix some of the incorrect warnings about messages with >2000
  characters when trying to edit old events.

## v0.45.0 - 2024-03-27

### Added

- Automatic build pipeline using Github Actions

  Reads docker repo from variables. Defaults to
  `GITHUB_ACTOR/GITHUB_REPOSITORY` if variables aren't set

## v0.44.0 - 2024-03-06

### Fixed

- `archive_past_events` task runs only once if the bot reconnects
- Messages longer than 2000 messages are now truncated instead of just being
  printed in the log

## v0.43.0 - 2024-02-25

### Added

- !archivepast command to archive all past events
- Automatically archive past events after a configured time

### Changed

- Update to template v1.4.1a3

## v0.42.2 - 2024-01-10

### Changed

- Alway display the attendance emoji

## v0.42.1 - 2023-09-22

### Fixed

- Fixed a broken type hint in Event

## v0.42.0 - 2023-09-22

### Fixed

- Fixed optional arguments for discord commands

## v0.41.0 - 2023-09-21

### Changed

- Disable setting time with !setquick
- Make argument date parsing more flexible
- Allow finding events by date in commands

### Removed

- Remove Charlie from 1PLT roles

## v0.40.0 - 2023-09-20

### Changed

- Drop support for Python 3.9 and older.
- Updated template from cookiecutter to copier.

## v0.39.2 - 2022-12-15

### Changed

- Added a template by OverkillGuy.

## v0.39.1 - 2022-10-17

### Added

- Show timezone names dynamically.
