from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from connector.idempotency import (
    is_transaction_processed,
    load_registry,
    mark_transaction_processed,
)


class IdempotencyTestCase(unittest.TestCase):
    def test_unknown_transaction_is_not_processed(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "processed.json"

            self.assertFalse(
                is_transaction_processed(
                    "txn-001",
                    state_path=state_path,
                )
            )

    def test_processed_transaction_is_persisted_and_reloaded(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "processed.json"

            receipt_data = {
                "receipt_id": 42,
                "public_token": "token-42",
            }

            mark_transaction_processed(
                "txn-001",
                receipt_data,
                state_path=state_path,
            )

            self.assertTrue(
                is_transaction_processed(
                    "txn-001",
                    state_path=state_path,
                )
            )

            registry = load_registry(state_path)

            self.assertEqual(
                registry["txn-001"],
                receipt_data,
            )

    def test_multiple_transactions_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "processed.json"

            mark_transaction_processed(
                "txn-001",
                {"receipt_id": 42},
                state_path=state_path,
            )
            mark_transaction_processed(
                "txn-002",
                {"receipt_id": 43},
                state_path=state_path,
            )

            registry = load_registry(state_path)

            self.assertEqual(registry["txn-001"]["receipt_id"], 42)
            self.assertEqual(registry["txn-002"]["receipt_id"], 43)


if __name__ == "__main__":
    unittest.main()
