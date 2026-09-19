"""Regression coverage for inherited demo boards and safe repair/retry."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "bootstrap", Path(__file__).resolve().parents[1] / "deploy/retained/bootstrap-project.py")
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)
PROJECT = {"id": "0-2", "name": "MCP Server", "shortName": "MCPSER", "leader": {"id": "2-1"}}
STATE = {"field": {"id": "157-2", "name": "State"}}
BEFORE = {
    "id": "201-2", "name": "Demo project Overview-copy", "projects": [{"id": "0-2"}],
    "columnSettings": {"field": STATE["field"], "columns": [
        {"id": "202-6", "ordinal": 0, "presentation": "TO DO", "fieldValues": [{"id": "203-6", "name": "To do"}]},
        {"id": "202-7", "ordinal": 1, "presentation": "IN PROGRESS", "fieldValues": [{"id": "203-7", "name": "In Progress"}]},
        {"id": "202-8", "ordinal": 2, "presentation": "DONE", "fieldValues": [{"id": "203-8", "name": "Done"}]},
    ]},
    "sprintsSettings": {"disableSprints": True, "isExplicit": False, "explicitQuery": "Type: Task", "hideSubtasksOfCards": True},
    "swimlaneSettings": {"id": "195-2", "$type": "AttributeBasedSwimlaneSettings", "enabled": True,
                         "field": {"id": "157-4", "$type": "CustomFilterField", "customField": {"id": "157-4"}}, "values": []},
    "visibleForProjectBased": True, "updateableByProjectBased": True,
}
AFTER = copy.deepcopy(BEFORE)
AFTER["name"] = "MCP Server Kanban"
AFTER["columnSettings"]["columns"][-1]["ordinal"] = 3
AFTER["columnSettings"]["columns"].append({"id": "202-17", "ordinal": 2, "presentation": "IN REVIEW", "fieldValues": [{"id": "203-19", "name": "IN REVIEW"}]})
AFTER["sprintsSettings"].update(explicitQuery="project: MCPSER", hideSubtasksOfCards=False)
AFTER["swimlaneSettings"]["enabled"] = False


class BoardTests(unittest.TestCase):
    def run_board(self, before, after):
        api = unittest.mock.Mock(side_effect=[[before], before, None, after])
        with patch.object(bootstrap, "api", api):
            self.assertEqual("201-2", bootstrap.ensure_board("test-token", PROJECT, STATE))
        return api

    def test_inherited_columns_keep_ids_and_review_is_inserted_before_done(self):
        api = self.run_board(BEFORE, AFTER)
        body = api.call_args_list[2].args[3]
        columns = body["columnSettings"]["columns"]
        self.assertEqual(["202-6", "202-7", None, "202-8"], [c.get("id") for c in columns])
        self.assertEqual([0, 1, 2, 3], [c["ordinal"] for c in columns])
        self.assertEqual([{"name": "IN REVIEW"}], columns[2]["fieldValues"])
        self.assertEqual([{"id": "203-6"}], columns[0]["fieldValues"])
        self.assertEqual("project: MCPSER", body["sprintsSettings"]["explicitQuery"])
        self.assertFalse(body["swimlaneSettings"]["enabled"])
        self.assertEqual(BEFORE["swimlaneSettings"]["field"], body["swimlaneSettings"]["field"])
        self.assertTrue(all(call.args[1] in {"GET", "POST"} for call in api.call_args_list))

    def test_repair_retry_keeps_board_and_all_four_columns(self):
        api = self.run_board(AFTER, AFTER)
        posts = [call for call in api.call_args_list if call.args[1] == "POST"]
        self.assertEqual(1, len(posts))
        self.assertEqual("/api/agiles/201-2", posts[0].args[2])
        self.assertEqual({"202-6", "202-7", "202-8", "202-17"},
                         {c["id"] for c in posts[0].args[3]["columnSettings"]["columns"]})

    def test_missing_board_is_created_once_and_then_configured(self):
        api = unittest.mock.Mock(side_effect=[[], {"id": "201-2"}, BEFORE, None, AFTER])
        with patch.object(bootstrap, "api", api):
            bootstrap.ensure_board("test-token", PROJECT, STATE)
        create = api.call_args_list[1]
        self.assertEqual("/api/agiles?template=kanban&fields=id", create.args[2])
        self.assertEqual([{"id": "0-2"}], create.args[3]["projects"])
        self.assertEqual({"id": "2-1"}, create.args[3]["owner"])

    def test_multiple_or_shared_boards_are_not_modified(self):
        shared = dict(BEFORE, projects=[{"id": "0-2"}, {"id": "0-0"}])
        for boards in [[BEFORE, dict(BEFORE, id="201-3")], [shared]]:
            with self.subTest(boards=boards), patch.object(bootstrap, "api", return_value=boards) as api:
                with self.assertRaises(SystemExit):
                    bootstrap.ensure_board("test-token", PROJECT, STATE)
                self.assertEqual(1, api.call_count)

    def test_custom_columns_are_not_deleted(self):
        custom = copy.deepcopy(BEFORE)
        custom["columnSettings"]["columns"][0]["presentation"] = "CUSTOM"
        with patch.object(bootstrap, "api", side_effect=[[custom], custom]) as api:
            with self.assertRaises(SystemExit):
                bootstrap.ensure_board("test-token", PROJECT, STATE)
            self.assertEqual(2, api.call_count)

    def test_successful_http_without_matching_readback_is_not_success(self):
        with patch.object(bootstrap, "api", side_effect=[[BEFORE], BEFORE, None, BEFORE]):
            with self.assertRaises(SystemExit):
                bootstrap.ensure_board("test-token", PROJECT, STATE)


if __name__ == "__main__":
    unittest.main()
