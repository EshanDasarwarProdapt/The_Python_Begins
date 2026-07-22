class Subscriber:
    def __init__(self, msisdn, plan_type):
        self.msisdn = msisdn
        self.plan_type = plan_type
        self.calls = []

    def add_call(self, call):
        self.calls.append(call)

    def total_cost(self):
        total = 0

        for call in self.calls:
            total += call.cost

        return round(total, 2)


class CDR:
    def __init__(self, msisdn, call_type, duration_sec, cost):
        self.msisdn = msisdn
        self.call_type = call_type
        self.duration_sec = duration_sec
        self.cost = cost

    def is_suspicious(self, threshold=3600):

        if self.duration_sec > 0 and self.cost == 0:
            return True

        if self.call_type == "international" and self.duration_sec > threshold:
            return True

        return False
