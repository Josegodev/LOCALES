```c
#include <stdio.h>

int main() {
    float a, b, area;

    printf("Ingrese la longitud del semieje mayor (a): ");
    scanf("%f", &a);
    printf("Ingrese la longitud del semieje menor (b): ");
    scanf("%f", &b);

    area = 3.14159 * a * b;

    printf("El área de la elipse es: %.2f\n", area);

    return 0;
}
```