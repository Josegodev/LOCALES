```c
#include <stdio.h>
#include <math.h>

int main() {
    int n;
    printf("Ingrese el número de términos para la serie de Leibniz: ");
    scanf("%d", &n);

    double pi = 0.0;
    for (int i = 0; i < n; i++) {
        if (i % 2 == 0) {
            pi += 1.0 / (2 * i + 1);
        } else {
            pi -= 1.0 / (2 * i + 1);
        }
    }

    pi *= 4;
    printf("Aproximación de π: %.6f\n", pi);

    return 0;
}
```