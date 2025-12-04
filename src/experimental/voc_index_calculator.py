import math
from dataclasses import dataclass

@dataclass
class VOCIndexState:
    baseline: float = None

class VOCIndexCalculator:
    """
    Simple custom VOC index based on deviation from a moving baseline.
    Not compatible with Sensirion's official VOC index, but good for
    relative indoor air quality indication.
    """
    def __init__(self, baseline_alpha: float = 0.001, scale: float = 300.0):
        """
        :param baseline_alpha: How quickly the baseline adapts (smaller = slower).
        :param scale: How strongly deviations affect the index.
        """
        self.state = VOCIndexState()
        self.baseline_alpha = baseline_alpha
        self.scale = scale

    def update(self, raw_value: int) -> int:
        """
        Feed a new raw VOC value and get back a VOC index (0–500-ish).
        Call this once per measurement (e.g. every 1–10 seconds).
        """
        raw = float(raw_value)

        # Initialise baseline on first reading
        if self.state.baseline is None:
            self.state.baseline = raw
            return 100  # neutral starting point

        # Update baseline with exponential moving average (slow)
        b = self.state.baseline
        alpha = self.baseline_alpha
        b_new = (1.0 - alpha) * b + alpha * raw
        self.state.baseline = b_new

        # Compute relative deviation from baseline
        # e.g. +0.5 means 50% above baseline
        if b_new <= 0:
            rel = 0.0
        else:
            rel = (raw - b_new) / b_new

        # Map to index using a squashed function so it doesn't blow up
        # For small deviations, index stays near 100; larger deviations push it up/down.
        # You can tweak scale to change sensitivity.
        x = rel * (self.scale / 100.0)
        idx = 100 + 200 * math.tanh(x)  # roughly 0–200 above/below 100

        # Clamp to 0–500 range
        idx = max(0, min(500, int(round(idx))))
        return idx

def classify_voc_index(index: int) -> str:
    if index < 80:
        return "Excellent"
    elif index < 120:
        return "Good"
    elif index < 160:
        return "Moderate"
    elif index < 220:
        return "Unhealthy"
    else:
        return "Very Unhealthy"
