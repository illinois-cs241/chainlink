# Chainlink
[![Build Status](https://travis-ci.com/illinois-cs241/chainlink.svg?branch=master)](https://travis-ci.com/illinois-cs241/chainlink)
[![Coverage Status](https://coveralls.io/repos/github/illinois-cs241/chainlink/badge.svg?branch=master)](https://coveralls.io/github/illinois-cs241/chainlink?branch=master)
![License](https://img.shields.io/badge/license-NCSA%2FIllinois-blue.svg)
![Python Versions](https://img.shields.io/badge/python-3.5%20%7C%203.6-blue.svg)

`chainlink` is a Python module for running Docker containers in sequence.

### Installation

This module is not currently on PyPI. However, you can still install it via pip with

```sh
pip install git+https://github.com/illinois-cs241/chainlink
```

### Usage

The class `Chainlink` is the only object exported by this module.

#### Constructor

```
__init__(self, stages, workdir="/tmp")
```

The `Chainlink` constructor takes a list of `stages` to chain and a `workdir` into which a temporary directory will be rooted. An example initialization with all available options is annotated below:

```python
# a single-stage specification
stages = [{
  # container entrypoint (optional, defaults to image entrypoint)
  "entrypoint": ["ip", "link", "set", "lo", "up"],
  # container hostname (optional, defaults to 'container')
  "hostname": "somehost",
  # image to run (required, may be local or available on Docker Hub)
  "image": "alpine:3.5",
  # memory cap (optional, defaults to 2GB)
  "memory": "2g",
  # whether to allow networking capabilities (optional, defaults to True)
  "networking": True,
  # whether to switch on privileged mode (optional, defaults to False)
  "privileged": True,
  # the number of seconds until the container is killed (optional, defaults to 30)
  "timeout": 30,
  # container environment additions/overrides (optional, defaults to none)
  "env": {
    "VAR1": "1"
  }
}]
# use home directory as tempdir root
workdir = "/home/user/"

from chainlink import Chainlink
chain = Chainlink(stages, workdir=workdir)
```

Note that all images needed to run the specified stages are pulled in parallel during construction. 

#### Run

```
run(self, environ={}):
```

The `Chainlink` run function takes a base environment (`environ`) and executes each container specified by `stages` during construction in sequence. If a stage fails, then no subsequent stages will be run.

Unless it makes sense to have a base environment for all containers, `environ` can usually be left empty and specified in the `env` option of each stage instead.

The run function returns a list of object, an example of which is annotated below:

```python
[{
  # the data returned by inspecting the State of the stage (container)
  # immediately before it was removed (see Docker SDK for details)
  "data": { ... },
  # whether or not the stage was killed due to a timeout
  "killed": False,
  # the stdout and stderr (with timestamps) for the stage
  "logs": {
    "stdout": b"bytestring",
    "stderr": b"bytestring"
  }
}]
```

Note that the returned list will have the same number of elements as there are stages, with element corresponding to the stage with the same index.

### Cross-Stage Communication

A single directory is mounted at `/job` in each container before it is run, and contents in this `/job` directory are persisted across stages.

This helps facilitate cross-stage communication, which becomes particularly useful if certain stages need to pass along results.

### Troubleshooting

- Docker usually needs to be run with `sudo` in order to get the right permissions to work. Please check that you have the proper permissions to interact with Docker before reporting an issue
- Files mounted into the temp directory used to store `/job` files across stages usually are written as `sudo` due to Dockers defaults. Failing to use this library with `sudo` may result in failures during cleanup
- This module needs a default event loop to be present in order to operate. In most cases, you will not have to take any action to ensure that one exists. In more complicated systems, you may have to set a default event loop for the thread that you are running a `Chainlink` instance in

### Testing

To run integration tests, run:

```sh
sudo python3 -m unittest tests/integration/*.py
```

Note you should execute this command from the root of the project to ensure imports are correctly specified.
