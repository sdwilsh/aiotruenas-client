![Lint](https://github.com/sdwilsh/aiotruenas-client/workflows/Lint/badge.svg)
![Build](https://github.com/sdwilsh/aiotruenas-client/workflows/Build/badge.svg)

# Python Module for TrueNAS Websocket API

This python module utilizes the [TrueNAS Websocket API](https://www.truenas.com/docs/hub/additional-topics/api/websocket_api.html) to get state from a TrueNAS instance.

## Installation

```
pip install aiotruenas-client
```

## Usage

```python
from aiotruenas_client import CachingMachine as TrueNASMachine

machine = await TrueNASMachine.create(
    "hostname.of.machine",
    api_key="someapikey"
)
disks = await machine.get_disks()
pools = await machine.get_pools()
vms = await machine.get_vms()
```

Alternatively, a username and password may also be supplied.

### `Machine`

Object representing a TrueNAS instance.

### `Disk`

Available from `machine.disks`, contains information about the disks attached to the machine.

### `Pool`

Available from `machine.pools`, contains information about the ZFS pools known to the machine.

### `VirturalMachine`

Available from `machine.vms`, contains information about the virtural machines available on the machine.

Each instance has the following methods availabe:

- `vm.start`
- `vm.stop`
- `vm.restart`

## Development

### Setup

```
python3.8 -m venv .venv
source .venv/bin/activate

# Install Requirements
pip install -r requirements.txt

# Install Dev Requirements
pip install -r requirements-dev.txt

# One-Time Install of Commit Hooks
pre-commit install
```

### Working With Methods & Subscriptions

When adding support for a new object, or updating existing code, it can be useful to see the raw response from the
TrueNAS machine from time to time. In order to help do that easily, you can drop a `.auth.yaml` file in the root of
the repository, with the following content:

```yaml
host: "some.host.name"
api_key: "someapikey"
```

Use `scripts/invoke_method.py` to call a method:

```
python scripts/invoke_method.py disk.query
```

Use `scripts/subscribe.py` to subscribe to a topic:

```
python scripts/subscribe.py reporting.realtime
```

Run either with -h to see additional options.


### Testing

Tests are run with `pytest`.
