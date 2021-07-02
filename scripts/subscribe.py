import argparse
import asyncio
import json
import logging
import pprint

import yaml

from aiotruenas_client.websockets import CachingMachine as Machine


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Subscribe to topics on a remote TrueNAS machine.",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "-i",
        "--insecure",
        action="store_true",
        help="Do not encrypt connection",
    )
    parser.add_argument(
        "name", help="The subscription name to subscribe to on the remote machine."
    )
    parser.add_argument(
        "--host",
        help="The host or IP address of the TrueNAS machine.  Loads from .auth.yaml if not present.",
    )
    parser.add_argument(
        "--password",
        "-p",
        help="The password to authenticiate with.  Loads from .auth.yaml if not present.",
    )
    parser.add_argument(
        "--username",
        "-u",
        help="The username to authenticiate with.  Loads from .auth.yaml if not present.",
    )
    parser.add_argument(
        "--api_key",
        "-a",
        help="The api_key to authenticiate with.  Loads from .auth.yaml if not present.",
    )
    return parser


async def subscribe(
    host: str,
    username: str,
    password: str,
    secure: bool,
    name: str,
    api_key: str,
) -> None:
    print(f"Connecting to {host} to subscribe to {name}...")
    machine = await Machine.create(
        host=host,
        username=username,
        password=password,
        api_key=api_key,
        secure=secure,
    )
    assert machine._client is not None
    queue = await machine._client.subscribe(name)
    while True:
        message = await queue.get()
        pprint.pprint(message)
        queue.task_done()


if __name__ == "__main__":
    parser = init_argparse()
    args = parser.parse_args()
    if args.verbose:
        logger = logging.getLogger("websockets")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.StreamHandler())

    host = args.host
    username = args.username
    password = args.password
    secure = not args.insecure
    api_key = args.api_key

    try:
        with open(".auth.yaml", "r") as stream:
            data = yaml.safe_load(stream)
            host = data.get("host", args.host)
            username = data.get("username", args.username)
            password = data.get("password", args.password)
            api_key = data.get("api_key", args.api_key)
    except IOError:
        pass
    asyncio.get_event_loop().run_until_complete(
        subscribe(
            host=host,
            username=username,
            password=password,
            secure=secure,
            api_key=api_key,
            name=args.name,
        )
    )
    asyncio.get_event_loop().run_forever()
