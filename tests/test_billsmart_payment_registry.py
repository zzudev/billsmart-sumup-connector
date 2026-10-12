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


def test_payment_can_transition_from_created_to_pending():
    from connector.billsmart_payment_registry import update_payment_status

    payment = {
        "payment_id": "BLB-PAY-STATUS-001",
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

        update_payment_status(
            "BLB-PAY-STATUS-001",
            "pending",
            state_path=state_path,
        )

        restored = load_payment(
            "BLB-PAY-STATUS-001",
            state_path=state_path,
        )

        assert restored["status"] == "pending"
        assert restored["sale_id"] == "BLB-SALE-001"


def test_payment_cannot_succeed_directly_from_created():
    import pytest

    from connector.billsmart_payment_registry import update_payment_status

    payment = {
        "payment_id": "BLB-PAY-INVALID-TRANSITION-001",
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

        with pytest.raises(
            ValueError,
            match="Invalid payment status transition",
        ):
            update_payment_status(
                payment["payment_id"],
                "succeeded",
                state_path=state_path,
            )

        restored = load_payment(
            payment["payment_id"],
            state_path=state_path,
        )

        assert restored["status"] == "created"


def test_repeated_pending_transition_is_idempotent():
    from connector.billsmart_payment_registry import update_payment_status

    payment = {
        "payment_id": "BLB-PAY-IDEMPOTENT-001",
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

        first = update_payment_status(
            payment["payment_id"],
            "pending",
            state_path=state_path,
        )

        second = update_payment_status(
            payment["payment_id"],
            "pending",
            state_path=state_path,
        )

        restored = load_payment(
            payment["payment_id"],
            state_path=state_path,
        )

        assert first["status"] == "pending"
        assert second["status"] == "pending"
        assert restored["status"] == "pending"
        assert restored["sale_id"] == "BLB-SALE-001"


def test_pending_payment_can_transition_to_succeeded():
    from connector.billsmart_payment_registry import update_payment_status

    payment = {
        "payment_id": "BLB-PAY-SUCCESS-001",
        "sale_id": "BLB-SALE-001",
        "amount": "6.20",
        "currency": "EUR",
        "provider": "sumup",
        "status": "created",
        "provider_checkout_id": "CHECKOUT-SUCCESS-001",
    }

    with tempfile.TemporaryDirectory() as tmp:
        state_path = Path(tmp) / "payments.json"

        save_payment(payment, state_path=state_path)

        update_payment_status(
            payment["payment_id"],
            "pending",
            state_path=state_path,
        )

        update_payment_status(
            payment["payment_id"],
            "succeeded",
            state_path=state_path,
        )

        restored = load_payment(
            payment["payment_id"],
            state_path=state_path,
        )

        assert restored["status"] == "succeeded"
        assert restored["sale_id"] == "BLB-SALE-001"
        assert restored["provider_checkout_id"] == "CHECKOUT-SUCCESS-001"


def test_pending_payment_can_fail_or_be_cancelled():
    from connector.billsmart_payment_registry import update_payment_status

    for final_status in ("failed", "cancelled"):
        payment_id = f"BLB-PAY-{final_status.upper()}-001"

        payment = {
            "payment_id": payment_id,
            "sale_id": "BLB-SALE-001",
            "amount": "6.20",
            "currency": "EUR",
            "provider": "sumup",
            "status": "created",
            "provider_checkout_id": f"CHECKOUT-{final_status.upper()}-001",
        }

        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "payments.json"

            save_payment(payment, state_path=state_path)

            update_payment_status(
                payment_id,
                "pending",
                state_path=state_path,
            )

            update_payment_status(
                payment_id,
                final_status,
                state_path=state_path,
            )

            restored = load_payment(
                payment_id,
                state_path=state_path,
            )

            assert restored["status"] == final_status
            assert restored["sale_id"] == "BLB-SALE-001"


def test_pending_payment_can_fail_or_be_cancelled():
    from connector.billsmart_payment_registry import update_payment_status

    for final_status in ("failed", "cancelled"):
        payment_id = f"BLB-PAY-{final_status.upper()}-001"

        payment = {
            "payment_id": payment_id,
            "sale_id": "BLB-SALE-001",
            "amount": "6.20",
            "currency": "EUR",
            "provider": "sumup",
            "status": "created",
            "provider_checkout_id": f"CHECKOUT-{final_status.upper()}-001",
        }

        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "payments.json"

            save_payment(payment, state_path=state_path)

            update_payment_status(
                payment_id,
                "pending",
                state_path=state_path,
            )

            update_payment_status(
                payment_id,
                final_status,
                state_path=state_path,
            )

            restored = load_payment(
                payment_id,
                state_path=state_path,
            )

            assert restored["status"] == final_status
            assert restored["sale_id"] == "BLB-SALE-001"


def test_terminal_payment_statuses_cannot_be_changed():
    import pytest

    from connector.billsmart_payment_registry import update_payment_status

    for terminal_status in ("succeeded", "failed", "cancelled"):
        payment_id = f"BLB-PAY-TERMINAL-{terminal_status.upper()}"

        payment = {
            "payment_id": payment_id,
            "sale_id": "BLB-SALE-001",
            "amount": "6.20",
            "currency": "EUR",
            "provider": "sumup",
            "status": "created",
            "provider_checkout_id": f"CHECKOUT-{terminal_status.upper()}",
        }

        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "payments.json"

            save_payment(payment, state_path=state_path)

            update_payment_status(
                payment_id, "pending", state_path=state_path
            )

            update_payment_status(
                payment_id, terminal_status, state_path=state_path
            )

            for other_status in ("succeeded", "failed", "cancelled"):
                if other_status == terminal_status:
                    continue

                with pytest.raises(
                    ValueError,
                    match="Invalid payment status transition",
                ):
                    update_payment_status(
                        payment_id,
                        other_status,
                        state_path=state_path,
                    )

            restored = load_payment(payment_id, state_path=state_path)
            assert restored["status"] == terminal_status


def test_provider_client_transaction_reference_is_persisted():
    from connector.billsmart_payment_registry import (
        set_provider_client_transaction_reference,
    )

    payment = {
        "payment_id": "BLB-PAY-CLIENT-REF-001",
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

        set_provider_client_transaction_reference(
            payment["payment_id"],
            "CLIENT-TX-001",
            state_path=state_path,
        )

        restored = load_payment(
            payment["payment_id"],
            state_path=state_path,
        )

        assert restored["sale_id"] == "BLB-SALE-001"
        assert (
            restored["provider_client_transaction_id"]
            == "CLIENT-TX-001"
        )


def test_conflicting_provider_client_transaction_reference_is_rejected():
    import pytest

    from connector.billsmart_payment_registry import (
        set_provider_client_transaction_reference,
    )

    payment = {
        "payment_id": "BLB-PAY-CLIENT-CONFLICT-001",
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

        set_provider_client_transaction_reference(
            payment["payment_id"],
            "CLIENT-TX-001",
            state_path=state_path,
        )

        with pytest.raises(
            ValueError,
            match="Conflicting provider client transaction reference",
        ):
            set_provider_client_transaction_reference(
                payment["payment_id"],
                "CLIENT-TX-002",
                state_path=state_path,
            )

        restored = load_payment(
            payment["payment_id"],
            state_path=state_path,
        )

        assert restored["provider_client_transaction_id"] == "CLIENT-TX-001"


def test_provider_client_transaction_reference_cannot_be_shared():
    import pytest

    from connector.billsmart_payment_registry import (
        set_provider_client_transaction_reference,
    )

    with tempfile.TemporaryDirectory() as tmp:
        state_path = Path(tmp) / "payments.json"

        for payment_id in ("BLB-PAY-CLIENT-001", "BLB-PAY-CLIENT-002"):
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

        set_provider_client_transaction_reference(
            "BLB-PAY-CLIENT-001",
            "CLIENT-TX-001",
            state_path=state_path,
        )

        with pytest.raises(
            ValueError,
            match="Provider client transaction reference already assigned",
        ):
            set_provider_client_transaction_reference(
                "BLB-PAY-CLIENT-002",
                "CLIENT-TX-001",
                state_path=state_path,
            )

        restored = load_payment(
            "BLB-PAY-CLIENT-002",
            state_path=state_path,
        )

        assert restored.get("provider_client_transaction_id") is None


def test_repeated_provider_client_transaction_reference_is_idempotent():
    from connector.billsmart_payment_registry import (
        set_provider_client_transaction_reference,
    )

    payment = {
        "payment_id": "BLB-PAY-CLIENT-IDEMPOTENT-001",
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

        first = set_provider_client_transaction_reference(
            payment["payment_id"],
            "CLIENT-TX-001",
            state_path=state_path,
        )

        second = set_provider_client_transaction_reference(
            payment["payment_id"],
            "CLIENT-TX-001",
            state_path=state_path,
        )

        restored = load_payment(
            payment["payment_id"],
            state_path=state_path,
        )

        assert first["provider_client_transaction_id"] == "CLIENT-TX-001"
        assert second["provider_client_transaction_id"] == "CLIENT-TX-001"
        assert restored["provider_client_transaction_id"] == "CLIENT-TX-001"
        assert restored["sale_id"] == "BLB-SALE-001"
