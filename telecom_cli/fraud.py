def is_suspicious(cdr, threshold=3600):

    if cdr.duration_sec > 0 and cdr.cost == 0:
        return True

    if cdr.call_type == "international" and cdr.duration_sec > threshold:
        return True

    return False