import unittest

from dockerchain import DockerChain

stages = [
  {
    "image": "ubuntu:14.04",
    "entrypoint": ["unshare", "--mount", "echo", "dumb"],
    "capabilities": ["SYS_ADMIN"]
  },
  {
    "image": "ubuntu:14.04",
    "entrypoint": ["ip", "link", "set", "lo", "up"],
    "capabilities": ["NET_ADMIN"]
  }
]

class TestCapAdd(unittest.TestCase):

  def test_basic_chain(self):
    chain = DockerChain(stages)
    results = chain.run({}, roster=[])

    self.assertEqual(results[0]["data"]["ExitCode"], 0)
    self.assertEqual(results[1]["data"]["ExitCode"], 0)
