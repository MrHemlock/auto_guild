# auto_guild

Creates a Discord server based on a template you lay out, making it an easy and quick way to flesh out a server to fit your needs.

## Installation

### pip

You can install the project using `pip`:

#### Linux/Mac
```bash
$ pip3 install auto_guild
```

#### Windows
```powershell
> py -m pip install auto_guild
```

### Source

This project uses PDM, a package manager that implements PEP 582, please visit https://pdm.fming.dev/#installation for
installation instructions.

To install the project, clone the repository and install the dependencies.

```bash
$ git clone https://github.com/MrHemlock/auto_guild.git
$ pdm install
```

## Usage

The script requires 3 things in order to run:
- a server template yaml
- a token for the bot you want to make the server
- a user ID for the user you want to transfer ownership to

`auto_guild` requires that you provide it with either a server name that you want to use (if you want it to create a blank server) or provide it with a file path to a server template yaml.

The `BOT_TOKEN` and `USER_ID` can either be passed as arguments on the command-line, placed in a `.env` file, or come from your system's environmental variables.

Example:

```
usage: auto_guild.py [-h] (-s STRUCTURE | -n SERVER_NAME) [-u USER_ID] [-t BOT_TOKEN]
```

```bash
$ python auto_guild.py -s examples/pydis_bot.yml
```

```bash
$ python auto_guild.py -n "Hemlock's Cool Server" -u USER_ID -t BOT_TOKEN
```

## Server Template Format

The server template yaml format is as follows:

```yaml
name: server_name_here
categories:
    category_name:
        - channel_name: channel_type
roles:
    - role_name
```

`category_name` and `channel_name` should be replaced with the relevant names you desire. For a practical example, see the `pydis_bot.yml` file in the `examples` folder.
