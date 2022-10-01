## Install:

You must have a python version >= 3.10.5 (I haven't tested for other versions) .

```
git clone https://github.com/Gadzhi07/degeneRATe.git
```

## Configure:

```
cd server
pip install -r requirements.txt
```

**Create a new encryption key and change it in the server/main.py and client/main.py (the FERNET_KEY variable).**

In the client/main.py replace the IP variable with the IP of your server.

#### **For Linux:**

```
echo -e "from cryptography.fernet import Fernet\nprint(Fernet.generate_key())" | python
```

#### **For Windows:**

Create and run a new file with the code:

```
from cryptography.fernet import Fernet
print(Fernet.generate_key())
```

Copy the output ^ and paste it into the FERNET_KEY variable (in server/main.py and client/main.py).

## Run:

### Server:

```
cd server
python main.py
```

### Client:

```
cd client
python main.py
```

## How to use?

#### All commands:

| NAME         | DESCRIPTION                                         |
|--------------|-----------------------------------------------------|
| help         | Print information about all commands.               |
| conns        | Print all connections.                              |
| use          | Select connection from the list of connections.     |
| upload       | Upload local file.                                  |
| download     | Download remote file.                               |
| open_link    | Opening a link on the selected connection.          |
| hot_key      | Pressing hotkeys on the selected connection.        |
| write_text   | Enter text on the selected connection.              |
| window_alert | Creating a window on the selected connection.       |
| screenshot   | Creating a screenshot for the selected connection.  |
| pc_info      | Information about the computer.                     |
| ins_command  | Adding commands to the DB.                          |
| commands     | Output of commands from the DB.                     |
| del_command  | Deleting commands from the DB.                      |
| exit         | Close program.                                      |

First look at all the connections:

`conns`

Next you have to choose a connection:

`use`

For example:
```
use
Enter ID: 0
Enter "Shell" or "Commands" (from DB) : Shell
```

After successfully selecting a connection, you can use all commands.