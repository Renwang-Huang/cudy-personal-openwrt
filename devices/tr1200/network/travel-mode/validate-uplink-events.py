#!/usr/bin/env python3
"""Exercise uplink event decisions with isolated command stubs, without networking."""
from pathlib import Path
import os
import subprocess
import tempfile

SOURCE = Path(__file__).parent / "files/usr/libexec/cudy-uplink-sync"


def check_case(name, *, action="ifupdate", interface="wwan", device="wifi0",
               current="wifi0", cached="192.0.2.1", resolver="192.0.2.1",
               locked=False, enabled=True, expected=False):
    with tempfile.TemporaryDirectory(prefix="tr1200-event-test-") as directory:
        root = Path(directory)
        commands = root / "bin"
        commands.mkdir()
        lock = root / "lock"
        lock.mkdir()
        (lock / "passwall_ready.lock").touch()
        (root / "resolv").write_text(f"nameserver {resolver}\n")
        (root / "utils").write_text(
            f"LOCK_PATH={lock}\n"
            f"get_cache_var() {{ printf '%s' '{cached}'; }}\n"
        )
        stubs = {
            "ip": f"printf '%s\\n' 'default via 192.0.2.254 dev {current}'\n"
                  if current else ":\n",
            "uci": f"case \"$*\" in *direct_dns_mode*) echo auto;; *) echo {int(enabled)};; esac\n",
            "flock": f"exit {int(locked)}\n",
            "sleep": ":\n",
            "logger": ":\n",
            "restart": f"printf '%s\\n' restarted >> {root / 'restarts'}\n",
        }
        for command, body in stubs.items():
            path = commands / command
            path.write_text("#!/bin/sh\n" + body)
            path.chmod(0o755)
        program = SOURCE.read_text().replace(
            "PATH=/usr/sbin:/usr/bin:/sbin:/bin", f"PATH={commands}:/usr/bin:/bin"
        ).replace("/usr/share/passwall/utils.sh", str(root / "utils")).replace(
            "/tmp/resolv.conf.d/resolv.conf.auto", str(root / "resolv")
        ).replace("/etc/init.d/passwall", str(commands / "restart"))
        # Wait for the isolated worker so assertions inspect its completed behavior.
        assert program.endswith("exit 0\n")
        program = program[:-len("exit 0\n")] + "wait\nexit 0\n"
        script = root / "event"
        script.write_text(program)
        environment = dict(os.environ, ACTION=action, INTERFACE=interface, DEVICE=device)
        subprocess.run(["sh", str(script), "--event"], env=environment, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        log = root / "restarts"
        restart_count = len(log.read_text().splitlines()) if log.exists() else 0
        assert restart_count == int(expected), (name, restart_count, expected)
        print(f"PASS: {name}")


check_case("unchanged DHCP DNS causes no restart")
check_case("changed DHCP DNS regenerates proxy configuration", cached="192.0.2.9", expected=True)
check_case("non-default uplink DNS event is ignored", cached="192.0.2.9", device="eth0")
check_case("LAN event is ignored", interface="lan", cached="192.0.2.9")
check_case("concurrent native ifup worker suppresses duplicate restart", cached="192.0.2.9", locked=True)
check_case("wired removal with wireless fallback reloads proxy", action="ifdown", interface="wan",
           device="eth0", expected=True)
check_case("no fallback route causes no restart", action="ifdown", interface="wan", device="eth0", current="")
check_case("disabled proxy stays disabled", cached="192.0.2.9", enabled=False)
check_case("normal ifup remains handled by upstream hook", action="ifup", cached="192.0.2.9")
