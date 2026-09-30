"""Set the monthly account ceiling with the workflow's credential."""

import argparse
from decimal import Decimal

from legal_cost_guard.infrai_gateway import InfraiGateway


parser = argparse.ArgumentParser()
parser.add_argument("hard_cap_usd", type=Decimal)
parser.add_argument("--alert-threshold-usd", type=Decimal)
args = parser.parse_args()

result = InfraiGateway.from_environment().set_budget(
    hard_cap_usd=args.hard_cap_usd,
    period="monthly",
    alert_threshold_usd=args.alert_threshold_usd,
)
print(result)
