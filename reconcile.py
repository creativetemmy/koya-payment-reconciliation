
#!/usr/bin/env python3

"""Reconcile payment attempts and print the verification code."""

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path


def parse_timestamp(value):
    """Parse an ISO timestamp, including UTC timestamps ending in Z."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def reconcile():
    base_dir = Path(__file__).resolve().parent
    payments_file = base_dir / "payments.jsonl"
    expected_file = base_dir / "expected.txt"

    latest_by_transaction = {}

    with payments_file.open("r", encoding="utf-8") as file:
        for line in file:
            try:
                event = json.loads(line)

                txn_id = event.get("txn_id")
                if not txn_id:
                    continue

                timestamp = parse_timestamp(event["ts"])

                previous = latest_by_transaction.get(txn_id)

                if (
                    previous is None
                    or timestamp >= previous["_parsed_ts"]
                ):
                    event["_parsed_ts"] = timestamp
                    latest_by_transaction[txn_id] = event

            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                continue

    successful_payments = [
        event
        for event in latest_by_transaction.values()
        if event.get("status") == "success"
    ]

    total = sum(
        (
            Decimal(str(event["amount"]).replace(",", "").strip())
            for event in successful_payments
        ),
        Decimal("0"),
    )

    count = len(successful_payments)
    expected = int(expected_file.read_text(encoding="utf-8").strip())

    if count != expected:
        print(
            f"Check failed: counted {count} successful payments, "
            f"expected {expected}."
        )
        print(
            "Check the event parsing and latest-attempt logic "
            "before submitting."
        )
        return

    print(f"Check passed: {count} successful payments.")
    print(f"Your code: KOYA-{round(total)}")


if __name__ == "__main__":
    reconcile()
