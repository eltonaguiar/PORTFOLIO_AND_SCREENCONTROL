#!/usr/bin/env python3
"""A9 probe: scripted read of the remote Linux AT-SPI accessibility tree.

Connects to the session AT-SPI bus on gx10-c9b9 (eltonsGX10)
(unix:path=/run/user/1000/at-spi/bus_0) over SSH and dumps the root
accessible tree: name, role, child count, recursing to bounded depth.

This is topology B from PC_AGENT_CONTROL_RESEARCH.md §4.1: SSH + AT-SPI,
RustDesk only for watching. pyatspi is not installed on the remote box, so
the probe uses dbus-python against the well-known name
org.a11y.atspi.Registry and reads /org/a11y/atspi/accessible/root.

Run on the Linux box:  python3 remote_atspi_tree.py
Run evidence: 01-screen-control-llm/transcripts/remote_atspi_tree_20261123T1328Z.txt
(captured from the unattended cron host over SSH, exit code 0).
"""
import dbus

BUS_ADDR = "unix:path=/run/user/1000/at-spi/bus_0"
ROOT_PATH = "/org/a11y/atspi/accessible/root"
REGISTRY = "org.a11y.atspi.Registry"
IFACE = "org.a11y.atspi.Accessible"
PROPS = "org.freedesktop.DBus.Properties"
MAX_DEPTH = 4
MAX_CHILDREN = 30


def connect():
    try:
        return dbus.bus.BusConnection(BUS_ADDR)
    except TypeError:
        return dbus.bus.BusConnection(address=BUS_ADDR)


def role(acc):
    try:
        return acc.GetRoleName()
    except Exception as exc:
        return f"<role error: {exc}>"


def prop(obj, iface, name):
    p = dbus.Interface(obj, PROPS)
    try:
        return p.Get(iface, name)
    except Exception as exc:
        return f"<{name} error: {exc}>"


def walk(bus, acc, obj_path, label, depth, lines):
    name = prop(acc, IFACE, "Name")
    count = prop(acc, IFACE, "ChildCount")
    lines.append(f"{'  ' * depth}{label} {obj_path} | name={name!r} | role={role(acc)} | children={count}")
    if depth >= MAX_DEPTH:
        return
    try:
        children = acc.GetChildren()
    except Exception as exc:
        lines.append(f"{'  ' * (depth + 1)}  <GetChildren error: {exc}>")
        return
    for index, (bus_name, child_path) in enumerate(children[:MAX_CHILDREN]):
        try:
            child = dbus.Interface(
                bus.get_object(str(bus_name), str(child_path)), IFACE
            )
        except Exception as exc:
            lines.append(f"{'  ' * (depth + 1)}  [{index}] <bind error: {exc}> {child_path}")
            continue
        walk(bus, child, str(child_path), f"[{index}]", depth + 1, lines)
    if len(children) > MAX_CHILDREN:
        lines.append(f"{'  ' * (depth + 1)}  ... {len(children) - MAX_CHILDREN} more children not shown")


def main():
    bus = connect()
    root_obj = bus.get_object(REGISTRY, ROOT_PATH)
    root = dbus.Interface(root_obj, IFACE)
    lines = []
    walk(bus, root, ROOT_PATH, "root", 0, lines)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
