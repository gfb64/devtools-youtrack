#!/usr/bin/env python3
"""Create a YouTrack project from the retained Helix template."""

import getpass
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request


BASE_URL = "https://dev-tools.helix-onprem.net"
TEMPLATE_KEY = "HELIXTPL"
TOKEN_FILE = "/etc/devtools-youtrack/admin-bootstrap.token"


def fail(message):
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_token():
    try:
        with open(TOKEN_FILE, encoding="utf-8") as token_file:
            token = token_file.read().strip()
    except FileNotFoundError:
        token = getpass.getpass("YouTrack permanent token: ").strip()
    except PermissionError:
        fail(f"cannot read {TOKEN_FILE}; run with sudo")
    if not token:
        fail("no YouTrack token was supplied")
    return token


def api(token, method, path, body=None):
    request = urllib.request.Request(
        BASE_URL + path,
        data=None if body is None else json.dumps(body).encode(),
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            content = response.read()
            return json.loads(content) if content else None
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")
        try:
            detail = json.loads(detail).get("error_description", detail)
        except (json.JSONDecodeError, AttributeError):
            pass
        fail(f"YouTrack returned HTTP {error.code}: {detail}")
    except urllib.error.URLError as error:
        fail(f"cannot reach YouTrack: {error.reason}")


def prompt():
    name = input("Project name: ").strip()
    key = input("Project key (for example MCPSER): ").strip().upper()
    description = input("Description (optional): ").strip()

    if not name:
        fail("project name is required")
    if not re.fullmatch(r"[A-Z][A-Z0-9-]*", key):
        fail("project key must start with a letter and contain only A-Z, 0-9, or -")

    print(f"\nCreate {name!r} with key {key!r} from {TEMPLATE_KEY}?")
    if input("Continue [y/N]: ").strip().lower() != "y":
        print("Cancelled.")
        raise SystemExit(0)
    return name, key, description


def verify_fields(token, project_id):
    quoted_id = urllib.parse.quote(project_id, safe="")
    fields = api(
        token,
        "GET",
        f"/api/admin/projects/{quoted_id}/customFields"
        "?fields=field(name),bundle(values(name,isResolved)),defaultValues(name)&%24top=1000",
    )
    by_name = {item["field"]["name"]: item for item in fields}

    state = by_name.get("State", {})
    state_values = [value["name"] for value in state.get("bundle", {}).get("values", [])]
    state_default = [value["name"] for value in state.get("defaultValues", [])]
    if state_values != ["TO DO", "IN PROGRESS", "IN REVIEW", "DONE"] or state_default != ["TO DO"]:
        fail("project was created, but its State configuration does not match the template")

    readiness = by_name.get("Agent Readiness", {})
    readiness_values = [
        value["name"] for value in readiness.get("bundle", {}).get("values", [])
    ]
    readiness_default = [value["name"] for value in readiness.get("defaultValues", [])]
    if readiness_values != ["Pending Review", "Approved"] or readiness_default != ["Pending Review"]:
        fail("project was created, but its Agent Readiness configuration does not match the template")


def main():
    name, key, description = prompt()
    token = read_token()

    projects = api(
        token,
        "GET",
        "/api/admin/projects?fields=name,shortName,template&%24top=1000",
    )
    if any(project["name"] == name or project["shortName"] == key for project in projects):
        fail("a project with that name or key already exists")
    if not any(
        project["shortName"] == TEMPLATE_KEY and project.get("template")
        for project in projects
    ):
        fail(f"template {TEMPLATE_KEY} is missing or is not enabled as a template")

    current_user = api(token, "GET", "/api/users/me?fields=id,login")
    query = urllib.parse.urlencode(
        {
            "template": TEMPLATE_KEY,
            "fields": "id,name,shortName,leader(id,login)",
        }
    )
    project = api(
        token,
        "POST",
        f"/api/admin/projects?{query}",
        {
            "name": name,
            "shortName": key,
            "description": description or None,
            "leader": {"id": current_user["id"]},
        },
    )

    verify_fields(token, project["id"])
    print(f"\nCreated {project['name']} ({project['shortName']}).")
    print(f"Verified State and Agent Readiness fields: {BASE_URL}/projects/{project['shortName']}")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        raise SystemExit(130)
