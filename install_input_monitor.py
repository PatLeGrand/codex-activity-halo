#!/usr/bin/python3
"""Install the root-owned, read-only activity detector for the sudo caller."""
import argparse
import os
from pathlib import Path
import pwd
import shutil
import subprocess


def unit(uid, gid):
    return f'''[Unit]
Description=Physical input activity signal for Codex (UID {uid})
After=user@{uid}.service
BindsTo=user@{uid}.service
StartLimitIntervalSec=60
StartLimitBurst=10

[Service]
Type=simple
ExecStart=/usr/bin/python3 -I /usr/local/libexec/codex-input-activity/monitor_helper.py --uid {uid} --gid {gid}
Restart=on-failure
RestartSec=1
NoNewPrivileges=yes
CapabilityBoundingSet=CAP_DAC_READ_SEARCH CAP_SETUID CAP_SETGID
ProtectSystem=strict
ProtectHome=tmpfs
BindReadOnlyPaths=/run/user/{uid}
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectKernelLogs=yes
ProtectControlGroups=yes
RestrictSUIDSGID=yes
RestrictNamespaces=yes
LockPersonality=yes
RestrictAddressFamilies=AF_UNIX
SystemCallArchitectures=native
DevicePolicy=closed
DeviceAllow=char-input r
UMask=0077

[Install]
WantedBy=user@{uid}.service
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    uid = int(os.environ.get('SUDO_UID', os.getuid()))
    if uid < 1000:
        raise SystemExit('Launch with sudo from your normal user account.')
    gid = pwd.getpwuid(uid).pw_gid
    if args.dry_run:
        print(unit(uid, gid))
        return
    if os.geteuid() != 0:
        raise SystemExit('This installer needs sudo once to install the physical activity detector.')
    destination = Path('/usr/local/libexec/codex-input-activity')
    destination.mkdir(mode=0o755, parents=True, exist_ok=True)
    if destination.is_symlink() or destination.stat().st_uid != 0:
        raise SystemExit('Refusing an unsafe installation directory.')
    destination.chmod(0o755)
    source = Path(__file__).resolve().with_name('monitor_helper.py')
    script = destination / 'monitor_helper.py'
    if script.is_symlink():
        raise SystemExit('Refusing a symlink at the service script path.')
    shutil.copyfile(source, script)
    os.chown(script, 0, 0)
    script.chmod(0o644)
    service = f'codex-input-activity-{uid}.service'
    path = Path('/etc/systemd/system') / service
    if path.is_symlink():
        raise SystemExit('Refusing a symlink at the service unit path.')
    path.write_text(unit(uid, gid))
    os.chown(path, 0, 0)
    path.chmod(0o644)
    restorecon = shutil.which('restorecon')
    if restorecon:
        subprocess.run([restorecon, '-R', str(destination), str(path)], check=True)
    subprocess.run(['systemctl', 'daemon-reload'], check=True)
    subprocess.run(['systemctl', 'enable', '--now', service], check=True)
    print(f'Installed {service}. No input-group membership was added.')


if __name__ == '__main__':
    main()
