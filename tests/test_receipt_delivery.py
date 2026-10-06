from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from connector.idempotency import is_transaction_processed
from connector.receipt_delivery import deliver_receipt


class ReceiptDeliveryTestCase(unittest.TestCase):
    @patch("connector.receipt_delivery.ingest_csv_with_bsm1")
    def test_created_receipt_marks_transaction_processed(self, ingest):
        ingest.return_value = {
            "ok": True,
            "receipt": {"receipt_id": 42, "public_token": "token-42"},
            "edge": {"ok": True},
        }

        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"

            result = deliver_receipt(
                "tx-42",
                "ticket.csv",
                state_path=state_path,
            )

            self.assertTrue(
                is_transaction_processed("tx-42", state_path=state_path)
            )

        self.assertFalse(result["already_processed"])

    @patch("connector.receipt_delivery.ingest_csv_with_bsm1")
    def test_edge_failure_still_marks_transaction_processed(self, ingest):
        ingest.return_value = {
            "ok": False,
            "receipt": {"receipt_id": 43, "public_token": "token-43"},
            "edge": {"ok": False},
        }

        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"

            deliver_receipt(
                "tx-43",
                "ticket.csv",
                state_path=state_path,
            )

            self.assertTrue(
                is_transaction_processed("tx-43", state_path=state_path)
            )

    @patch("connector.receipt_delivery.ingest_csv_with_bsm1")
    def test_processed_transaction_is_not_ingested_again(self, ingest):
        ingest.return_value = {
            "ok": True,
            "receipt": {"receipt_id": 44, "public_token": "token-44"},
            "edge": {"ok": True},
        }
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"

            first = deliver_receipt(
                "tx-44",
                "ticket.csv",
                state_path=state_path,
            )
            second = deliver_receipt(
                "tx-44",
                "ticket.csv",
                state_path=state_path,
            )

        self.assertFalse(first["already_processed"])
        self.assertTrue(second["already_processed"])
        ingest.assert_called_once()


if __name__ == "__main__":
    unittest.main()
