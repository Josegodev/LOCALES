```python
def is_prime(n):
    """Verifica si un número es primo."""
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

def calcular_primos_ordenados(start, end):
    """Calcula y devuelve una lista de números primos ordenados entre start y end."""
    return [num for num in range(start, end + 1) if is_prime(num)]

# Ejemplo de uso
start = int(input("Ingrese el inicio del rango: "))
end = int(input("Ingrese el final del rango: "))

primos_ordenados = calcular_primos_ordenados(start, end)
print(f"Números primos entre {start} y {end}: {primos_ordenados}")
```

**Información pendiente:**  
- Asegúrate de que los valores de `start` e `end` sean enteros válidos.  
- Considera manejar excepciones para entradas no numéricas o rangos inválidos (por ejemplo, cuando `start > end`).