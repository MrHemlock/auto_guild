import argparse

# from yaml import load, Loader


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
