"""Open two blocking TCP connections to a loopback test endpoint."""

import errno
import json
from pathlib import Path
import socket
import sys


LOOPBACK = "127.0.0.1"


def run():
    with (
        socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener,
        socket.socket(socket.AF_INET, socket.SOCK_STREAM) as reserved,
    ):
        listener.bind((LOOPBACK, 0))
        listener.listen()
        reserved.bind((LOOPBACK, 0))

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect(listener.getsockname())
            accepted, _ = listener.accept()
            accepted.close()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            try:
                client.connect(reserved.getsockname())
            except OSError as exc:
                if exc.errno != errno.ECONNREFUSED:
                    raise
            else:
                raise RuntimeError("connection to the reserved port unexpectedly succeeded")

        return [
            {"address": LOOPBACK, "port": listener.getsockname()[1], "result": 0},
            {
                "address": LOOPBACK,
                "port": reserved.getsockname()[1],
                "result": -errno.ECONNREFUSED,
            },
        ]


if __name__ == "__main__":
    Path(sys.argv[1]).write_text(json.dumps(run()), encoding="utf-8")
