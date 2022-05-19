"""A Python script to automate the creation of guilds."""

from __future__ import annotations

import argparse
import webbrowser
from os import getenv

from dotenv import load_dotenv
from requests import Session
from yaml import Loader, dump, load

BASE_URL = r"https://discord.com/api/v9"


class InvalidChannelType(Exception):
    """Raised when the channel type is invalid."""

    def __init__(self, channel_type: str) -> None:
        self.channel_type: str = channel_type
        self.message: str = (
            "{} is not a valid channel type.  Please consult the readme."
        )
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message.format(self.channel_type)


def channel_parser(
    channel_mapping: dict[str, list[dict[str, str]]]
) -> list[dict[str, str | int]]:
    """Builds a list of channel objects to pass to the API

    Channels must consist of either 3 things if they're a category
    or 4 if they're a channel in a category

    name: str - The name of the channel or category
    id: int - Placeholder id for the channel. This will be replaced by a unique
        snowflake on Discord's end
    type: int - Dictates what kind of channel it is. We only care about 3 of them:
        0 - Text channel
        2 - Voice channel
        4 - Category
    parent_id: int - Used for the voice and text channels. Represents the category
        id that the channel is listed under
    """
    payload = []
    current_id = 0

    for category, channels in channel_mapping.items():
        parent_id = current_id

        payload.append(
            {
                "name": category,
                "id": parent_id,
                "type": 4,
            }
        )
        current_id += 1
        for channel in channels:
            ((name, type_),) = channel.items()
            if type_ == "voice":
                type_id = 2
            elif type_ == "text":
                type_id = 0
            else:
                raise InvalidChannelType(type_)

            payload.append(
                {
                    "name": name,
                    "id": current_id,
                    "type": type_id,
                    "parent_id": parent_id,
                }
            )
            current_id += 1

    return payload


def role_parser(roles: list[str]) -> list[dict[str, str | int]]:
    """Returns a list of role objects to pass to the API

    Role objects submitted to the Create Guild endpoint only require
    the role's name. The first role in the list will always be for
    the @everyone role
    """
    payload = [
        {
            "name": "everyone",
            "id": 0,
        }
    ]

    current_id = 1

    for role in roles:
        payload.append(
            {
                "name": role,
                "id": current_id,
            }
        )
        current_id += 1

    return payload


def payload_builder(config: dict) -> dict[str, str | list[dict[str, str | int]]]:
    """Builds the complete payload to pass to the API"""
    return {
        "name": config["name"],
        "channels": channel_parser(config["categories"]),
        "roles": role_parser(config["roles"]),
        "system_channel_id": 1,
    }


def create_guild(
    session: Session, payload: dict[str, str | list[dict[str, str | int]]]
) -> dict:
    """Creates a guild using the API"""
    response = session.post(
        f"{BASE_URL}/guilds",
        json=payload,
    )
    return response.json()


def get_channels(session: Session, guild_id: int) -> list[dict]:
    """Gets all channels in a guild"""
    response = session.get(f"{BASE_URL}/guilds/{guild_id}/channels")
    return response.json()


def compile_finished_guild(
    channels: list[dict], roles: list[dict]
) -> dict[str, list[dict[str, str]]]:
    """Compiles the guild details into the format that the bot expects"""
    finished_guild = {}

    channel_list = []
    for channel in channels:
        name = channel["name"]
        id_ = channel["id"]
        channel_list.append({name: id_})
    finished_guild["channels"] = channel_list

    role_list = []
    for role in roles:
        name = role["name"]
        id_ = role["id"]
        role_list.append({name: id_})
    finished_guild["roles"] = role_list

    return finished_guild


def get_invite(session: Session, channel_id: str) -> str:
    """Creates an invite for the given channel and returns the invite URL"""
    response = session.post(
        f"{BASE_URL}/channels/{channel_id}/invites",
        json={},
    )
    invite_id = response.json()["code"]
    return f"https://discord.gg/{invite_id}"


def transfer_ownership(session: Session, user_id: str, guild_id: str) -> None:
    """Transfers ownership of a guild to a user"""
    session.patch(
        f"{BASE_URL}/guilds/{guild_id}",
        json={"owner_id": str(user_id)},
    )


def run() -> None:
    """Runs the script"""
    parser = argparse.ArgumentParser(
        description="Create a Discord guild with the specified configuration",
        epilog="Example: python auto_guild.py examples/pydis_bot.yml",
    )
    parser.add_argument("structure", help="file path to the guild structure", type=str)
    parser.add_argument(
        "-u",
        "--user",
        help="user ID for user who will ownership transferred to them",
        type=str,
    )
    parser.add_argument(
        "-t",
        "--token",
        help="bot token used for creating the guild",
        type=str,
    )
    args = parser.parse_args()
    load_dotenv()

    USER_ID: str | None = args.user or getenv("USER_ID")
    if not USER_ID:
        raise ValueError("USER_ID not found")
    BOT_TOKEN: str | None = args.token or getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not found")
    template_path = args.structure

    with open(template_path) as file:
        dumped = load(file, Loader=Loader)

    payload_ = payload_builder(dumped)

    initialized = Session()
    initialized.headers.update(
        {
            "Authorization": f"Bot {BOT_TOKEN}",
            "User-Agent": "Auto-Guild (https://github.com/MrHemlock/auto_guild)",
            "Content-Type": "application/json",
        }
    )

    with initialized as session_:
        guild_response = create_guild(session_, payload_)
        guild_id_ = guild_response["id"]
        guild_roles = guild_response["roles"]
        invite_channel_id = guild_response["system_channel_id"]

        channels_ = get_channels(session_, guild_id_)

        finished_guild_ = compile_finished_guild(channels_, guild_roles)

        with open("guild_layout.yaml", "w") as file:
            dump(finished_guild_, file)
        print(f"Guild layout saved to guild_layout.yaml")

        invite_url = get_invite(session_, invite_channel_id)
        print(invite_url)
        webbrowser.open(invite_url, new=2)

        input("Press enter after you have joined the server")
        transfer_ownership(session_, USER_ID, guild_id_)
        print("Ownership transferred")


if __name__ == "__main__":
    run()
