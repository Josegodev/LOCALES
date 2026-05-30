```python
def es_primo(num):
    if num <= 1:
        return False
    for i in range(2, int(num**0.5) + 1):
        if num % i == 0:
            return False
    return True

def calcular_numeros_primos(limite):
    primos = []
    for numero in range(2, limite + 1):
        if es_primo(numero):
            primos.append(numero)
    return primos

# Ejemplo de uso
limite = int(input("Introduce el límite para buscar números primos: "))
primos_encontrados = calcular_numeros_primos(limite)
print(f"Números primos hasta {limite}: {primos_encontrados}")
```