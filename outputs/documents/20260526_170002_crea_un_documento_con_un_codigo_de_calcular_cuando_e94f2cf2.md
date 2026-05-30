```markdown
# Calculadora de Valor de Token

## Descripción

Este programa permite calcular el valor de un token basándose en su precio y cantidad disponible.

## Código

```python
def calculate_token_value(price, quantity):
    """
    Calcula el valor total de un token.

    Args:
        price (float): El precio del token.
        quantity (int): La cantidad de tokens disponibles.

    Returns:
        float: El valor total del token.
    """
    value = price * quantity
    return value

# Ejemplo de uso
price_per_token = 10.5
available_quantity = 120
total_value = calculate_token_value(price_per_token, available_quantity)
print(f"El valor total de los tokens es: ${total_value}")
```

## Información pendiente

- Agregar soporte para diferentes tipos de monedas.
- Implementar validaciones para los inputs.
```