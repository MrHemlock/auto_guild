# auto_guild

Creates a Discord server based on a template you lay out, making it an easy and quick way to flesh out a server to fit
your needs.

## Installation

This project uses PDM, a package manager that implements PEP 582, please visit https://pdm.fming.dev/#installation for
installation instructions.

To install the project, clone the repository and install the dependencies.

```bash
$ git clone https://github.com/MrHemlock/auto_guild.git
$ pdm install
```

## Usage

Example:

```bash
$ python auto_guild.py examples/pydis_bot.yml
```

## Channel types

The valid channel types are listed below

- `0` - Text channel
- `2` - Voice channel
- `4` - Category
