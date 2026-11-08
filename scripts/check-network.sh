#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

output_dir=${1:-captures}
repetitions=${2:-1}
if [[ $# -gt 2 || ! $repetitions =~ ^([1-9][0-9]{0,3}|10000)$ ]]; then
    printf 'Usage: %s [output-directory [repetitions from 1 to 10000]]\n' "$0" >&2
    exit 2
fi

lab_dir=$(mktemp -d /tmp/traceguard-network.XXXXXX)
trap 'rm -rf -- "$lab_dir"' EXIT

tag=${lab_dir##*.}
client_comm="tgn-$tag"
ln -s -- /usr/bin/python3 "$lab_dir/$client_comm"
cp -- scripts/tcp-workload.py "$lab_dir/workload.py"

sudo bpftrace -q -c "$lab_dir/$client_comm $lab_dir/workload.py $lab_dir/expected.json $repetitions" \
    sensor/connect.bt "$client_comm" > "$lab_dir/raw.log" 2> "$lab_dir/diagnostics.log" || {
    cat "$lab_dir/diagnostics.log" >&2
    exit 1
}

if [[ -s "$lab_dir/diagnostics.log" ]]; then
    cat "$lab_dir/diagnostics.log" >&2
    exit 1
fi

mkdir -p -- "$output_dir"
output=$(mktemp --suffix=.jsonl -- "$output_dir/network-$tag.XXXXXX")
if ! python3 -m traceguard.network_lab "$client_comm" "$lab_dir/expected.json" \
    < "$lab_dir/raw.log" > "$output"; then
    rm -f -- "$output"
    cat "$lab_dir/raw.log" >&2
    exit 1
fi
printf 'Capture saved to %s\n' "$output"
