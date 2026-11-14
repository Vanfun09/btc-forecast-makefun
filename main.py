import json, os, math

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def forecast_btc(prices, horizon):
    """Forecast BTC price horizon minutes ahead using weighted linear regression + mean reversion."""
    n = len(prices)
    if n == 0:
        return 0.0
    last = prices[-1]
    
    # Use multiple timeframes and blend
    predictions = []
    weights = []
    
    # 1. Persistence (last price) - always a strong baseline
    predictions.append(last)
    weights.append(2.0)
    
    # 2. Short-term trend (last 60 min) extrapolated
    if n >= 60:
        window = prices[-60:]
        # Weighted linear regression (more weight on recent)
        sw = sx = sy = sxy = sx2 = 0.0
        for i, p in enumerate(window):
            w = 1.0 + i / len(window)  # increasing weight
            sw += w
            sx += w * i
            sy += w * p
            sxy += w * i * p
            sx2 += w * i * i
        denom = sw * sx2 - sx * sx
        if abs(denom) > 1e-10:
            slope = (sw * sxy - sx * sy) / denom
            # Dampen extrapolation (mean reversion factor)
            dampen = 0.3
            pred = last + slope * horizon * dampen
            predictions.append(pred)
            weights.append(1.5)
    
    # 3. Medium-term trend (last 240 min = 4h)
    if n >= 240:
        window = prices[-240:]
        sw = sx = sy = sxy = sx2 = 0.0
        for i, p in enumerate(window):
            w = 1.0 + i / len(window)
            sw += w
            sx += w * i
            sy += w * p
            sxy += w * i * p
            sx2 += w * i * i
        denom = sw * sx2 - sx * sx
        if abs(denom) > 1e-10:
            slope = (sw * sxy - sx * sy) / denom
            dampen = 0.15
            pred = last + slope * horizon * dampen
            predictions.append(pred)
            weights.append(1.0)
    
    # 4. Mean reversion toward recent average
    if n >= 720:  # 12 hours
        avg_12h = sum(prices[-720:]) / 720
        # Slight pull toward 12h average
        pred = last + (avg_12h - last) * 0.05
        predictions.append(pred)
        weights.append(0.5)
    
    # Weighted average of all predictions
    total_w = sum(weights)
    result = sum(p * w for p, w in zip(predictions, weights)) / total_w
    
    return round(result, 5)

inputs = sorted(f for f in os.listdir(INPUT_DIR) if f.endswith(".in"))
for fname in inputs:
    case_id = fname[:-3]
    with open(os.path.join(INPUT_DIR, fname)) as f:
        case = json.load(f)
    
    prices = case["markets"][0]["prices"]
    horizon = case["horizon_minutes"]
    prediction = forecast_btc(prices, horizon)
    
    with open(os.path.join(OUTPUT_DIR, f"{case_id}.out"), "w") as f:
        f.write(f"{prediction}\n")
