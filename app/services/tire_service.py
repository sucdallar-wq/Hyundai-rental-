def calculate_tire_cost(model, total_hours, tire_price):

    tire_life = 4000

    replacements = int(total_hours / tire_life)

    return replacements * tire_price