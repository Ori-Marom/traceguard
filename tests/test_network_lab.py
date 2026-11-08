import unittest

from traceguard.network_lab import verify_connections
from traceguard.normalize import normalize
from traceguard.replay import replay


WIRE = [
    "TG\texec\t100\t10\t80\t0\t0\ttgn-test\n",
    "TG\tconnect\t120\t10\t80\t127.0.0.1\t30001\t0\n",
    "TG\tconnect\t140\t10\t80\t127.0.0.1\t30002\t-111\n",
]
EXPECTED = [
    {"address": "127.0.0.1", "port": 30001, "result": 0},
    {"address": "127.0.0.1", "port": 30002, "result": -111},
]


class NetworkLabTests(unittest.TestCase):
    def test_replays_both_tcp_outcomes_for_tagged_client(self):
        events = normalize(reversed(WIRE), "lab", "boot-a")
        lines, pid = verify_connections(events, "tgn-test", EXPECTED)
        self.assertEqual(pid, 10)
        self.assertEqual(
            [event["result"] for event in replay(lines)["connections"]], [0, -111]
        )

    def test_dual_stack_capture_matches_both_families_and_normalizes_ipv6(self):
        wire = [
            *WIRE,
            "TG\tconnect\t160\t10\t80\tv6hex:00000000000000000000000000000001\t30003\t0\n",
            "TG\tconnect\t180\t10\t80\t::1\t30004\t-111\n",
        ]
        expected = [
            *EXPECTED,
            {"address": "::1", "port": 30003, "result": 0},
            {"address": "::1", "port": 30004, "result": -111},
        ]
        events = normalize(reversed(wire), "lab", "boot-a")
        lines, pid = verify_connections(events, "tgn-test", expected)
        self.assertEqual(pid, 10)
        self.assertEqual(
            [event["address"] for event in replay(lines)["connections"]],
            ["127.0.0.1", "127.0.0.1", "::1", "::1"],
        )

    def test_rejects_short_ipv6_wire_buffer(self):
        with self.assertRaisesRegex(ValueError, "invalid IPv6 address bytes on line 1"):
            normalize(["TG\tconnect\t160\t10\t80\tv6hex:0001\t30003\t0\n"], "lab", "boot-a")

    def test_reused_pid_does_not_resolve_a_connection_to_the_wrong_process(self):
        wrong_identity = WIRE[2].replace("\t80\t", "\t81\t")
        events = normalize([*WIRE[:2], wrong_identity], "lab", "boot-a")
        with self.assertRaisesRegex(ValueError, "client identity"):
            verify_connections(events, "tgn-test", EXPECTED)

    def test_rejects_invalid_destination_port(self):
        invalid_port = WIRE[2].replace("\t30002\t", "\t65536\t")
        events = normalize([*WIRE[:2], invalid_port], "lab", "boot-a")
        with self.assertRaisesRegex(ValueError, "port must be <= 65535"):
            verify_connections(events, "tgn-test", EXPECTED)
