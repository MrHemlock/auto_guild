from __future__ import annotations
import argparse
import webbrowser

from dotenv import dotenv_values
from requests import Session
from yaml import dump, load, Loader


BOT_TOKEN = dotenv_values(".env")["BOT_TOKEN"]
USER_ID = dotenv_values(".env")["USER_ID"]
BASE_URL = r"https://discord.com/api/v9"


class InvalidChannelType(Exception):
    def __init__(self, channel_type):
        self.channel_type = channel_type
        self.message = "{} is not a valid channel type.  Please consult the readme."
        super().__init__(self.message)

    def __str__(self):
        return self.message.format(self.channel_type)


def channel_parser(
    channel_mapping: dict[str, list[dict[str, str]]]
) -> list[dict[str, str | int]]:
    """Builds a list of channel objects to pass to the API

    Channels must consist of either 3 things if they're a category
    or 4 if they're a channel in a category

    name: str - The name of the channel or category
    id: int - Placeholder id for the channel.  This will be replaced by a unique
        snowflake on Discord's end
    type: int - Dictates what kind of channel it is.  We only care about 3 of them:
        0 - Text channel
        2 - Voice channel
        4 - Category
    parent_id: int - Used for the voice and text channels.  Represents the category
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
    payload = []
    current_id = 0

    payload.append(
        {
            "name": "everyone",
            "id": current_id,
        }
    )
    current_id += 1

    for role in roles:
        payload.append(
            {
                "name": role,
                "id": current_id,
            }
        )
        current_id += 1

    return payload


def payload_builder(config) -> dict[str, str | list[dict[str, str | int]]]:
    payload = {}
    payload["name"] = config["name"]
    payload["channels"] = channel_parser(config["categories"])
    payload["roles"] = role_parser(config["roles"])
    payload["system_channel_id"] = 1
    return payload


def create_guild(session, payload):
    response = session.post(
        f"{BASE_URL}/guilds",
        json=payload,
    )
    return response.json()


def get_channels(session, guild_id):
    response = session.get(f"{BASE_URL}/guilds/{guild_id}/channels")
    return response.json()


def compile_finished_guild(channels, roles):
    channel_list = []
    role_list = []
    finished_guild = {}

    for channel in channels:
        name = channel["name"]
        id_ = channel["id"]
        channel_list.append({name: id_})
    finished_guild["channels"] = channel_list

    for role in roles:
        name = role["name"]
        id_ = role["id"]
        role_list.append({name: id_})
    finished_guild["roles"] = role_list

    return finished_guild


def get_invite(session, channel_id):
    response = session.post(
        f"{BASE_URL}/channels/{channel_id}/invites",
        json={},
    )
    invite_id = response.json()["code"]
    return f"https://discord.gg/{invite_id}"


def transfer_ownership(session, user_id, guild_id):
    session.patch(
        f"{BASE_URL}/guilds/{guild_id}",
        json={"owner_id": str(user_id)},
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("structure", help="file path to the guild structure")
    args = parser.parse_args()

    with open(args.structure) as file:
        dumped = load(file, Loader=Loader)

    payload = payload_builder(dumped)

    initalized = Session()
    initalized.headers.update(
        {
            "Authorization": f"Bot {BOT_TOKEN}",
            "User-Agent": "Auto-Guild (https://github.com/MrHemlock/auto_guild)",
            "Content-Type": "application/json",
        }
    )

    with initalized as session:
        guild_response = create_guild(session, payload)
        guild_id = guild_response["id"]
        guild_roles = guild_response["roles"]
        invite_channel_id = guild_response["system_channel_id"]

        channels = get_channels(session, guild_id)

        finished_guild = compile_finished_guild(channels, guild_roles)

        with open("guild_layout.yaml", "w") as file:
            dump(finished_guild, file)

        invite_url = get_invite(session, invite_channel_id)
        print(invite_url)
        webbrowser.open(invite_url, new=2)

        input("Press enter after you have joined the server")
        transfer_ownership(session, USER_ID, guild_id)
