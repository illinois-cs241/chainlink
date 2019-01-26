import unittest

from chainlink import Chainlink

stages = [
  {
    "image": "alpine:3.5",
    "entrypoint": ["env"],
    "env": {
      "ASSIGNMENT": "",
      "NETID": "$NETID"
    }
  },
  {
    "image": "alpine:3.5",
    "entrypoint": ["sleep", "2"]
  }
]
env = {
  "TEST": "testing",
  "SEMESTER": "sp18",
  "ASSIGNMENT": "mp1"
}

class TestBasicChaining(unittest.TestCase):

  def test_basic_chain(self):
    chain = Chainlink(stages)
    results = chain.run(env)
    
    self.assertTrue("TEST=testing" in results[0]["logs"].decode("utf-8"))
    self.assertEqual(results[1]["data"]["ExitCode"], 0)