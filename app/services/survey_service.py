def calculate_usage_factor(score):

    if score <= 22:
        return 1.0

    elif score <= 33:
        return 1.1

    else:
        return 1.2


def calculate_residual_factor(usage_factor):

    if usage_factor == 1.0:
        return 1.0

    elif usage_factor == 1.1:
        return 0.95

    else:
        return 0.90