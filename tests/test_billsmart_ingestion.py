from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from connector.billsmart_ingestion import ingest_csv_with_bsm1


class BillSmartIngestionTestCase(unittest.TestCase):
    @patch("connector.billsmart_ingestion.subprocess.run")
    def test_ingestion_calls_bsm1_cli_and_returns_json(self, run):
        run.return_value.stdout = json.dumps({
            "ok": True,
            "receipt": {
                "receipt_id": 42,
                "public_token": "token-42",
            },
            "edge": {"ok": True},
        })
        run.return_value.returncode = 0

        result = ingest_csv_with_bsm1(
            "runtime/tmp/ticket.csv",
            bsm1_root="/opt/bsm1",
        )

        self.assertEqual(result["receipt"]["receipt_id"], 42)

        command = run.call_args.args[0]
        self.assertEqual(command[0], "/opt/bsm1/venv/bin/python")
        self.assertEqual(
            command[1:3],
            ["-m", "backend.app.receipt_ingestion_cli"],
        )

        self.assertEqual(run.call_args.kwargs["cwd"], Path("/opt/bsm1"))
        self.assertTrue(run.call_args.kwargs["capture_output"])
        self.assertTrue(run.call_args.kwargs["text"])
        self.assertFalse(run.call_args.kwargs["check"])

    @patch("connector.billsmart_ingestion.subprocess.run")
    def test_invalid_json_raises_runtime_error(self, run):
        run.return_value.stdout = "not-json"
        run.return_value.returncode = 1

        with self.assertRaisesRegex(
            RuntimeError,
            "Réponse JSON invalide de BSM1",
        ):
            ingest_csv_with_bsm1(
                "runtime/tmp/ticket.csv",
                bsm1_root="/opt/bsm1",
            )

    @patch("connector.billsmart_ingestion.subprocess.run")
    def test_receipt_is_returned_even_if_edge_fails(self, run):
        run.return_value.stdout = json.dumps({
            "ok": False,
            "receipt": {
                "receipt_id": 43,
                "public_token": "token-43",
            },
            "edge": {
                "ok": False,
                "error_code": "edge_connection_error",
            },
        })
        run.return_value.returncode = 0

        result = ingest_csv_with_bsm1(
            "runtime/tmp/ticket.csv",
            bsm1_root="/opt/bsm1",
        )

        self.assertEqual(result["receipt"]["receipt_id"], 43)
        self.assertFalse(result["edge"]["ok"])



if __name__ == "__main__":
    unittest.main()
