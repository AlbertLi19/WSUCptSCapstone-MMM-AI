# Auto-Update System Documentation

## Table of Contents
1. [Overview](#overview)
2. [How It Works](#how-it-works)
3. [Initial Setup](#initial-setup)
4. [Building Executables](#building-executables)
5. [Creating Releases](#creating-releases)
6. [Distribution](#distribution)
7. [Updating Your Application](#updating-your-application)
8. [Cross-Platform Support](#cross-platform-support)
9. [Troubleshooting](#troubleshooting)

---

## Overview

This application includes an automatic update system that allows clients to receive updates without downloading a new executable. The system supports two modes:

**Developer Mode (Git-based)**
- Uses git commands for updates
- Fast, incremental updates
- Requires git repository and git installation
- Ideal for developers and testers

**Client Mode (GitHub Releases)**
- Uses GitHub API for updates
- Downloads full releases from GitHub
- No git required
- Ideal for end-users and clients

The application automatically detects which mode to use based on the environment.

---

## How It Works

### Architecture

```
App Startup (launcher.py)
    |
    v
Check for .git directory
    |
    +-- Found? --> Use auto_updater.py (git pull)
    |
    +-- Not Found? --> Use github_updater.py (GitHub API)
    |
    v
Check for updates
    |
    v
Update available?
    |
    +-- Yes --> Prompt user to update
    |
    +-- No --> Continue to app
```

### Version Tracking

The system uses semantic versioning (MAJOR.MINOR.PATCH):
- version.txt contains current version (e.g., "1.0.0")
- Git tags mark releases (e.g., "v1.0.0")
- GitHub releases host downloadable executables

### Update Process

**Git Mode:**
1. Fetches from origin/release branch
2. Compares commit hashes
3. If updates available, runs git pull
4. Restarts application

**GitHub Mode:**
1. Queries GitHub API for latest release
2. Compares version numbers
3. If newer version available, downloads zip
4. Extracts and replaces files
5. Restarts application

---

## Initial Setup

### Prerequisites

- Python 3.9 or higher
- Git installed and configured
- PyInstaller for building executables
- Required Python packages (see requirements.txt)

### Install Dependencies

```bash
cd /path/to/-wsum-fullstackapp-
pip install -r requirements.txt
pip install pyinstaller requests
```

### Verify Setup

Check that these files exist:
- src/app/launcher.py (entry point)
- src/app/auto_updater.py (git-based updates)
- src/app/github_updater.py (GitHub API updates)
- version.txt (current version number)
- build.sh (macOS/Linux build script)
- build.bat (Windows build script)

---

## Building Executables

### macOS/Linux

```bash
# Navigate to project root
cd /path/to/-wsum-fullstackapp-

# Clean previous builds
rm -rf build dist

# Build executable
./build.sh

# Result: dist/SegmentationApp/SegmentationApp
```

### Windows

```batch
REM Navigate to project root
cd C:\path\to\-wsum-fullstackapp-

REM Clean previous builds
rmdir /S /Q build dist

REM Build executable
build.bat

REM Result: dist\SegmentationApp\SegmentationApp.exe
```

### Verify Build

The executable should be in `dist/SegmentationApp/` with:
- Main executable (SegmentationApp or SegmentationApp.exe)
- _internal/ folder containing:
  - version.txt
  - All Python libraries
  - Application resources

Test the executable:
```bash
# From project directory (tests git mode)
./dist/SegmentationApp/SegmentationApp

# From different directory (tests GitHub mode)
cd /tmp
/path/to/dist/SegmentationApp/SegmentationApp
```

---

## Creating Releases

### Step 1: Update Version Number

Edit version.txt with the new version:
```bash
echo "1.0.0" > version.txt
```

Commit the change:
```bash
git add version.txt
git commit -m "Bump version to 1.0.0"
git push origin main
```

### Step 2: Create Git Tag

Tags mark specific points in history as releases:
```bash
# Create annotated tag
git tag -a v1.0.0 -m "Release version 1.0.0 - Initial release"

# Push tag to remote
git push origin v1.0.0
```

Tag naming convention:
- Always prefix with 'v' (v1.0.0, not 1.0.0)
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Match the version in version.txt

### Step 3: Build Executables

Build for each target platform:

**Option A: Manual (requires each OS)**
```bash
# On macOS
./build.sh
cd dist
zip -r SegmentationApp-v1.0.0-mac.zip SegmentationApp/
cd ..

# On Windows
build.bat
cd dist
powershell Compress-Archive -Path SegmentationApp -DestinationPath SegmentationApp-v1.0.0-windows.zip
cd ..

# On Linux
./build.sh
cd dist
tar -czf SegmentationApp-v1.0.0-linux.tar.gz SegmentationApp/
cd ..
```

**Option B: GitHub Actions (automatic)**

If you've set up the workflow (see Cross-Platform Support), GitHub builds all platforms automatically when you push a tag.

### Step 4: Create GitHub Release

1. Navigate to releases page:
   ```
   https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/releases
   ```

2. Click "Create a new release"

3. Configure release:
   - Choose tag: Select v1.0.0 from dropdown
   - Release title: Version 1.0.0 - Initial Release
   - Description: List new features, bug fixes, changes

4. Attach binaries:
   - Drag and drop the zip/tar.gz files
   - For multi-platform: upload all variants

5. Options:
   - [x] Set as the latest release (checked)
   - [ ] Set as a pre-release (unchecked for stable)

6. Click "Publish release"

### Step 5: Verify Release

Check that the release appears at:
```
https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/releases/latest
```

Test the update check:
```bash
# Run executable - should see "Application is up to date"
./dist/SegmentationApp/SegmentationApp
```

---

## Distribution

### To Developers (Git Mode)

Share the repository URL:
```bash
git clone https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-.git
cd -wsum-fullstackapp-
./run_app.sh --auto-update
```

### To Clients (GitHub Releases)

Provide the releases page link:
```
https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/releases
```

Instructions for clients:
1. Download the appropriate file for your platform:
   - macOS: SegmentationApp-vX.Y.Z-mac.zip
   - Windows: SegmentationApp-vX.Y.Z-windows.zip
   - Linux: SegmentationApp-vX.Y.Z-linux.tar.gz

2. Extract the downloaded file

3. Run the application:
   - macOS: Double-click SegmentationApp
   - Windows: Double-click SegmentationApp.exe
   - Linux: ./SegmentationApp

4. Future updates are automatic

### Client Experience

When a client runs the application:
```
============================================================
Impurity Segmentation App - Starting...
============================================================

Checking for updates (GitHub Releases)...
Application is up to date!

Starting application...
```

When an update is available:
```
Checking for updates (GitHub Releases)...

************************************************************
UPDATE AVAILABLE!
************************************************************
Current version: v1.0.0
Latest version: v1.0.1
************************************************************

Would you like to update now? (yes/no):
```

If user types 'yes':
```
Downloading update v1.0.1...
Progress: 100.0%
Download complete
Extracting update...
Update applied successfully!
Application will restart to apply update...
```

---

## Updating Your Application

### Release Workflow

For each new version:

1. Make code changes
2. Test thoroughly
3. Update version number
4. Commit and push changes
5. Create and push tag
6. Build executables
7. Create GitHub release
8. Verify updates work

### Example: Bug Fix Release (1.0.0 to 1.0.1)

```bash
# 1. Fix the bug in your code
vim src/app/main.py

# 2. Test the fix
python src/app/main.py

# 3. Update version
echo "1.0.1" > version.txt

# 4. Commit changes
git add .
git commit -m "Fix critical bug in image processing"
git push origin main

# 5. Create tag
git tag -a v1.0.1 -m "Release 1.0.1 - Bug fixes"
git push origin v1.0.1

# 6. Build (or let GitHub Actions do it)
./build.sh
cd dist && zip -r SegmentationApp-v1.0.1-mac.zip SegmentationApp/ && cd ..

# 7. Create release on GitHub
# Upload the new zip file

# 8. Test update
# Run old version - should prompt to update to 1.0.1
```

### Version Number Guidelines

**MAJOR (X.0.0)** - Breaking changes
- Complete redesign
- Incompatible API changes
- Major feature overhaul

**MINOR (x.Y.0)** - New features
- New functionality added
- Backwards compatible
- Performance improvements

**PATCH (x.y.Z)** - Bug fixes
- Bug fixes
- Security patches
- Minor improvements

---

## Cross-Platform Support

### GitHub Actions (Recommended)

The repository includes a GitHub Actions workflow that automatically builds for all platforms.

Location: `.github/workflows/build-release.yml`

**How it works:**
1. You push a tag: `git push origin v1.0.0`
2. GitHub Actions triggers
3. Builds on macOS, Windows, and Linux simultaneously
4. Creates packages for each platform
5. Uploads all packages to the release

**Advantages:**
- No need for multiple machines
- Consistent build environment
- Automatic process
- Free for public repositories

**To use:**
```bash
# Just commit and push the workflow file
git add .github/workflows/build-release.yml
git commit -m "Add multi-platform build workflow"
git push origin main

# Then push tags as normal
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0

# Check build progress at:
# https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/actions
```

### Platform-Specific Notes

**macOS:**
- Builds create .app bundle
- Code signing recommended for distribution
- Users may need to allow in Security & Privacy settings

**Windows:**
- Builds create .exe file
- Windows Defender may flag first run
- Users may need to click "More info" and "Run anyway"

**Linux:**
- Builds create standard binary
- May need execute permissions: `chmod +x SegmentationApp`
- Distribution varies by distro

### Platform Detection

The `github_updater.py` automatically detects the platform:
```python
platform = sys.platform
# Returns: 'darwin' (Mac), 'win32' (Windows), 'linux' (Linux)
```

When checking for updates, it looks for files matching the platform:
- Mac users get files with 'mac' in the name
- Windows users get files with 'windows' in the name
- Linux users get files with 'linux' in the name

---

## Troubleshooting

### "404 Not Found" Error

**Problem:** App shows "Could not check for updates: 404 Client Error"

**Solution:** This means no releases exist yet. Create your first release on GitHub.

### "Update checking not available"

**Problem:** App says update checking is not available

**Solutions:**
- Git mode: Ensure you're running from the project directory
- GitHub mode: Check internet connection
- Verify github_updater.py is included in the build

### Version Mismatch

**Problem:** App shows wrong version number

**Solutions:**
- Check version.txt exists in dist/SegmentationApp/_internal/
- Verify version.txt is included in build script
- Rebuild: `rm -rf build dist && ./build.sh`

### Update Download Fails

**Problem:** Update downloads but won't apply

**Solutions:**
- Check file permissions
- Ensure sufficient disk space
- Verify the uploaded file isn't corrupted
- Check internet connection stability

### Build Failures

**Problem:** PyInstaller fails to build

**Solutions:**
- Verify all dependencies installed
- Check Python version (3.9+)
- Review build log for specific errors
- Try clean build: delete build/ and dist/ folders

### GitHub Actions Failures

**Problem:** Workflow fails on GitHub

**Solutions:**
- Check Actions tab for error logs
- Verify requirements.txt includes all dependencies
- Ensure workflow file syntax is correct
- Check if repository settings allow Actions

---

## Quick Reference

### Common Commands

```bash
# Build executable (macOS/Linux)
./build.sh

# Build executable (Windows)
build.bat

# Create release tag
git tag -a v1.0.0 -m "Release description"
git push origin v1.0.0

# Package for distribution (macOS/Linux)
cd dist && zip -r SegmentationApp-v1.0.0-mac.zip SegmentationApp/

# Package for distribution (Windows)
cd dist
powershell Compress-Archive -Path SegmentationApp -DestinationPath SegmentationApp-v1.0.0-windows.zip

# Test git mode
cd /path/to/project
./dist/SegmentationApp/SegmentationApp

# Test GitHub mode
cd /tmp
/path/to/dist/SegmentationApp/SegmentationApp

# View releases
open https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/releases

# View GitHub Actions
open https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/actions
```

### File Locations

```
-wsum-fullstackapp-/
├── version.txt                          # Current version number
├── build.sh                             # macOS/Linux build script
├── build.bat                            # Windows build script
├── src/app/
│   ├── launcher.py                      # Entry point, mode detection
│   ├── auto_updater.py                  # Git-based updates
│   ├── github_updater.py                # GitHub API updates
│   └── main.py                          # Application code
├── dist/                                # Build output (not in git)
│   └── SegmentationApp/
│       ├── SegmentationApp              # Executable
│       └── _internal/
│           └── version.txt              # Bundled version
└── .github/workflows/
    └── build-release.yml                # GitHub Actions workflow
```

### Release Checklist

Before publishing a release:

- [ ] Version number updated in version.txt
- [ ] Changes committed and pushed
- [ ] Git tag created and pushed
- [ ] Executables built for target platforms
- [ ] Executables tested locally
- [ ] Files packaged (zip/tar.gz)
- [ ] GitHub release created
- [ ] Files uploaded to release
- [ ] Release marked as latest
- [ ] Update check verified
- [ ] Release notes documented

---

## Summary

The auto-update system provides:
- Automatic update detection
- Two-mode operation (git for developers, GitHub for clients)
- Cross-platform support (macOS, Windows, Linux)
- Semantic versioning
- Professional release management

For developers: Fast git-based updates with full source code access
For clients: Simple GitHub releases with automatic updates

The system requires no configuration - it automatically detects the environment and chooses the appropriate update method.
