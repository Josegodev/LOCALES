# Attention Is All You Need

## Resumen del artículo original
El artículo "Attention Is All You Need" presentado por Vaswani et al. en 2017 introduce el modelo Transformer, una arquitectura diseñada para tareas de procesamiento de lenguaje natural (NLP) que se basa exclusivamente en mecanismos de atención y evita el uso de convoluciones o recurrentes.

### Resumen del contenido
- **Introducción a la atención**: Explica cómo los modelos de atención permiten que las partes relevantes de la entrada sean ponderadas según su relevancia para generar una salida.
- **Arquitectura Transformer**: Describe la estructura del modelo, incluyendo el codificador y el decodificador, ambos compuestos por múltiples capas de auto-atención y redes neuronales posicionales.
- **Mecanismos clave**:
  - **Auto-atención (Self-Attention)**: Permite que cada token en una secuencia se relacione con todos los demás tokens para capturar dependencias a distancia.
  - **Multi-head attention**: Utiliza múltiples "cabezas" de atención paralelas para capturar diferentes aspectos de las relaciones entre tokens.
  - **Posición relativa (Relative Position Representations)**: Introduce representaciones de posición relativa para capturar el orden de los tokens más efectivamente.
- **Implementación práctica**: Detalla cómo se entrenan y optimizan estos modelos, incluyendo técnicas como la normalización por lotes y el uso de gradient descent.
- **Resultados**: Muestra que los Transformers superan a las arquitecturas anteriores en varias tareas de NLP sin necesidad de procesamiento secuencial.

### Contribuciones significativas
1. **Eliminación de componentes secuenciales**: Los Transformers eliminan la necesidad de procesar datos secuencialmente, lo que permite un entrenamiento más paralelo y eficiente.
2. **Mejora en el manejo de dependencias a distancia**: La auto-atención permite capturar relaciones entre elementos distantes en una secuencia de manera efectiva.
3. **Flexibilidad y escalabilidad**: La arquitectura es altamente flexible, permitiendo su adaptación a diversas tareas y escalando bien con grandes cantidades de datos.

### Impacto
El artículo ha tenido un impacto monumental en el