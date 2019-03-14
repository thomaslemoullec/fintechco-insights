import math


def allocate(total, weights):
    # split total across weights, biggest slice absorbs the rounding
    if not weights:
        return []
    s = sum(weights)
    out = []
    acc = 0
    for w in weights:
        p = int(total * w / s)
        out.append(p)
        acc += p
    out[0] += total - acc
    return out


def apply_daily_interest(balance, rate, days):
    r = rate / 10000.0
    b = balance
    for _ in range(days):
        b = b + math.floor(b * r / 365.0)
    return b
