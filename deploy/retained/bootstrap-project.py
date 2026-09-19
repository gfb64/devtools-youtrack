#!/usr/bin/env python3
"""Create a YouTrack project from the retained Helix template."""

import argparse
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
STATES = ["TO DO", "IN PROGRESS", "IN REVIEW", "DONE"]
BOARD_FIELDS = (
    "id,name,projects(id),columnSettings(field(id,name),"
    "columns(id,ordinal,presentation,fieldValues(id,name))),"
    "sprintsSettings(disableSprints,isExplicit,explicitQuery,hideSubtasksOfCards),"
    "swimlaneSettings(id,$type,enabled,field(id,$type,customField(id)),values(id,name)),"
    "visibleForProjectBased,updateableByProjectBased"
)


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
        "?fields=field(id,name),bundle(values(name,isResolved)),defaultValues(name)&%24top=1000",
    )
    by_name = {item["field"]["name"]: item for item in fields}

    state = by_name.get("State", {})
    state_values = [value["name"] for value in state.get("bundle", {}).get("values", [])]
    state_default = [value["name"] for value in state.get("defaultValues", [])]
    if state_values != STATES or state_default != ["TO DO"]:
        fail("project was created, but its State configuration does not match the template")

    readiness = by_name.get("Agent Readiness", {})
    readiness_values = [
        value["name"] for value in readiness.get("bundle", {}).get("values", [])
    ]
    readiness_default = [value["name"] for value in readiness.get("defaultValues", [])]
    if readiness_values != ["Pending Review", "Approved"] or readiness_default != ["Pending Review"]:
        fail("project was created, but its Agent Readiness configuration does not match the template")

    return state


def ensure_board(token, project, state):
    """Configure the sole project board, retaining its identity and column IDs."""
    project_id = project["id"]
    boards = []
    for skip in range(0, 100000, 100):
        page = api(token, "GET", "/api/agiles?fields=id,name,projects(id)"
                   f"&%24top=100&%24skip={skip}")
        boards.extend(b for b in page if project_id in [p["id"] for p in b["projects"]])
        if len(page) < 100:
            break
    else:
        fail("board listing did not finish; no board was changed")
    if len(boards) > 1 or any(len(b["projects"]) != 1 for b in boards):
        fail("project has multiple or shared boards; choose the default board manually")
    if boards:
        board_id = boards[0]["id"]
    else:
        board = api(token, "POST", "/api/agiles?template=kanban&fields=id", {
            "name": project["name"] + " Kanban", "projects": [{"id": project_id}],
            "owner": {"id": project["leader"]["id"]},
            "visibleForProjectBased": True, "updateableByProjectBased": True,
        })
        board_id = board["id"]
    path = "/api/agiles/" + urllib.parse.quote(board_id, safe="")
    read_path = path + "?" + urllib.parse.urlencode({"fields": BOARD_FIELDS})
    board = api(token, "GET", read_path)
    settings = board["columnSettings"]
    if settings["field"]["id"] != state["field"]["id"]:
        fail("existing board columns do not use State; no board was changed")
    existing = {c["presentation"].upper(): c for c in settings["columns"]}
    if len(existing) != len(settings["columns"]) or set(existing) - set(STATES):
        fail("existing board has custom columns; no columns were removed")
    columns = []
    for ordinal, name in enumerate(STATES):
        column = {"ordinal": ordinal, "fieldValues": [{"name": name}]}
        if name in existing:
            old = existing[name]
            column["id"] = old["id"]
            column["fieldValues"] = [{"id": v["id"]} for v in old["fieldValues"]]
        columns.append(column)
    payload = {
        "name": project["name"] + " Kanban",
        "columnSettings": {"field": {"id": state["field"]["id"]}, "columns": columns},
        "sprintsSettings": {"disableSprints": True, "isExplicit": False,
                           "explicitQuery": "project: " + project["shortName"],
                           "hideSubtasksOfCards": False},
        "visibleForProjectBased": True, "updateableByProjectBased": True,
    }
    if board.get("swimlaneSettings"):
        # YouTrack requires the concrete type and field even when disabling swimlanes.
        payload["swimlaneSettings"] = dict(board["swimlaneSettings"], enabled=False)
    api(token, "POST", path, payload)
    verified = api(token, "GET", read_path)
    names = [c["presentation"] for c in sorted(
        verified["columnSettings"]["columns"], key=lambda c: c["ordinal"])]
    sprint = verified["sprintsSettings"]
    if (verified["name"] != payload["name"] or names != STATES
            or verified["projects"] != board["projects"]
            or not sprint["disableSprints"] or sprint["isExplicit"]
            or sprint["explicitQuery"] != payload["sprintsSettings"]["explicitQuery"]
            or sprint["hideSubtasksOfCards"]
            or (verified.get("swimlaneSettings") or {}).get("enabled", False)
            or not verified["visibleForProjectBased"]
            or not verified["updateableByProjectBased"]):
        fail(f"board {board_id} readback does not match; inspect it before retrying")
    return board_id


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair-board", metavar="PROJECT_KEY",
                        help="configure an existing project's sole board; does not recreate the project")
    args = parser.parse_args()
    if args.repair_board:
        token = read_token()
        key = urllib.parse.quote(args.repair_board.upper(), safe="")
        project = api(token, "GET", f"/api/admin/projects/{key}?fields=id,name,shortName,leader(id)")
        state = verify_fields(token, project["id"])
        board_id = ensure_board(token, project, state)
        print(f"Verified Kanban board: {BASE_URL}/agiles/{board_id}/current")
        return
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

    state = verify_fields(token, project["id"])
    board_id = ensure_board(token, project, state)
    print(f"\nCreated {project['name']} ({project['shortName']}).")
    print(f"Verified State and Agent Readiness fields: {BASE_URL}/projects/{project['shortName']}")
    print(f"Verified Kanban board: {BASE_URL}/agiles/{board_id}/current")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        raise SystemExit(130)
