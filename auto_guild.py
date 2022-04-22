import argparse
from pprint import pprint

from yaml import load, Loader


parser = argparse.ArgumentParser()
parser.add_argument("structure", help="file path to the guild structure")
args = parser.parse_args()


def channel_parser(channel_mapping):
    """
    Builds an array of channels to pass to the API

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
            if type_ == "text":
                type_id = 0
            elif type_ == "voice":
                type_id = 2

            payload.append({
                "name": name,
                "id": current_id,
                "type": type_id,
                "parent_id": parent_id
                })
            current_id += 1

    return payload


if __name__ == "__main__":
    with open(args.structure) as file:
        dumped = load(file, Loader=Loader)

    organized = channel_parser(dumped["categories"])
    pprint(organized)
