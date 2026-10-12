import tempfile
import unittest
from pathlib import Path

from connector.billsmart_payment_registry import (
    load_payment,
    save_payment,
)


class PaymentRegistryTestCase(unittest.TestCase):
    def test_payment_is_persisted_and_reloaded(self):
        payment = {
            "payment_id": "BLB-PAY-0001",
            "sale_id": "BLB-REAL-0001",
            "amount": "6.20",
            "currency": "EUR",
            "provider": "sumup",
            "status": "created",
            "provider_checkout_id": None,
        }

        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "payments.json"

            save_payment(payment, state_path=state_path)

            stored = load_payment(
                "BLB-PAY-0001",
                state_path=state_path,
            )

            self.assertEqual(stored, payment)
            self.assertEqual(stored["sale_id"], "BLB-REAL-0001")


if __name__ == "__main__":
    unittest.main()


def test_duplicate_payment_is_rejected():
    import pytest

    payment = {
        "payment_id": "BLB-PAY-DUP-001",
        "sale_id": "BLB-SALE-001",
        "amount": "6.20",
        "currency": "EUR",
        "provider": "sumup",
        "status": "created",
        "provider_checkout_id": None,
    }

    with tempfile.TemporaryDirectory() as tmp:
        state_path = Path(tmp) / "payments.json"

        save_payment(payment, state_path=state_path)

        with pytest.raises(ValueError, match="Payment already registered"):
            save_payment(payment, state_path=state_path)

        assert load_payment(
            "BLB-PAY-DUP-001",
            state_path=state_path,
        ) == payment


def test_invalid_payment_amount_is_rejected():
    import pytest

    payment = {
        "payment_id": "BLB-PAY-INVALID-001",
        "sale_id": "BLB-SALE-001",
        "amount": "6.205",
        "currency": "EUR",
        "provider": "sumup",
        "status": "created",
        "provider_checkout_id": None,
    }

    with tempfile.TemporaryDirectory() as tmp:
        state_path = Path(tmp) / "payments.json"

        with pytest.raises(ValueError, match="Invalid payment amount"):
            save_payment(payment, state_path=state_path)

        assert not state_path.exists()
