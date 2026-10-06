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


if __name__ == "__main__":
    unittest.main()
