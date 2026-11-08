"""Check blocking TCP success and refusal over IPv4 and IPv6 loopback."""

import errno
import json
from pathlib import Path
import socket
import sys


def check_family(family, address):
    with (
        socket.socket(family, socket.SOCK_STREAM) as listener,
        socket.socket(family, socket.SOCK_STREAM) as reserved,
    ):
        listener.bind((address, 0))
        listener.listen()
        reserved.bind((address, 0))

        with socket.socket(family, socket.SOCK_STREAM) as client:
            client.connect(listener.getsockname())
            accepted, _ = listener.accept()
            accepted.close()

        with socket.socket(family, socket.SOCK_STREAM) as client:
            try:
                client.connect(reserved.getsockname())
            except OSError as exc:
                if exc.errno != errno.ECONNREFUSED:
                    raise
            else:
                raise RuntimeError("connection to the reserved port unexpectedly succeeded")

        return [
            {"address": address, "port": listener.getsockname()[1], "result": 0},
            {
                "address": address,
                "port": reserved.getsockname()[1],
                "result": -errno.ECONNREFUSED,
            },
        ]


def run(repetitions=1):
    outcomes = []
    for _ in range(repetitions):
        outcomes.extend(check_family(socket.AF_INET, "127.0.0.1"))
        outcomes.extend(check_family(socket.AF_INET6, "::1"))
    return outcomes


if __name__ == "__main__":
    repetitions = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    if not 1 <= repetitions <= 10000:
        sys.exit("repetitions must be between 1 and 10000")
    Path(sys.argv[1]).write_text(json.dumps(run(repetitions)), encoding="utf-8")
