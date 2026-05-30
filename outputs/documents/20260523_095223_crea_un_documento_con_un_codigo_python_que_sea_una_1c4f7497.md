# Calculadora de Números Primos
## Introducción

Esta es una calculadora de números primos desarrollada en Python. Un número primo es un número natural mayor que 1 que no tiene otros divisores positivos aparte de 1 y él mismo.

## Código

```python
def es_primo(n):
    """
    Comprueba si un número es primo.
    
    Args:
        n (int): El número a comprobar.
    
    Returns:
        bool: True si el número es primo, False en caso contrario.
    """
    if n <= 1:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True

def calculadora_primos():
    """
    Calcula los números primos en un rango determinado.
    
    Pide al usuario que ingrese el límite superior del rango y luego imprime todos los números primos en ese rango.
    """
    limite = int(input("Ingrese el límite superior del rango: "))
    primos = [i for i in range(2, limite + 1) if es_primo(i)]
    print("Números primos en el rango:", primos)

if __name__ == "__main__":
    calculadora_primos()
```

## Uso

Para usar esta calculadora de números primos, simplemente ejecuta el script y seguirá las instrucciones que se te mostrarán por pantalla.

## Información Pendiente

* No hay información pendiente en este momento.