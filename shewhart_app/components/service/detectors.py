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
            return (
                True,
                f"Asterisk pattern detected above the mean starting at point {i - 6}",
            )
    return False, ""


def detect_trends_x(data_points):
    increasing_trend = 0
    decreasing_trend = 0
    for i in range(1, len(data_points)):
        if data_points[i] > data_points[i - 1]:
            increasing_trend += 1
            decreasing_trend = 0
        elif data_points[i] < data_points[i - 1]:
            decreasing_trend += 1
            increasing_trend = 0
        else:
            increasing_trend = 0
            decreasing_trend = 0

        if (
            increasing_trend >= 7
        ):  # значение 7 может быть изменено в зависимости от ваших потребностей
            return True, f"Increasing trend detected starting at point {i - 6}"
        if decreasing_trend >= 7:
            return True, f"Decreasing trend detected starting at point {i - 6}"

    return False, ""


# Функция для определения сдвигов в данных
def detect_shifts_x(data_points, mean_value):
    above_mean = 0
    below_mean = 0
    for point in data_points:
        if point > mean_value:
            above_mean += 1
            below_mean = 0
        elif point < mean_value:
            below_mean += 1
            above_mean = 0
        else:
            above_mean = 0
            below_mean = 0

        if (
            above_mean >= 8
        ):  # значение 8 может быть изменено в зависимости от ваших потребностей
            return True, "Shift above the mean detected"
        if below_mean >= 8:
            return True, "Shift below the mean detected"

    return False, ""


def detect_asterisks_x(data_points, mean_value):
    above_mean = 0
    for point in data_points:
        if point > mean_value:
            above_mean += 1
        else:
            above_mean = 0  # сброс счетчика, если точка ниже среднего

        if (
            above_mean >= 7
        ):  # значение 7 может быть изменено в зависимости от ваших потребностей
            return (
                True,
                f"Asterisk pattern detected above the mean starting at point {len(data_points) - above_mean}",
            )

    return False, ""
