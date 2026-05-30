```markdown
# Suma de Números Primos en Python

Este documento contiene un ejemplo de código en Python que calcula la suma de números primos hasta un número dado \( n \).

## Código

```python
def es_primo(num):
    """Verifica si un número es primo."""
    if num <= 1:
        return False
    for i in range(2, int(num**0.5) + 1):
        if num % i == 0:
            return False
    return True

def suma_primos(n):
    """Calcula la suma de todos los números primos hasta n."""
    total = 0
    for i in range(2, n + 1):
        if es_primo(i):
            total += i
    return total

# Ejemplo de uso
n = 100  # Cambia este valor para calcular hasta otro número
resultado = suma_primos(n)
print(f"La suma de los números primos hasta {n} es: {resultado}")
```

## Explicación

1. **Función `es_primo(num)`**: Verifica si un número \( num \) es primo.
   - Si \( num \) es menor o igual a 1, no es primo.
   - Itera desde 2 hasta la raíz cuadrada de \( num \) para verificar divisores. Si encuentra uno, el número no es primo.

2. **Función `suma_primos(n)`**: Calcula la suma de todos los números primos desde 2 hasta \( n \).
   - Itera desde 2 hasta \( n \), verificando cada número con `es_primo`. Si un número es primo, lo añade al total.

3. **Ejemplo de uso**: Se establece \( n = 100 \) y se imprime la suma de los números primos hasta ese valor.

## Información pendiente
- No hay información pendiente.
```