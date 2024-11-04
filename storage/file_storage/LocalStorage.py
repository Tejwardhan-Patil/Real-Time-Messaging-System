import os
import shutil
from typing import List, Optional

class LocalStorage:
    def __init__(self, base_directory: str):
        """
        Initializes the LocalStorage class with a base directory for file storage.
        """
        if not os.path.exists(base_directory):
            os.makedirs(base_directory)
        self.base_directory = base_directory

    def _get_file_path(self, file_name: str) -> str:
        """
        Private method to get the full path of a file in the local storage.
        """
        return os.path.join(self.base_directory, file_name)

    def save_file(self, file_name: str, file_data: bytes) -> str:
        """
        Saves a file to the local storage.
        
        :param file_name: Name of the file to save
        :param file_data: Binary data of the file to be saved
        :return: Path to the saved file
        """
        file_path = self._get_file_path(file_name)
        with open(file_path, 'wb') as file:
            file.write(file_data)
        return file_path

    def read_file(self, file_name: str) -> Optional[bytes]:
        """
        Reads a file from local storage.
        
        :param file_name: Name of the file to read
        :return: Binary data of the file, or None if file doesn't exist
        """
        file_path = self._get_file_path(file_name)
        if os.path.exists(file_path):
            with open(file_path, 'rb') as file:
                return file.read()
        return None

    def delete_file(self, file_name: str) -> bool:
        """
        Deletes a file from local storage.
        
        :param file_name: Name of the file to delete
        :return: True if the file was successfully deleted, False otherwise
        """
        file_path = self._get_file_path(file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def list_files(self) -> List[str]:
        """
        Lists all files stored in the local storage directory.
        
        :return: List of file names
        """
        return os.listdir(self.base_directory)

    def file_exists(self, file_name: str) -> bool:
        """
        Checks if a file exists in local storage.
        
        :param file_name: Name of the file to check
        :return: True if file exists, False otherwise
        """
        file_path = self._get_file_path(file_name)
        return os.path.exists(file_path)

    def copy_file(self, file_name: str, destination: str) -> Optional[str]:
        """
        Copies a file from local storage to another location.
        
        :param file_name: Name of the file to copy
        :param destination: Path to the destination folder
        :return: Destination file path if copy is successful, None if file doesn't exist
        """
        source_file_path = self._get_file_path(file_name)
        if os.path.exists(source_file_path):
            if not os.path.exists(destination):
                os.makedirs(destination)
            destination_path = os.path.join(destination, file_name)
            shutil.copy(source_file_path, destination_path)
            return destination_path
        return None

    def move_file(self, file_name: str, destination: str) -> Optional[str]:
        """
        Moves a file from local storage to another location.
        
        :param file_name: Name of the file to move
        :param destination: Path to the destination folder
        :return: Destination file path if move is successful, None if file doesn't exist
        """
        source_file_path = self._get_file_path(file_name)
        if os.path.exists(source_file_path):
            if not os.path.exists(destination):
                os.makedirs(destination)
            destination_path = os.path.join(destination, file_name)
            shutil.move(source_file_path, destination_path)
            return destination_path
        return None

    def create_directory(self, directory_name: str) -> str:
        """
        Creates a new directory within the base directory.
        
        :param directory_name: Name of the directory to create
        :return: Path to the created directory
        """
        dir_path = os.path.join(self.base_directory, directory_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        return dir_path

    def delete_directory(self, directory_name: str) -> bool:
        """
        Deletes a directory from the base directory.
        
        :param directory_name: Name of the directory to delete
        :return: True if directory was successfully deleted, False otherwise
        """
        dir_path = os.path.join(self.base_directory, directory_name)
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            return True
        return False

    def get_file_size(self, file_name: str) -> Optional[int]:
        """
        Gets the size of a file in bytes.
        
        :param file_name: Name of the file
        :return: Size of the file in bytes, or None if file doesn't exist
        """
        file_path = self._get_file_path(file_name)
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        return None

    def get_file_modified_time(self, file_name: str) -> Optional[float]:
        """
        Gets the last modified time of a file in local storage.
        
        :param file_name: Name of the file
        :return: Last modified time in seconds since the epoch, or None if file doesn't exist
        """
        file_path = self._get_file_path(file_name)
        if os.path.exists(file_path):
            return os.path.getmtime(file_path)
        return None

    def rename_file(self, old_name: str, new_name: str) -> bool:
        """
        Renames a file in local storage.
        
        :param old_name: Current name of the file
        :param new_name: New name of the file
        :return: True if renaming is successful, False otherwise
        """
        old_path = self._get_file_path(old_name)
        new_path = self._get_file_path(new_name)
        if os.path.exists(old_path) and not os.path.exists(new_path):
            os.rename(old_path, new_path)
            return True
        return False

    def get_directory_size(self) -> int:
        """
        Calculates the total size of all files in the base directory.
        
        :return: Total size in bytes
        """
        total_size = 0
        for dirpath, _, filenames in os.walk(self.base_directory):
            for file in filenames:
                file_path = os.path.join(dirpath, file)
                total_size += os.path.getsize(file_path)
        return total_size

    def clear_storage(self) -> None:
        """
        Clears all files and directories in the local storage.
        """
        for file_name in self.list_files():
            self.delete_file(file_name)
        for dir_name in os.listdir(self.base_directory):
            dir_path = os.path.join(self.base_directory, dir_name)
            if os.path.isdir(dir_path):
                shutil.rmtree(dir_path)

    def copy_directory(self, destination: str) -> str:
        """
        Copies the entire base directory to a specified destination.
        
        :param destination: Path to the destination folder
        :return: Path to the copied directory
        """
        if not os.path.exists(destination):
            os.makedirs(destination)
        destination_path = os.path.join(destination, os.path.basename(self.base_directory))
        shutil.copytree(self.base_directory, destination_path)
        return destination_path

# Usage
# storage = LocalStorage("/local/storage")
# storage.save_file("file.txt", b"Hello, World!")