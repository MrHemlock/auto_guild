from __future__ import annotations
import argparse
from pprint import pprint

from dotenv import dotenv_values
from yaml import load, Loader


config = dotenv_values(".env")
parser = argparse.ArgumentParser()
parser.add_argument("structure", help="file path to the guild structure")
args = parser.parse_args()



def channel_parser(channel_mapping: dict[str, list[dict[str, str]]]) -> list[dict[str, str | int]]:
    """Builds an list of channel objects to pass to the API

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

        payload.append({
            "name": category,
            "id": parent_id,
            "type": 4
            })
        current_id += 1
        for channel in channels:
            (name, type_), = channel.items()
            if type_ == "voice":
                type_id = 2
            else:
                type_id = 0

            payload.append({
                "name": name,
                "id": current_id,
                "type": type_id,
                "parent_id": parent_id
                })
            current_id += 1

    return payload


def role_parser(roles: list[str]) -> list[dict[str, str | int]]:
    """Returns a list of role objects to pass to the API
    """
    payload = []
    current_id = 0

    payload.append({
        "name": "everyone",
        "id": current_id
        })
    current_id += 1

    for role in roles:
        payload.append({
            "name": role,
            "id": current_id
            })

    return payload


def payload_builder(config):
    pass

if __name__ == "__main__":
    with open(args.structure) as file:
        dumped = load(file, Loader=Loader)

    payload = payload_builder(dumped)

    # channels = channel_parser(dumped["categories"])
    # roles = role_parser(dumped["roles"])
    # payload = {"channels": channels, "roles": roles}
    pprint(payload)
