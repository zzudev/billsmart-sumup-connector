from __future__ import annotations

import subprocess
import sys
import time


POLL_INTERVAL_SECONDS = 5


def run_cycle() -> int:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "connector.build_billsmart_ticket",
        ],
        check=False,
    )
    return completed.returncode


def main() -> None:
    print(
        "Surveillance SumUp démarrée "
        f"(intervalle : {POLL_INTERVAL_SECONDS} s)."
    )

    try:
        while True:
            try:
                return_code = run_cycle()

                if return_code != 0:
                    print(
                        "Cycle SumUp en erreur "
                        f"(code {return_code})."
                    )

            except Exception as exc:
                print(
                    "Erreur pendant le cycle SumUp : "
                    f"{type(exc).__name__}: {exc}"
                )

            time.sleep(POLL_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\nSurveillance SumUp arrêtée.")


if __name__ == "__main__":
    main()
