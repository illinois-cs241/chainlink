import unittest

from chainlink import Chainlink

short_delta_stages = [
    {"image": "alpine:3.5", "entrypoint": ["sleep", "3"], "timeout": 2}
]
long_delta_stages = [
    {"image": "alpine:3.5", "entrypoint": ["sleep", "20"], "timeout": 2}
]


class TestTimeout(unittest.TestCase):
    def test_timeout_short_delta(self):
        chain = Chainlink(short_delta_stages)
        results = chain.run({})

        self.assertTrue(results[0]["killed"])

    def test_timeout_long_delta(self):
        chain = Chainlink(long_delta_stages)
        results = chain.run({})

        self.assertTrue(results[0]["killed"])
