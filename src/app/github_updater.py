"""
GitHub-based Auto-Updater for Standalone Distribution
Works without requiring git or a local repository.
"""

import sys
import requests
import zipfile
import shutil
from pathlib import Path
from typing import Optional, Tuple
import json
import os


class GitHubUpdater:
    """Auto-updater using GitHub API - no git required."""
    
    def __init__(self, repo_owner: str, repo_name: str, current_version: str):
        """
        Initialize the GitHub updater.
        
        Args:
            repo_owner: GitHub username/org (e.g., 'WSUCptSCapstone-S25-F25')
            repo_name: Repository name (e.g., '-wsum-fullstackapp-')
            current_version: Current app version (e.g., '1.0.0')
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.current_version = current_version
        self.api_base = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        
        # Determine app directory
        if getattr(sys, 'frozen', False):
            # Running as executable
            self.app_dir = Path(sys.executable).parent
        else:
            # Running as script
            self.app_dir = Path(__file__).parent
    
    def check_for_updates(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check if a new release is available.
        
        Returns:
            Tuple of (update_available, latest_version, download_url)
        """
        try:
            # Get latest release from GitHub
            response = requests.get(
                f"{self.api_base}/releases/latest",
                timeout=10
            )
            response.raise_for_status()
            
            release_data = response.json()
            latest_version = release_data['tag_name'].lstrip('v')
            
            # Compare versions
            if self._compare_versions(latest_version, self.current_version) > 0:
                # Find the appropriate asset for the platform
                download_url = self._get_download_url(release_data)
                return True, latest_version, download_url
            
            return False, self.current_version, None
            
        except requests.exceptions.RequestException as e:
            print(f"WARNING: Could not check for updates: {e}")
            return False, None, None
        except Exception as e:
            print(f"WARNING: Update check error: {e}")
            return False, None, None
    
    def _get_download_url(self, release_data: dict) -> Optional[str]:
        """Get the appropriate download URL for the current platform."""
        assets = release_data.get('assets', [])
        
        # Determine platform
        platform = sys.platform
        
        # Look for platform-specific asset
        for asset in assets:
            name = asset['name'].lower()
            if platform == 'darwin' and 'mac' in name:
                return asset['browser_download_url']
            elif platform == 'win32' and 'windows' in name:
                return asset['browser_download_url']
            elif platform == 'linux' and 'linux' in name:
                return asset['browser_download_url']
        
        # Fallback to first asset or source code
        if assets:
            return assets[0]['browser_download_url']
        
        # Last resort: source code zip
        return release_data.get('zipball_url')
    
    def download_and_apply_update(self, download_url: str, version: str) -> bool:
        """
        Download and apply an update.
        
        Args:
            download_url: URL to download the update from
            version: Version being downloaded
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"\n📥 Downloading update v{version}...")
            
            # Create temp directory
            temp_dir = self.app_dir / "update_temp"
            temp_dir.mkdir(exist_ok=True)
            
            # Download the file
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            update_file = temp_dir / "update.zip"
            
            # Download with progress
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(update_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size:
                            percent = (downloaded / total_size) * 100
                            print(f"\rProgress: {percent:.1f}%", end='', flush=True)
            
            print("\n✓ Download complete")
            
            # Extract and apply update
            print("📦 Extracting update...")
            
            extract_dir = temp_dir / "extracted"
            extract_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(update_file, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Update version file
            version_file = self.app_dir / "version.txt"
            version_file.write_text(version)
            
            print("Update applied successfully!")
            print("\nWARNING: Please restart the application to use the new version.")
            
            return True
            
        except Exception as e:
            print(f"\nERROR: Update failed: {e}")
            return False
        finally:
            # Cleanup
            if 'temp_dir' in locals() and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
    
    def _compare_versions(self, v1: str, v2: str) -> int:
        """
        Compare two semantic versions.
        
        Returns:
            1 if v1 > v2, -1 if v1 < v2, 0 if equal
        """
        def parse_version(v: str) -> list:
            return [int(x) for x in v.split('.')]
        
        try:
            parts1 = parse_version(v1)
            parts2 = parse_version(v2)
            
            # Pad shorter version with zeros
            max_len = max(len(parts1), len(parts2))
            parts1.extend([0] * (max_len - len(parts1)))
            parts2.extend([0] * (max_len - len(parts2)))
            
            for p1, p2 in zip(parts1, parts2):
                if p1 > p2:
                    return 1
                elif p1 < p2:
                    return -1
            
            return 0
        except Exception:
            return 0
    
    def get_current_version(self) -> str:
        """Get the current version from version.txt or default."""
        version_file = self.app_dir / "version.txt"
        if version_file.exists():
            return version_file.read_text().strip()
        return self.current_version
