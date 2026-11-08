# Development setup

## 1. Inspect Windows / WSL

Run in Windows PowerShell:

```powershell
wsl --status
wsl --version
wsl --list --verbose
```

If WSL is not installed, open PowerShell as Administrator:

```powershell
wsl --install -d Ubuntu
```

Restart if requested, open Ubuntu, and complete the initial username/password setup. Confirm Ubuntu uses version 2 in the distribution list.

Reference: https://learn.microsoft.com/en-us/windows/wsl/install

## 2. Inspect the Linux environment

Run inside Ubuntu:

```bash
uname -r
uname -m
cat /etc/os-release
test -r /sys/kernel/btf/vmlinux && echo "Kernel BTF present" || echo "Kernel BTF unavailable"
```

These are preliminary checks only. BTF presence alone does not prove that all required hooks, helpers, or permissions are supported. The next implementation task is a feature probe and a minimal tracing smoke test. Do not replace the kernel or disable protections based solely on these checks.

## 3. Clone inside Linux

Once Git is installed and GitHub authentication is configured:

```bash
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/Ori-Marom/traceguard.git
cd traceguard
git status
```

The repository is private. Use your own GitHub authentication; never embed tokens in a clone URL or commit them.

## Current installation status

Ubuntu on WSL2 has captured a successful exec with a temporary bpftrace probe. Follow the [exec sensor lab](EXEC-LAB.md) to verify the repository prototype and its parent PID field.
