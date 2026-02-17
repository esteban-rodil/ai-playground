#!/usr/bin/env python3
"""
keepass_diff - Compare two KeePass (.kdbx) database files entry by entry.

Decrypts both databases, matches entries by UUID (with fallback to title+username),
and produces a detailed field-level diff report.

Usage:
    python keepass_diff.py db1.kdbx db2.kdbx [options]

Requirements:
    pip install pykeepass colorama
"""

import argparse
import getpass
import json
import sys
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional
from pathlib import Path

try:
    from pykeepass import PyKeePass
except ImportError:
    print("Error: pykeepass is required. Install with: pip install pykeepass")
    sys.exit(1)

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init()
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class DiffStatus(str, Enum):
    ONLY_IN_A = "only_in_a"
    ONLY_IN_B = "only_in_b"
    MODIFIED = "modified"
    IDENTICAL = "identical"


@dataclass
class FieldDiff:
    field_name: str
    value_a: Optional[str]
    value_b: Optional[str]

    @property
    def changed(self) -> bool:
        return self.value_a != self.value_b


@dataclass
class EntryDiff:
    status: DiffStatus
    path: str  # group path + title for display
    uuid: Optional[str] = None
    title: str = ""
    username: str = ""
    matched_by: str = "uuid"  # "uuid" or "title+username"
    field_diffs: list[FieldDiff] = field(default_factory=list)

    @property
    def changed_fields(self) -> list[FieldDiff]:
        return [f for f in self.field_diffs if f.changed]


@dataclass
class GroupDiff:
    only_in_a: list[str] = field(default_factory=list)
    only_in_b: list[str] = field(default_factory=list)


@dataclass
class ComparisonResult:
    db_a_path: str
    db_b_path: str
    db_a_entry_count: int = 0
    db_b_entry_count: int = 0
    entry_diffs: list[EntryDiff] = field(default_factory=list)
    group_diff: GroupDiff = field(default_factory=GroupDiff)

    @property
    def only_in_a(self) -> list[EntryDiff]:
        return [d for d in self.entry_diffs if d.status == DiffStatus.ONLY_IN_A]

    @property
    def only_in_b(self) -> list[EntryDiff]:
        return [d for d in self.entry_diffs if d.status == DiffStatus.ONLY_IN_B]

    @property
    def modified(self) -> list[EntryDiff]:
        return [d for d in self.entry_diffs if d.status == DiffStatus.MODIFIED]

    @property
    def identical(self) -> list[EntryDiff]:
        return [d for d in self.entry_diffs if d.status == DiffStatus.IDENTICAL]


# ---------------------------------------------------------------------------
# Database loading
# ---------------------------------------------------------------------------

def open_database(path: str, password: str | None, keyfile: str | None, label: str) -> PyKeePass:
    """Open a KDBX database, prompting for password if not provided."""
    if password is None:
        password = getpass.getpass(f"Password for {label} ({Path(path).name}): ")

    try:
        kp = PyKeePass(path, password=password, keyfile=keyfile)
    except Exception as e:
        print(f"Error opening {label}: {e}")
        sys.exit(1)

    return kp


# ---------------------------------------------------------------------------
# Entry extraction helpers
# ---------------------------------------------------------------------------

def get_entry_path(entry) -> str:
    """Build a human-readable path like 'Root/Social/facebook'."""
    try:
        group_path = "/".join(g.name for g in entry.group.path if g.name) if hasattr(entry, 'group') and entry.group else ""
    except Exception:
        group_path = ""

    # pykeepass entry.path is sometimes a list, sometimes not
    try:
        if hasattr(entry, 'path') and entry.path:
            return "/".join(str(p) for p in entry.path) if isinstance(entry.path, (list, tuple)) else str(entry.path)
    except Exception:
        pass

    title = entry.title or "(untitled)"
    return f"{group_path}/{title}" if group_path else title


def get_entry_uuid(entry) -> str:
    """Get a string representation of the entry UUID."""
    if entry.uuid:
        return str(entry.uuid)
    return ""


COMPARE_FIELDS = [
    "title",
    "username",
    "password",
    "url",
    "notes",
    "tags",
    "icon",
    "expiry_time",
    "otp",
]


def extract_entry_fields(entry) -> dict[str, str]:
    """Extract comparable fields from a pykeepass Entry."""
    data = {}
    for f in COMPARE_FIELDS:
        try:
            val = getattr(entry, f, None)
            if val is None:
                data[f] = ""
            elif isinstance(val, (list, tuple)):
                data[f] = ", ".join(str(v) for v in val)
            else:
                data[f] = str(val)
        except Exception:
            data[f] = ""

    # Custom string fields
    try:
        if entry.custom_properties:
            for key, val in entry.custom_properties.items():
                data[f"custom:{key}"] = str(val) if val else ""
    except Exception:
        pass

    return data


# ---------------------------------------------------------------------------
# Comparison logic
# ---------------------------------------------------------------------------

def compare_entries(entry_a_fields: dict, entry_b_fields: dict) -> list[FieldDiff]:
    """Produce field-level diffs between two entries."""
    all_keys = sorted(set(entry_a_fields.keys()) | set(entry_b_fields.keys()))
    diffs = []
    for key in all_keys:
        val_a = entry_a_fields.get(key, "")
        val_b = entry_b_fields.get(key, "")
        diffs.append(FieldDiff(field_name=key, value_a=val_a, value_b=val_b))
    return diffs


def compare_databases(kp_a: PyKeePass, kp_b: PyKeePass, path_a: str, path_b: str) -> ComparisonResult:
    """Main comparison: match entries by UUID then by title+username fallback."""
    result = ComparisonResult(db_a_path=path_a, db_b_path=path_b)

    entries_a = [e for e in kp_a.entries if not _is_recycle_bin_entry(kp_a, e)]
    entries_b = [e for e in kp_b.entries if not _is_recycle_bin_entry(kp_b, e)]

    result.db_a_entry_count = len(entries_a)
    result.db_b_entry_count = len(entries_b)

    # Index by UUID
    uuid_map_a: dict[str, object] = {}
    uuid_map_b: dict[str, object] = {}
    for e in entries_a:
        uid = get_entry_uuid(e)
        if uid:
            uuid_map_a[uid] = e
    for e in entries_b:
        uid = get_entry_uuid(e)
        if uid:
            uuid_map_b[uid] = e

    # Fallback index: title+username (for entries not matched by UUID)
    def _fallback_key(entry) -> str:
        t = (entry.title or "").strip().lower()
        u = (entry.username or "").strip().lower()
        return f"{t}||{u}"

    matched_a = set()
    matched_b = set()

    # Pass 1: match by UUID
    for uid, ea in uuid_map_a.items():
        if uid in uuid_map_b:
            eb = uuid_map_b[uid]
            matched_a.add(id(ea))
            matched_b.add(id(eb))

            fields_a = extract_entry_fields(ea)
            fields_b = extract_entry_fields(eb)
            field_diffs = compare_entries(fields_a, fields_b)

            has_changes = any(fd.changed for fd in field_diffs)
            result.entry_diffs.append(EntryDiff(
                status=DiffStatus.MODIFIED if has_changes else DiffStatus.IDENTICAL,
                path=get_entry_path(ea),
                uuid=uid,
                title=ea.title or "",
                username=ea.username or "",
                matched_by="uuid",
                field_diffs=field_diffs,
            ))

    # Pass 2: fallback matching for unmatched entries
    unmatched_a = [e for e in entries_a if id(e) not in matched_a]
    unmatched_b = [e for e in entries_b if id(e) not in matched_b]

    fb_map_b: dict[str, list] = {}
    for e in unmatched_b:
        key = _fallback_key(e)
        fb_map_b.setdefault(key, []).append(e)

    for ea in unmatched_a:
        key = _fallback_key(ea)
        candidates = fb_map_b.get(key, [])
        if candidates:
            eb = candidates.pop(0)
            if not candidates:
                del fb_map_b[key]

            matched_a.add(id(ea))
            matched_b.add(id(eb))

            fields_a = extract_entry_fields(ea)
            fields_b = extract_entry_fields(eb)
            field_diffs = compare_entries(fields_a, fields_b)

            has_changes = any(fd.changed for fd in field_diffs)
            result.entry_diffs.append(EntryDiff(
                status=DiffStatus.MODIFIED if has_changes else DiffStatus.IDENTICAL,
                path=get_entry_path(ea),
                uuid=get_entry_uuid(ea),
                title=ea.title or "",
                username=ea.username or "",
                matched_by="title+username",
                field_diffs=field_diffs,
            ))

    # Remaining unmatched
    for ea in entries_a:
        if id(ea) not in matched_a:
            result.entry_diffs.append(EntryDiff(
                status=DiffStatus.ONLY_IN_A,
                path=get_entry_path(ea),
                uuid=get_entry_uuid(ea),
                title=ea.title or "",
                username=ea.username or "",
            ))

    for eb in entries_b:
        if id(eb) not in matched_b:
            result.entry_diffs.append(EntryDiff(
                status=DiffStatus.ONLY_IN_B,
                path=get_entry_path(eb),
                uuid=get_entry_uuid(eb),
                title=eb.title or "",
                username=eb.username or "",
            ))

    # Group comparison
    groups_a = {"/".join(str(p) for p in g.path) if isinstance(g.path, (list, tuple)) else str(g.path)
                for g in kp_a.groups}
    groups_b = {"/".join(str(p) for p in g.path) if isinstance(g.path, (list, tuple)) else str(g.path)
                for g in kp_b.groups}
    result.group_diff.only_in_a = sorted(groups_a - groups_b)
    result.group_diff.only_in_b = sorted(groups_b - groups_a)

    return result


def _is_recycle_bin_entry(kp: PyKeePass, entry) -> bool:
    """Check if an entry is inside the recycle bin."""
    try:
        rb = kp.recyclebin_group
        if rb is None:
            return False
        # Walk up the group tree
        g = entry.group
        while g:
            if g == rb:
                return True
            g = g.parentgroup if hasattr(g, 'parentgroup') else None
    except Exception:
        pass
    return False


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def _c(text: str, color: str) -> str:
    """Apply color if available."""
    if not HAS_COLOR:
        return text
    return f"{color}{text}{Style.RESET_ALL}"


def _mask(value: str, show_passwords: bool) -> str:
    """Mask password values unless --show-passwords is set."""
    if not value:
        return "(empty)"
    if not show_passwords:
        return "****"
    return value


def format_console(result: ComparisonResult, show_passwords: bool = False, show_identical: bool = False) -> str:
    """Pretty-print the comparison result to the console."""
    lines: list[str] = []
    a_name = Path(result.db_a_path).name
    b_name = Path(result.db_b_path).name

    lines.append("")
    lines.append(_c("═" * 70, Fore.CYAN if HAS_COLOR else ""))
    lines.append(_c(f"  KeePass Database Comparison", Fore.CYAN if HAS_COLOR else ""))
    lines.append(_c("═" * 70, Fore.CYAN if HAS_COLOR else ""))
    lines.append(f"  A: {a_name} ({result.db_a_entry_count} entries)")
    lines.append(f"  B: {b_name} ({result.db_b_entry_count} entries)")
    lines.append("")

    # Summary
    lines.append(_c("── Summary ─────────────────────────────────────────", Fore.WHITE if HAS_COLOR else ""))
    lines.append(f"  Identical:    {len(result.identical)}")
    lines.append(f"  Modified:     {_c(str(len(result.modified)), Fore.YELLOW if HAS_COLOR else '')}")
    lines.append(f"  Only in A:    {_c(str(len(result.only_in_a)), Fore.RED if HAS_COLOR else '')}")
    lines.append(f"  Only in B:    {_c(str(len(result.only_in_b)), Fore.GREEN if HAS_COLOR else '')}")
    lines.append("")

    # Group differences
    if result.group_diff.only_in_a or result.group_diff.only_in_b:
        lines.append(_c("── Group Differences ───────────────────────────────", Fore.WHITE if HAS_COLOR else ""))
        for g in result.group_diff.only_in_a:
            lines.append(f"  {_c('- ', Fore.RED if HAS_COLOR else '')}{g}  (only in A)")
        for g in result.group_diff.only_in_b:
            lines.append(f"  {_c('+ ', Fore.GREEN if HAS_COLOR else '')}{g}  (only in B)")
        lines.append("")

    # Only in A
    if result.only_in_a:
        lines.append(_c("── Only in A ───────────────────────────────────────", Fore.RED if HAS_COLOR else ""))
        for d in result.only_in_a:
            lines.append(f"  {_c('- ', Fore.RED if HAS_COLOR else '')}{d.path}  [{d.username}]")
        lines.append("")

    # Only in B
    if result.only_in_b:
        lines.append(_c("── Only in B ───────────────────────────────────────", Fore.GREEN if HAS_COLOR else ""))
        for d in result.only_in_b:
            lines.append(f"  {_c('+ ', Fore.GREEN if HAS_COLOR else '')}{d.path}  [{d.username}]")
        lines.append("")

    # Modified entries
    if result.modified:
        lines.append(_c("── Modified Entries ────────────────────────────────", Fore.YELLOW if HAS_COLOR else ""))
        for d in result.modified:
            match_info = f" (matched by {d.matched_by})" if d.matched_by != "uuid" else ""
            lines.append(f"  {_c('~ ', Fore.YELLOW if HAS_COLOR else '')}{d.path}  [{d.username}]{match_info}")
            for fd in d.changed_fields:
                is_pw = fd.field_name == "password"
                val_a = _mask(fd.value_a, show_passwords) if is_pw else (fd.value_a or "(empty)")
                val_b = _mask(fd.value_b, show_passwords) if is_pw else (fd.value_b or "(empty)")
                lines.append(f"      {fd.field_name}:")
                lines.append(f"        A: {val_a}")
                lines.append(f"        B: {val_b}")
            lines.append("")

    # Identical (optional)
    if show_identical and result.identical:
        lines.append(_c("── Identical Entries ───────────────────────────────", Fore.WHITE if HAS_COLOR else ""))
        for d in result.identical:
            lines.append(f"  = {d.path}  [{d.username}]")
        lines.append("")

    return "\n".join(lines)


def format_json(result: ComparisonResult, show_passwords: bool = False) -> str:
    """Export comparison result as JSON."""
    data = {
        "db_a": result.db_a_path,
        "db_b": result.db_b_path,
        "db_a_entries": result.db_a_entry_count,
        "db_b_entries": result.db_b_entry_count,
        "summary": {
            "identical": len(result.identical),
            "modified": len(result.modified),
            "only_in_a": len(result.only_in_a),
            "only_in_b": len(result.only_in_b),
        },
        "group_diff": {
            "only_in_a": result.group_diff.only_in_a,
            "only_in_b": result.group_diff.only_in_b,
        },
        "entries": [],
    }

    for d in result.entry_diffs:
        if d.status == DiffStatus.IDENTICAL:
            continue
        entry_data = {
            "status": d.status.value,
            "path": d.path,
            "uuid": d.uuid,
            "title": d.title,
            "username": d.username,
            "matched_by": d.matched_by,
        }
        if d.status == DiffStatus.MODIFIED:
            entry_data["changes"] = {}
            for fd in d.changed_fields:
                is_pw = fd.field_name == "password"
                entry_data["changes"][fd.field_name] = {
                    "a": _mask(fd.value_a, show_passwords) if is_pw else fd.value_a,
                    "b": _mask(fd.value_b, show_passwords) if is_pw else fd.value_b,
                }
        data["entries"].append(entry_data)

    return json.dumps(data, indent=2, default=str)


def format_html(result: ComparisonResult, show_passwords: bool = False) -> str:
    """Export comparison result as a self-contained HTML report."""
    a_name = Path(result.db_a_path).name
    b_name = Path(result.db_b_path).name

    rows = []
    for d in result.entry_diffs:
        if d.status == DiffStatus.IDENTICAL:
            continue
        if d.status == DiffStatus.ONLY_IN_A:
            rows.append(f'<tr class="only-a"><td>{d.path}</td><td>{d.username}</td>'
                        f'<td>Only in A</td><td>—</td></tr>')
        elif d.status == DiffStatus.ONLY_IN_B:
            rows.append(f'<tr class="only-b"><td>{d.path}</td><td>{d.username}</td>'
                        f'<td>Only in B</td><td>—</td></tr>')
        elif d.status == DiffStatus.MODIFIED:
            changes_html = "<br>".join(
                f"<b>{fd.field_name}</b>: "
                f"<span class='val-a'>{_mask(fd.value_a, show_passwords) if fd.field_name == 'password' else (fd.value_a or '(empty)')}</span> → "
                f"<span class='val-b'>{_mask(fd.value_b, show_passwords) if fd.field_name == 'password' else (fd.value_b or '(empty)')}</span>"
                for fd in d.changed_fields
            )
            rows.append(f'<tr class="modified"><td>{d.path}</td><td>{d.username}</td>'
                        f'<td>Modified</td><td>{changes_html}</td></tr>')

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>KeePass Diff Report</title>
<style>
  body {{ font-family: -apple-system, sans-serif; margin: 2em; background: #1a1a2e; color: #e0e0e0; }}
  h1 {{ color: #64ffda; }} h2 {{ color: #80cbc4; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 1em; }}
  th, td {{ border: 1px solid #333; padding: 8px 12px; text-align: left; }}
  th {{ background: #16213e; color: #64ffda; }}
  .only-a {{ background: #2d1b1b; }} .only-b {{ background: #1b2d1b; }} .modified {{ background: #2d2d1b; }}
  .val-a {{ color: #ef5350; }} .val-b {{ color: #66bb6a; }}
  .summary {{ display: flex; gap: 2em; margin: 1em 0; }}
  .summary div {{ padding: 1em; border-radius: 8px; background: #16213e; }}
</style></head><body>
<h1>KeePass Database Comparison</h1>
<p><b>A:</b> {a_name} ({result.db_a_entry_count} entries) &nbsp; <b>B:</b> {b_name} ({result.db_b_entry_count} entries)</p>
<div class="summary">
  <div>Identical: {len(result.identical)}</div>
  <div style="color:#ffd54f">Modified: {len(result.modified)}</div>
  <div style="color:#ef5350">Only in A: {len(result.only_in_a)}</div>
  <div style="color:#66bb6a">Only in B: {len(result.only_in_b)}</div>
</div>
<table><thead><tr><th>Entry Path</th><th>Username</th><th>Status</th><th>Changes</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table>
</body></html>"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="keepass_diff",
        description="Compare two KeePass (.kdbx) databases entry by entry.",
    )
    p.add_argument("db_a", help="Path to first .kdbx database (A)")
    p.add_argument("db_b", help="Path to second .kdbx database (B)")
    p.add_argument("-p", "--password", help="Password for both databases (if same)")
    p.add_argument("--password-a", help="Password for database A")
    p.add_argument("--password-b", help="Password for database B")
    p.add_argument("--keyfile-a", help="Key file for database A")
    p.add_argument("--keyfile-b", help="Key file for database B")
    p.add_argument("--show-passwords", action="store_true", help="Show password values in output (default: masked)")
    p.add_argument("--show-identical", action="store_true", help="Include identical entries in output")
    p.add_argument("-f", "--format", choices=["console", "json", "html"], default="console", help="Output format")
    p.add_argument("-o", "--output", help="Write output to file instead of stdout")
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    # Resolve passwords
    pw_a = args.password_a or args.password
    pw_b = args.password_b or args.password

    # Open databases
    kp_a = open_database(args.db_a, pw_a, args.keyfile_a, "Database A")
    kp_b = open_database(args.db_b, pw_b, args.keyfile_b, "Database B")

    # Compare
    result = compare_databases(kp_a, kp_b, args.db_a, args.db_b)

    # Format output
    if args.format == "json":
        output = format_json(result, args.show_passwords)
    elif args.format == "html":
        output = format_html(result, args.show_passwords)
    else:
        output = format_console(result, args.show_passwords, args.show_identical)

    # Write
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
