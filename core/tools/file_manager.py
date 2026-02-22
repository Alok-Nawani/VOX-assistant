import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import logging

class FileManager:
    """Class for managing file system operations"""
    
    def __init__(self, base_dir: Optional[str] = None):
        """Initialize file manager with base directory"""
        self.base_dir = Path(base_dir) if base_dir else Path.home()
        
    def list_directory(self, path: str = "") -> List[Dict]:
        """List contents of a directory
        
        Args:
            path: Relative path from base directory
            
        Returns:
            List of dictionaries containing file/directory information
        """
        try:
            target_path = self.base_dir / path
            if not target_path.exists():
                return []
                
            contents = []
            for item in target_path.iterdir():
                contents.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                    "modified": item.stat().st_mtime
                })
                
            return sorted(contents, key=lambda x: (x["type"] == "file", x["name"]))
            
        except Exception as e:
            logging.error(f"Error listing directory: {e}")
            return []
            
    def create_directory(self, path: str) -> bool:
        """Create a new directory
        
        Args:
            path: Relative path from base directory
            
        Returns:
            bool: True if directory was created successfully
        """
        try:
            target_path = self.base_dir / path
            target_path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logging.error(f"Error creating directory: {e}")
            return False
            
    def move_item(self, source: str, destination: str) -> bool:
        """Move a file or directory
        
        Args:
            source: Relative path of source from base directory
            destination: Relative path of destination from base directory
            
        Returns:
            bool: True if item was moved successfully
        """
        try:
            source_path = self.base_dir / source
            dest_path = self.base_dir / destination
            
            if not source_path.exists():
                return False
                
            # Create destination directory if it doesn't exist
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(source_path), str(dest_path))
            return True
        except Exception as e:
            logging.error(f"Error moving item: {e}")
            return False
            
    def delete_item(self, path: str) -> bool:
        """Delete a file or directory
        
        Args:
            path: Relative path from base directory
            
        Returns:
            bool: True if item was deleted successfully
        """
        try:
            target_path = self.base_dir / path
            
            if not target_path.exists():
                return False
                
            if target_path.is_dir():
                shutil.rmtree(str(target_path))
            else:
                target_path.unlink()
                
            return True
        except Exception as e:
            logging.error(f"Error deleting item: {e}")
            return False
            
    def search_files(self, pattern: str, path: str = "") -> List[Dict]:
        """Search for files matching a pattern
        
        Args:
            pattern: Search pattern (glob pattern)
            path: Relative path from base directory to search in
            
        Returns:
            List of matching file information dictionaries
        """
        try:
            target_path = self.base_dir / path
            if not target_path.exists():
                return []
                
            matches = []
            for item in target_path.rglob(pattern):
                matches.append({
                    "name": item.name,
                    "path": str(item.relative_to(self.base_dir)),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
                
            return matches
            
        except Exception as e:
            logging.error(f"Error searching files: {e}")
            return []
