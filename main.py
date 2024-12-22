import os
import time
import subprocess
from datetime import datetime


def check_adb_connection():
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        devices = result.stdout.strip().split('\n')
        print(f"Connected devices: {devices}")  # Debug print
        if len(devices) > 1:
            print("ADB connection successful")
            return True
        print("No devices connected")
        return False
    except FileNotFoundError:
        print("Error: ADB not found. Please ensure ADB is installed and in system PATH")
        return False


def create_folder_on_android(folder_path):
    try:
        command = f'adb shell mkdir -p "{folder_path.replace(' ', "\\ ")}"'
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"Successfully created folder: {folder_path}")
        else:
            print(f"Failed to create folder: {folder_path}")
            print(f"Error: {result.stderr}")
    except Exception as e:
        print(f"Error executing command: {e}")


class ADBFileTransfer:
    def __init__(self, android_path, windows_path):
        self.android_path = android_path
        self.windows_path = windows_path
        self.known_files = set()

    def verify_android_path(self):

        try:
            result = subprocess.run(['adb', 'shell', f'ls {self.android_path.replace(' ', "\\ ")}'],
                                    capture_output=True, text=True)
            if not result.returncode ==0:
                create_folder_on_android(self.android_path)
            result = subprocess.run(['adb', 'shell', f'ls {self.android_path.replace(' ', "\\ ")}'],
                                    capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Android path verified: {self.android_path}")
                return True
            print(f"Android path not accessible: {self.android_path}")
            print(f"Error output: {result.stderr}")
            return False
        except Exception as e:
            print(f"Error verifying Android path: {e}")
            return False

    def get_android_files(self):
        try:
            # First, check if the directory exists
            check_dir = subprocess.run(['adb', 'shell', f'test -d {self.android_path.replace(' ', "\\ ")} && echo "exists"'],
                                       capture_output=True, text=True)
            if 'exists' not in check_dir.stdout:
                print(f"Directory does not exist: {self.android_path}")
                return set()

            # List files in the directory
            result = subprocess.run(['adb', 'shell', f'ls {self.android_path.replace(' ', "\\ ")}'],
                                    capture_output=True, text=True)

            print(f"ADB ls command output: {result.stdout}")  # Debug print
            print(f"ADB ls error output: {result.stderr}")  # Debug print

            if result.returncode == 0 and result.stdout.strip():
                files = set(filter(None, result.stdout.strip().split('\n')))
                print(f"Files found in directory: {files}")
                return files

            print(f"No files found or error occurred. Return code: {result.returncode}")
            return set()

        except Exception as e:
            print(f"Error listing files: {e}")
            return set()

    def pull_file(self, filename):
        try:
            source = f"{self.android_path}/{filename}"
            destination = os.path.join(self.windows_path, filename)

            print(f"Attempting to pull file: {filename}")
            print(f"Source: {source}")
            print(f"Destination: {destination}")

            result = subprocess.run(['adb', 'pull', source, destination],
                                    capture_output=True, text=True)

            print(f"Pull command output: {result.stdout}")  # Debug print
            print(f"Pull command error: {result.stderr}")  # Debug print

            if result.returncode == 0:
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Successfully copied: {filename}")

                # Launch application with full path
                # subprocess.Popen([r"C:\Program Files\NAPS2\NAPS2.exe", str(destination)])

                # Delete file from Android after successful transfer
                delete_command = f"adb shell rm '{self.android_path}/{filename}'"
                delete_result = subprocess.run(delete_command, shell=True, capture_output=True, text=True)

                if delete_result.returncode == 0:
                    print(f"Successfully deleted {filename} from Android device")
                else:
                    print(f"Failed to delete {filename} from Android device")
                    print(f"Delete error: {delete_result.stderr}")

                return True

            print(f"Failed to copy file. Return code: {result.returncode}")
            return False
        except Exception as e:
            print(f"Error pulling file {filename}: {e}")
            return False

    def monitor_and_transfer(self):
        if not check_adb_connection():
            print("No ADB connection available. Exiting...")
            return

        if not self.verify_android_path():
            print("Android path verification failed. Exiting...")
            return

        print("\n=== Starting File Monitor ===")
        print(f"Monitoring: {self.android_path}")
        print(f"Copying to: {self.windows_path}")
        print("Press Ctrl+C to stop")

        self.known_files = self.get_android_files()
        print(f"Initial files in directory: {self.known_files}")

        while True:
            try:
                print("\nChecking for new files...")
                current_files = self.get_android_files()
                print(f"Current files: {current_files}")

                new_files = current_files - self.known_files
                print(f"New files detected: {new_files}")

                if new_files:
                    print(f"Found {len(new_files)} new files")
                    for file_name in new_files:
                        if file_name and not file_name.startswith('.'):
                            if self.pull_file(file_name):
                                print(f"Successfully transferred: {file_name}")
                            else:
                                print(f"Failed to transfer: {file_name}")
                else:
                    print("No new files found")

                self.known_files = current_files
                print("Waiting 5 seconds before next check...")
                time.sleep(5)

            except KeyboardInterrupt:
                print("\nStopping file monitor...")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                print("Waiting 5 seconds before retry...")
                time.sleep(5)


def main():
    # Replace these paths with your actual paths
    android_folder = "/storage/emulated/0/Documents/Office Lens"
    windows_folder = r".\output_dir"

    # Ensure output directory exists
    if not os.path.exists(windows_folder):
        try:
            os.makedirs(windows_folder)
            print(f"Created output directory: {windows_folder}")
        except Exception as e:
            print(f"Error creating output directory: {e}")
            return

    print("\n=== ADB File Transfer Tool ===")
    print(f"Android folder: {android_folder}")
    print(f"Windows folder: {windows_folder}")

    transfer = ADBFileTransfer(android_folder, windows_folder)
    transfer.monitor_and_transfer()


if __name__ == "__main__":
    main()
