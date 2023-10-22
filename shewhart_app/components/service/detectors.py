def detect_trends(proportions):
    increasing_trend = 0
    decreasing_trend = 0
    for i in range(1, len(proportions)):
        if proportions[i] > proportions[i - 1]:
            increasing_trend += 1
            decreasing_trend = 0
        elif proportions[i] < proportions[i - 1]:
            decreasing_trend += 1
            increasing_trend = 0
        else:
            increasing_trend = 0
            decreasing_trend = 0
        if increasing_trend >= 7:
            return True, f"Increasing trend detected starting at point {i - 6}"
        if decreasing_trend >= 7:
            return True, f"Decreasing trend detected starting at point {i - 6}"
    return False, ""


def detect_shifts(proportions, p_bar):
    above_mean = 0
    below_mean = 0
    for i in range(len(proportions)):
        if proportions[i] > p_bar:
            above_mean += 1
            below_mean = 0
        elif proportions[i] < p_bar:
            below_mean += 1
            above_mean = 0
        else:
            above_mean = 0
            below_mean = 0
        if above_mean >= 8:
            return True, f"Shift above the mean detected starting at point {i - 7}"
        if below_mean >= 8:
            return True, f"Shift below the mean detected starting at point {i - 7}"
    return False, ""


def detect_asterisks(proportions, p_bar):
    above_mean = 0
    for i in range(len(proportions)):
        if proportions[i] > p_bar:
            above_mean += 1
        else:
            above_mean = 0
        if above_mean >= 7:
            return True, f"Asterisk pattern detected above the mean starting at point {i - 6}"
    return False, ""