```markdown
# Calculadora de Números Primos en Python

## Función para determinar si un número es primo

```python
def es_primo(n):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True
```

## Función para generar una lista de números primos hasta un límite dado

```python
def genera_lista_primos(limite):
    primos = []
    for numero in range(2, limite + 1):
        if es_primo(numero):
            primos.append(numero)
    return primos
```

## Ejemplo de uso

```python
limite = 50
primos = genera_lista_primos(limite)
print("Los números primos hasta {} son:".format(limite))
for primo in primos:
    print(primo, end=" ")
```

Información pendiente:
- No se ha especificado cómo se utilizará el código generado.
- No se ha incluido una función para comprobar si un número es primo de manera interactiva.