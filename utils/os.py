import shutil
import os


def copy_directory(source, destination):
    try:
        shutil.copytree(source, destination)
        print(f"Directory copied from {source} to {destination}")
    except shutil.Error as e:
        print(f"Directory copy failed: {e}")
    except OSError as e:
        print(f"Directory copy failed: {e}")


def delete_file(file_path):
    try:
        os.remove(file_path)
        print(f"The file '{file_path}' has been successfully deleted.")
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
    except Exception as e:
        print(f"An error occurred while deleting the file '{file_path}': {e}")


def delete_folder(folder_path):
    try:
        shutil.rmtree(folder_path)
        print(f"The folder '{folder_path}' has been successfully deleted.")
    except FileNotFoundError:
        print(f"Folder '{folder_path}' not found.")
    except Exception as e:
        print(
            f"An error occurred while deleting the folder '{folder_path}': {e}")


def copy_file(source, destination):
    try:
        shutil.copy(source, destination)
        print(f"File copied from {source} to {destination}")
    except shutil.Error as e:
        print(f"File copy failed: {e}")
    except OSError as e:
        print(f"File copy failed: {e}")
