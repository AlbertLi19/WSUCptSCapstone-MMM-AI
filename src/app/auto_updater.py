"""
Auto-updater module that checks for updates from a release branch
and applies them automatically.
"""
import os
import sys
import subprocess
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
import json


class AutoUpdater:
    def __init__(self, app_dir=None, release_branch="release"):
        """
        Initialize the auto-updater.
        
        Args:
            app_dir: Directory of the application (defaults to current directory)
            release_branch: Name of the release branch to check for updates
        """
        if app_dir:
            self.app_dir = Path(app_dir)
        else:
            # When running as executable, use current working directory (where user runs the app from)
            # When running as script, use the script's parent directory
            if getattr(sys, 'frozen', False):
                # Running as executable - use the directory where the app was run from
                self.app_dir = Path.cwd()
            else:
                # Running as script - use project root
                self.app_dir = Path(__file__).parent.parent.parent
        
        self.release_branch = release_branch
        self.update_info_file = self.app_dir / ".update_info.json"
        self.git_dir = self.app_dir / ".git"
        
    def is_git_repository(self):
        """Check if the current directory is a git repository"""
        return self.git_dir.exists() and self.git_dir.is_dir()
    
    def get_current_commit(self):
        """Get the current commit hash"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.app_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error getting current commit: {e}")
            return None
    
    def get_remote_commit(self, branch):
        """Get the latest commit hash from remote branch"""
        try:
            # Fetch latest changes
            subprocess.run(
                ["git", "fetch", "origin", branch],
                cwd=self.app_dir,
                capture_output=True,
                check=True
            )
            
            # Get remote commit hash
            result = subprocess.run(
                ["git", "rev-parse", f"origin/{branch}"],
                cwd=self.app_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error getting remote commit: {e}")
            return None
    
    def has_updates(self):
        """Check if there are updates available on the release branch"""
        if not self.is_git_repository():
            print("Not a git repository. Update checking disabled.")
            return False
        
        current_commit = self.get_current_commit()
        remote_commit = self.get_remote_commit(self.release_branch)
        
        if not current_commit or not remote_commit:
            return False
        
        return current_commit != remote_commit
    
    def get_update_info(self):
        """Get information about available updates"""
        if not self.has_updates():
            return None
        
        try:
            current_commit = self.get_current_commit()
            remote_commit = self.get_remote_commit(self.release_branch)
            
            # Get commit messages between current and remote
            result = subprocess.run(
                ["git", "log", f"{current_commit}..origin/{self.release_branch}", 
                 "--pretty=format:%h - %s (%ar)"],
                cwd=self.app_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            return {
                "current_commit": current_commit[:7],
                "latest_commit": remote_commit[:7],
                "changes": result.stdout.strip().split('\n') if result.stdout.strip() else []
            }
        except subprocess.CalledProcessError as e:
            print(f"Error getting update info: {e}")
            return None
    
    def backup_current_state(self):
        """Create a backup of the current state before updating"""
        try:
            backup_dir = self.app_dir.parent / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copytree(self.app_dir, backup_dir, ignore=shutil.ignore_patterns('.git'))
            return backup_dir
        except Exception as e:
            print(f"Error creating backup: {e}")
            return None
    
    def apply_update(self):
        """Apply the update by pulling from the release branch"""
        if not self.has_updates():
            print("No updates available.")
            return False
        
        try:
            # Check for local changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.app_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.stdout.strip():
                print("Local changes detected. Stashing them...")
                subprocess.run(
                    ["git", "stash"],
                    cwd=self.app_dir,
                    check=True
                )
            
            # Pull updates
            print(f"Pulling updates from {self.release_branch}...")
            subprocess.run(
                ["git", "pull", "origin", self.release_branch],
                cwd=self.app_dir,
                check=True
            )
            
            # Update requirements if needed
            requirements_file = self.app_dir / "requirements.txt"
            if requirements_file.exists():
                print("Updating dependencies...")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
                    check=True
                )
            
            # Save update info
            self._save_update_info()
            
            print("Update applied successfully!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error applying update: {e}")
            return False
    
    def _save_update_info(self):
        """Save information about the last update"""
        info = {
            "last_update": datetime.now().isoformat(),
            "commit": self.get_current_commit()
        }
        with open(self.update_info_file, 'w') as f:
            json.dump(info, f, indent=2)
    
    def check_and_update(self, auto_apply=False):
        """
        Check for updates and optionally apply them automatically.
        
        Args:
            auto_apply: If True, automatically apply updates without prompting
        
        Returns:
            bool: True if update was applied, False otherwise
        """
        if not self.is_git_repository():
            return False
        
        print("Checking for updates...")
        
        if not self.has_updates():
            print("Application is up to date!")
            return False
        
        update_info = self.get_update_info()
        if update_info:
            print(f"\nUpdate available!")
            print(f"Current version: {update_info['current_commit']}")
            print(f"Latest version: {update_info['latest_commit']}")
            print(f"\nChanges:")
            for change in update_info['changes'][:5]:  # Show first 5 changes
                print(f"  - {change}")
            if len(update_info['changes']) > 5:
                print(f"  ... and {len(update_info['changes']) - 5} more")
        
        if auto_apply:
            return self.apply_update()
        else:
            # Prompt user
            response = input("\nDo you want to apply this update? (yes/no): ").lower()
            if response in ['yes', 'y']:
                return self.apply_update()
        
        return False


def main():
    """Main function for standalone update checking"""
    updater = AutoUpdater()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        updater.check_and_update(auto_apply=True)
    else:
        updater.check_and_update(auto_apply=False)


if __name__ == "__main__":
    main()
