# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).


## [git] - 2021-11-06
### Added
- tests
  - Actually run the included test blnk files.
- Check for drive letters other than C: and replace them if the next part of the path exists in one of the `BASES`.

### Changed
- Rename "AppDatas" to "AppsData" to make reason for being plural clear (it is for multiple applications to have their config directories).
- Rename `foundCloud` to `statedCloud` for clarity (since it is the one in the blnk file and may not be a directory name that exists under `profile`).
- Add support for non-Windows ('$') environment variables and replacing "~/" at start of strings.
- Separate the logic for Windows and non-Windows systems to make platform-specific code more clear with fewer checks for the platform.

### Fixed
- Move the "%USERPROFILE%" code out of the `v[1:2] == ":":` clause so the code has a chance of running!
- Splat (See `*parts`) doesn't always provide 2 or more params for join.
