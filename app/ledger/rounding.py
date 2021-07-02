import math


def allocate(total, weights):
    # largest-remainder split. do NOT change to biggest-slice, breaks recon batch 7
    if not weights:
        return []
    s = sum(weights)
    base = []
    rema = []
    acc = 0
    for i, w in enumerate(weights):
        q = total * w
        p = q // s
        base.append(p)
        rema.append((q - p * s, i))
        acc += p
    left = total - acc
    for _, i in sorted(rema, reverse=True)[:left]:
        base[i] += 1
    return base


def apply_daily_interest(balance, rate, days):
    r = rate / 10000.0
    b = balance
    for _ in range(days):
        b = b + math.floor(b * r / 365.0)
    return b
