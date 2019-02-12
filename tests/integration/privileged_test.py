import unittest

from chainlink import Chainlink

stages = [
  {
    "image": "ubuntu:14.04",
    "entrypoint": ["unshare", "--mount", "echo", "dumb"],
    "privileged": True
  },
  {
    "image": "ubuntu:14.04",
    "entrypoint": ["ip", "link", "set", "lo", "up"],
    "privileged": True
  }
]

class TestPrivileged(unittest.TestCase):

  def test_basic_chain(self):
    chain = Chainlink(stages)
    results = chain.run({})

    self.assertEqual(results[0]["data"]["ExitCode"], 0)
    self.assertEqual(results[1]["data"]["ExitCode"], 0)
