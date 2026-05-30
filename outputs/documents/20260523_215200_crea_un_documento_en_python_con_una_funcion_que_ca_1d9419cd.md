```python
def calcular_pi(n):
    """
    Calcula el valor de Pi usando el método de Monte Carlo.

    Args:
        n (int): El número de puntos aleatorios a generar.

    Returns:
        float: Aproximación del valor de Pi.
    """
    import random

    dentro_circulo = 0
    total_puntos = 0

    for _ in range(n):
        x, y = random.random(), random.random()
        if x**2 + y**2 <= 1:
            dentro_circulo += 1
        total_puntos += 1

    return 4 * (dentro_circulo / total_puntos)

# Ejemplo de uso
aproximacion_pi = calcular_pi(1000000)
print(f"Aproximación de Pi: {aproximacion_pi}")
```