from config import RATES


def compute_cost(call_type, duration_sec):
    rate = RATES.get(call_type, RATES["domestic"])

    minutes = duration_sec / 60

    cost = rate * minutes

    return round(cost, 2)
