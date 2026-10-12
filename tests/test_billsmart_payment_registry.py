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


def test_provider_checkout_reference_is_persisted():
    payment = {
        "payment_id": "BLB-PAY-REF-001",
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

        from connector.billsmart_payment_registry import (
            set_provider_checkout_reference,
        )

        set_provider_checkout_reference(
            "BLB-PAY-REF-001",
            "SUMUP-CHECKOUT-001",
            state_path=state_path,
        )

        restored = load_payment(
            "BLB-PAY-REF-001",
            state_path=state_path,
        )

        assert restored["sale_id"] == "BLB-SALE-001"
        assert restored["provider_checkout_id"] == "SUMUP-CHECKOUT-001"


def test_conflicting_provider_reference_is_rejected():
    import pytest

    from connector.billsmart_payment_registry import (
        set_provider_checkout_reference,
    )

    payment = {
        "payment_id": "BLB-PAY-CONFLICT-001",
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

        set_provider_checkout_reference(
            payment["payment_id"],
            "CHECKOUT-001",
            state_path=state_path,
        )

        with pytest.raises(
            ValueError,
            match="Conflicting provider checkout reference",
        ):
            set_provider_checkout_reference(
                payment["payment_id"],
                "CHECKOUT-002",
                state_path=state_path,
            )

        restored = load_payment(
            payment["payment_id"],
            state_path=state_path,
        )

        assert restored["provider_checkout_id"] == "CHECKOUT-001"


def test_provider_reference_cannot_be_shared_by_two_payments():
    import pytest

    from connector.billsmart_payment_registry import (
        set_provider_checkout_reference,
    )

    with tempfile.TemporaryDirectory() as tmp:
        state_path = Path(tmp) / "payments.json"

        for payment_id in ("BLB-PAY-001", "BLB-PAY-002"):
            save_payment(
                {
                    "payment_id": payment_id,
                    "sale_id": "BLB-SALE-001",
                    "amount": "6.20",
                    "currency": "EUR",
                    "provider": "sumup",
                    "status": "created",
                    "provider_checkout_id": None,
                },
                state_path=state_path,
            )

        set_provider_checkout_reference(
            "BLB-PAY-001",
            "CHECKOUT-001",
            state_path=state_path,
        )

        with pytest.raises(
            ValueError,
            match="Provider checkout reference already assigned",
        ):
            set_provider_checkout_reference(
                "BLB-PAY-002",
                "CHECKOUT-001",
                state_path=state_path,
            )

        assert load_payment(
            "BLB-PAY-002",
            state_path=state_path,
        )["provider_checkout_id"] is None
