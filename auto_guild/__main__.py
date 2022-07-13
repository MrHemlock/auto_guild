"""A Python script to automate the creation of guilds."""

from __future__ import annotations

import argparse
import webbrowser
from os import getenv
from pathlib import Path

from dotenv import load_dotenv
from requests import Session
from yaml import Loader, dump, load


BASE_URL = r"https://discord.com/api/v10"
CHANNEL_TYPES = {
    "text": 0,
    "voice": 2,
    "category": 4,
}


class InvalidChannelType(Exception):
    """Raised when the channel type is invalid."""

    def __init__(self, channel_type):
        self.channel_type: str = channel_type
        self.message: str = (
            "{} is not a valid channel type.  Please consult the readme."
        )
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message.format(self.channel_type)


def channel_parser(channel_mapping: dict) -> tuple[list, int | None]:
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
    system_channel_id = None

    for category in channel_mapping:
        parent_id = current_id
        channels = {}

        if isinstance(category, dict):
            category_name, channels = next(iter(category.items()))
        else:
            category_name = category

        payload.append(
            {
                "name": category_name,
                "id": parent_id,
                "type": 4,
            }
        )

        current_id += 1

        for channel in channels:
            channel_name, type_ = next(iter(channel.items()))
            if (type_id := CHANNEL_TYPES.get(type_)) is None:
                raise InvalidChannelType(type_)
            payload.append(
                {
                    "name": channel_name,
                    "id": current_id,
                    "type": type_id,
                    "parent_id": parent_id,
                }
            )
            if system_channel_id is None:
                system_channel_id = current_id
            current_id += 1
    return payload, system_channel_id


def role_parser(roles: list[str]) -> list[dict[str, list]]:
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


def payload_builder(
    config: dict,
    *,
    system_channel_id: int | None = 1,
) -> dict:
    """Builds the complete payload to pass to the API"""
    payload = {}
    if categories := config.get("categories"):
        channels_, system_channel_id = channel_parser(categories)
        payload.update(channels=channels_)
    payload.update(system_channel_id=system_channel_id)

    if roles := config.get("roles"):
        payload.update(roles=role_parser(roles))
    if name_ := config.get("name"):
        payload.update(name=name_)
    return payload


def create_guild(session: Session, payload: dict) -> dict:
    """Creates a guild using the API"""
    response = session.post(
        f"{BASE_URL}/guilds",
        json=payload,
    )
    response.raise_for_status()

    return response.json()


def get_channels(session: Session, guild_id: str) -> list[dict]:
    """Gets all channels in a guild"""
    response = session.get(f"{BASE_URL}/guilds/{guild_id}/channels")
    return response.json()


def create_webhooks(
    session: Session,
    webhook_channels: list,
    channels_: list[dict],
) -> list[dict]:
    webhooks = []

    for channel in channels_:
        if channel.get("type") == 4:
            continue
        if (channel_name := channel.get("name")) not in webhook_channels:
            continue
        channel_id = channel.get("id")
        response = session.post(
            f"{BASE_URL}/channels/{channel_id}/webhooks",
            json={"name": channel_name},
        )
        webhooks.append(response.json())

    return webhooks


def compile_finished_guild(
    name: str,
    id_: str,
    channels: list[dict],
    roles: list[dict],
    webhooks: list[dict],
) -> dict:
    """Compiles the guild details into the format that the bot expects"""
    finished_guild = {name: id_, "categories": {}, "roles": []}

    categories = finished_guild["categories"]
    current = ""
    for channel in channels:
        if channel["type"] == 4:
            current = channel["name"]
            categories[current] = {"id": channel["id"]}
        else:
            categories[current][channel["name"]] = channel["id"]

    role_list = []
    for role in roles:
        name = role["name"]
        id_ = role["id"]
        role_list.append({name: id_})
    finished_guild["roles"] = role_list

    webhook_list = []
    for webhook in webhooks:
        name = webhook["name"]
        id_ = webhook["id"]
        webhook_list.append({name: id_})
    finished_guild["webhooks"] = webhook_list

    return finished_guild


def get_invite(session: Session, channel_id: str) -> str:
    """Creates an invite for the given channel and returns the invite URL"""
    response = session.post(
        f"{BASE_URL}/channels/{channel_id}/invites",
        json={},
    )
    invite_id = response.json()["code"]
    return f"https://discord.gg/{invite_id}"


def transfer_ownership(session: Session, user_id: str, guild_id: str,) -> None:
    """Transfers ownership of a guild to a user"""
    session.patch(
        f"{BASE_URL}/guilds/{guild_id}",
        json={"owner_id": str(user_id)},
    )


def run():
    """Runs the script"""
    description = (
        "Create a Discord guild with the specified configuration. "
        "Either a server_name or guild template_path must be provided."
    )

    parser = argparse.ArgumentParser(
        description=description,
        epilog="Example: python -m auto_guild -s examples/pydis_bot.yml",
    )

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "-s",
        "--structure",
        help="file path to the guild structure",
        type=str,
    )
    group.add_argument(
        "-n",
        "--server-name",
        help="desired server name if a blank server is desired",
        type=str,
    )
    parser.add_argument(
        "-u",
        "--user-id",
        help="user ID for user who will ownership transferred to them",
        type=str,
    )
    parser.add_argument(
        "-t",
        "--bot-token",
        help="bot token used for creating the guild",
        type=str,
    )

    args = parser.parse_args()
    load_dotenv()

    USER_ID = args.user_id or getenv("USER_ID")
    if not USER_ID:
        raise ValueError("USER_ID not found")
    BOT_TOKEN = args.bot_token or getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not found")
    template_path = args.structure

    SERVER_NAME = args.server_name
    webhook_list = None
    if SERVER_NAME:
        payload_ = payload_builder({"name": SERVER_NAME})
    else:
        with open(template_path) as file:
            dumped = load(file, Loader=Loader)
            webhook_list = dumped.get("webhooks")
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
        guild_name = guild_response["name"]
        guild_id_ = guild_response["id"]
        guild_roles = guild_response["roles"]
        invite_channel_id = guild_response["system_channel_id"]

        channels_ = get_channels(session_, guild_id_)

        webhook_objects = []
        if webhook_list is not None:
            webhook_objects = create_webhooks(session_, webhook_list, channels_)

        finished_guild_ = compile_finished_guild(
            guild_name,
            guild_id_,
            channels_,
            guild_roles,
            webhook_objects,
        )

        output_path = Path("guild_layout.yaml")

        with open(output_path, "w") as file:
            dump(finished_guild_, file)
        print(f"Guild layout saved to {output_path.resolve()}")

        invite_url = get_invite(session_, invite_channel_id)
        print(invite_url)
        answer = input("Would you like to open the invite link in a browser? y/N: ")
        if len(answer) > 0 and "yes".startswith(answer.lower()):
            webbrowser.open(invite_url)

        input("Press enter after you have joined the server ")
        transfer_ownership(session_, USER_ID, guild_id_)
        print("Ownership transferred")


if __name__ == "__main__":
    run()
