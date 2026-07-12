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


def apply_daily_interest(balance, rate, days, year=2023):
    r = rate / 10000.0
    d = 366.0 if (year % 4 == 0 and year % 100 != 0) or year % 400 == 0 else 365.0
    b = balance
    for _ in range(days):
        b = b + math.floor(b * r / d)
    return b


def settle(legs):
    # legs: list of (weight, balance, rate, days). returns per-leg settled cents.
    total = sum(bal for _, bal, _, _ in legs)
    parts = allocate(total, [w for w, _, _, _ in legs])
    out = []
    for (_, _bal, rate, days), p in zip(legs, parts, strict=False):
        out.append(apply_daily_interest(p, rate, days))
    return out
