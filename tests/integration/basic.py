import unittest

from chainlink import Chainlink

stages_1 = [
    {
        "image": "alpine:3.5",
        "entrypoint": ["env"],
        "env": {"ASSIGNMENT": "", "NETID": "$NETID"},
    },
    {"image": "alpine:3.5", "entrypoint": ["sleep", "2"]},
]

stages_2 = [{"image": "no-such-image:3.1415926535", "entrypoint": ["env"]}]

env = {"TEST": "testing", "SEMESTER": "sp18", "ASSIGNMENT": "mp1"}


class TestBasicChaining(unittest.TestCase):
    def test_basic_chain(self):
        chain = Chainlink(stages_1)
        results = chain.run(env)

        self.assertFalse(results[0]["killed"])
        self.assertTrue("TEST=testing" in results[0]["logs"]["stdout"].decode("utf-8"))
        self.assertFalse(results[0]["killed"])
        self.assertEqual(results[1]["data"]["ExitCode"], 0)

    def test_no_such_image(self):
        with self.assertRaises(Exception):
            Chainlink(stages_2)
