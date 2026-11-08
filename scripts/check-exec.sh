#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
lab_dir=$(mktemp -d /tmp/traceguard-exec.XXXXXX)
trap 'rm -rf -- "$lab_dir"' EXIT

tag=${lab_dir##*.}
parent="$lab_dir/tgp-$tag"
child="$lab_dir/tgc-$tag"

ln -s -- /bin/bash "$parent"
ln -s -- /usr/bin/sleep "$child"

cat > "$lab_dir/workload.sh" <<'WORKLOAD'
"$1" 1 &
child_pid=$!
printf 'EXPECTED local_pid=%s local_ppid=%s child_comm=%s parent_comm=%s\n' \
    "$child_pid" "$BASHPID" "${1##*/}" "${2##*/}"
wait "$child_pid"
WORKLOAD

sudo bpftrace -c "$parent $lab_dir/workload.sh $child $parent" "$repo_root/sensor/exec.bt"
