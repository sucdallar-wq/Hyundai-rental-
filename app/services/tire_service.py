def calculate_tire_cost(model, total_hours, tire_price):
    """
    Lastik maliyetini saatlik oransal (amortisman) modeline göre hesaplar.
    Böylece lastik ömrü tam dolmasa bile çalışılan saat kadar maliyet teklife yansır.
    """
    tire_life = 4000
    
    # int() kaldırıldı, doğrusal aşınma oranı hesaplanıyor (Örn: 3000/4000 = 0.75)
    replacements = float(total_hours) / float(tire_life)
    
    return replacements * float(tire_price)
