![Lint](https://github.com/sdwilsh/py-freenas/workflows/Lint/badge.svg)
![Build](https://github.com/sdwilsh/py-freenas/workflows/Build/badge.svg)

# Python Module for FreeNAS Websocket API

This python module utilizes the [FreeNAS Websocket API](https://api.ixsystems.com/freenas/) to get state from a FreeNAS instance.

## Installation

```
pip install pyfreenas
```

## Usage

```python
from pyfreenas import Machine as FreeNASMachine

machine = await Machine.create(
    "hostname.of.machine",
    username="someuser",
    password="password",
)
await machine.refresh()
```

### `Machine`

Object representing a FreeNAS instance.

### `Disks`

Available from `machine.disks`, contains information about the disks attached to the machine.

### `VirturalMachines`

Available from `machine.vms`, contains information about the virtural machines available on the machine.

Each instance has the following methods availabe:
* `vm.start`
* `vm.stop`
* `vm.restart`

## Development

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