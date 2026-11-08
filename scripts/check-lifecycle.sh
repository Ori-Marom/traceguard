#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

lab_dir=$(mktemp -d /tmp/traceguard-lifecycle.XXXXXX)
trap 'rm -rf -- "$lab_dir"' EXIT

tag=${lab_dir##*.}
parent_comm="tgp-$tag"
child_comm="tgc-$tag"
parent="$lab_dir/$parent_comm"
child="$lab_dir/$child_comm"
ln -s -- /bin/bash "$parent"
ln -s -- /usr/bin/sleep "$child"

cat > "$lab_dir/workload.sh" <<'WORKLOAD'
"$1" 1 &
wait "$!"
WORKLOAD

sudo bpftrace -q -c "$parent $lab_dir/workload.sh $child" \
    sensor/lifecycle.bt "$parent_comm" > "$lab_dir/raw.log" 2> "$lab_dir/diagnostics.log" || {
    cat "$lab_dir/diagnostics.log" >&2
    exit 1
}

# Refuse partial captures if bpftrace reports dropped events or other diagnostics.
if [[ -s "$lab_dir/diagnostics.log" ]]; then
    cat "$lab_dir/diagnostics.log" >&2
    exit 1
fi

mkdir -p captures
output=$(mktemp --suffix=.jsonl "captures/lifecycle-$tag.XXXXXX")
if ! python3 -m traceguard.normalize "$parent_comm" "$child_comm" \
    < "$lab_dir/raw.log" > "$output"; then
    rm -f -- "$output"
    cat "$lab_dir/raw.log" >&2
    exit 1
fi
printf 'Capture saved to %s\n' "$output"
