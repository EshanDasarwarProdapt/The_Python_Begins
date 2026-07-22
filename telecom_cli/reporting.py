from rating import compute_cost
from models import CDR
from fraud import is_suspicious


def build_report(subscribers, cdrs, threshold):

    unknown_subscribers = set()
    fraud_suspects = []

    for item in cdrs:

        msisdn = item["msisdn"]

        if msisdn not in subscribers:
            unknown_subscribers.add(msisdn)
            continue

        cost = compute_cost(
            item["call_type"],
            item["duration_sec"]
        )

        cdr = CDR(
            item["msisdn"],
            item["call_type"],
            item["duration_sec"],
            cost
        )

        subscribers[msisdn].add_call(cdr)

        if is_suspicious(cdr, threshold):
            fraud_suspects.append({
                "msisdn": cdr.msisdn,
                "call_type": cdr.call_type,
                "duration_sec": cdr.duration_sec,
                "cost": cdr.cost
            })

    subscriber_report = {}

    for msisdn, subscriber in subscribers.items():

        subscriber_report[msisdn] = {
            "plan_type": subscriber.plan_type,
            "call_count": len(subscriber.calls),
            "total_cost": subscriber.total_cost()
        }

    report = {
        "subscribers": subscriber_report,
        "unknown_subscribers": list(unknown_subscribers),
        "fraud_suspects": fraud_suspects
    }

    return report
