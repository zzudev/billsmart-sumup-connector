from __future__ import annotations

import logging
import subprocess
import sys
import time


POLL_INTERVAL_SECONDS = 5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


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
    logger.info(
        "Surveillance SumUp démarrée "
        "(intervalle : %s s).",
        POLL_INTERVAL_SECONDS,
    )

    try:
        while True:
            try:
                return_code = run_cycle()

                if return_code != 0:
                    logger.warning(
                        "Cycle SumUp terminé avec le code %s.",
                        return_code,
                    )

            except Exception:
                logger.exception(
                    "Erreur pendant le cycle SumUp."
                )

            time.sleep(POLL_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        logger.info("Surveillance SumUp arrêtée.")


if __name__ == "__main__":
    main()
