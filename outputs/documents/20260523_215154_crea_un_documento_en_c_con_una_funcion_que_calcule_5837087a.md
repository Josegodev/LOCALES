```c
#include <stdio.h>
#include <math.h>

double calcularPi(int iteraciones) {
    double pi = 0.0;
    for (int i = 0; i < iteraciones; i++) {
        if (i % 2 == 0) {
            pi += 1.0 / (2 * i + 1);
        } else {
            pi -= 1.0 / (2 * i + 1);
        }
    }
    return pi * 4;
}

int main() {
    int iteraciones = 1000000;
    double resultado = calcularPi(iteraciones);
    printf("Aproximación de Pi con %d iteraciones: %.15f\n", iteraciones, resultado);
    return 0;
}
```