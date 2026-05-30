```php
<?php
function calcularPi($decimales) {
    $pi = 0;
    for ($i = 0; $i < $decimales * 14; $i++) {
        $pi += (pow(-1, $i)) / (2 * $i + 1);
    }
    return round($pi * 4, $decimales);
}

echo calcularPi(10); // Imprime el valor de pi con 10 decimales
?>
```