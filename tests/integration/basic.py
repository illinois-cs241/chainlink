import unittest

from dockerchain import DockerChain

stages = [
  {
    "image": "alpine:3.5",
    "entrypoint": ["cat", "job/roster.json"]
  },
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
roster = [
  { "NETID": "example1" }
]

class TestBasicChaining(unittest.TestCase):

  def test_basic_chain(self):
    chain = DockerChain(stages)
    results = chain.run(env, roster=roster)
    
    self.assertTrue("example1" in results[0]["logs"].decode("utf-8"))
    self.assertTrue("TEST=testing" in results[1]["logs"].decode("utf-8"))
    self.assertEqual(results[2]["data"]["ExitCode"], 0)
