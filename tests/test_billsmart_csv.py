from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from connector.billsmart_csv import build_billsmart_csv


class BillSmartCsvTestCase(unittest.TestCase):
    def test_builds_bsm1_compatible_csv(self):
        items = [
            {
                "price": 12.0,
                "quantity": 1,
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            output_path = build_billsmart_csv(
                items,
                output_dir=tmp,
                timestamp="20261005_120000",
            )

            self.assertEqual(
                output_path.name,
                "ticket_sumup_20261005_120000.csv",
            )

            with output_path.open(
                "r",
                encoding="utf-8",
                newline="",
            ) as csv_file:
                rows = list(csv.reader(csv_file))

        self.assertEqual(
            rows[0],
            ["reference", "designation", "quantite", "prix_unitaire"],
        )
        self.assertEqual(
            rows[1],
            ["SUMUP001", "Paiement SumUp", "1", "12.00"],
        )


if __name__ == "__main__":
    unittest.main()
