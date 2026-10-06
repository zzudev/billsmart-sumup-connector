from __future__ import annotations

import unittest
from unittest.mock import patch

from connector.poll_sumup import run_cycle


class PollSumUpTestCase(unittest.TestCase):
    @patch("connector.poll_sumup.subprocess.run")
    def test_run_cycle_launches_ticket_builder(self, run):
        run.return_value.returncode = 0

        result = run_cycle()

        self.assertEqual(result, 0)

        command = run.call_args.args[0]

        self.assertEqual(
            command[1:],
            ["-m", "connector.build_billsmart_ticket"],
        )
        self.assertFalse(run.call_args.kwargs["check"])

    @patch(
        "connector.poll_sumup.time.sleep",
        side_effect=KeyboardInterrupt,
    )
    @patch(
        "connector.poll_sumup.run_cycle",
        side_effect=RuntimeError("erreur temporaire"),
    )
    def test_main_survives_cycle_exception(
        self,
        run_cycle,
        sleep,
    ):
        from connector.poll_sumup import main

        with self.assertLogs(
            "connector.poll_sumup",
            level="ERROR",
        ) as logs:
            main()

        run_cycle.assert_called_once_with()
        sleep.assert_called_once_with(5)

        self.assertTrue(
            any(
                "Erreur pendant le cycle SumUp."
                in message
                for message in logs.output
            )
        )


if __name__ == "__main__":
    unittest.main()
