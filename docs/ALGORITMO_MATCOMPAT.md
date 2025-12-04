# Algoritmo MatCompat v5 – Explicación Técnica

## 1. Objetivo

Determinar qué tan matemático es un texto usando:

- coincidencias del vocabulario matemático,
- densidad matemática,
- pesos de cada término.

El resultado final es un puntaje entre **0 y 100**.

---

## 2. Definiciones

Sea un texto tokenizado:

- **tokens** → todas las palabras
- **tokens_significativos** → palabras sin stopwords
- **matched_tokens** → tokens encontrados en el vocabulario
- **avg_peso** → promedio de pesos de términos encontrados
- **densidad_matematica** = `matched_tokens / tokens_significativos`

---

## 3. Fórmula del algoritmo

```
score = 100 * (0.55 * avg_peso + 0.45 * densidad_matematica)
```

**Interpretación:**

- `avg_peso` aporta **55%**
- `densidad_matematica` aporta **45%**

Esto evita que textos mixtos parezcan matemáticos puros.

---

## 4. Ejemplos Numéricos

### Texto matemático puro
- avg_peso ≈ 0.9  
- densidad ≈ 0.7  
- score ≈ 80–95%

### Texto mixto
- avg_peso ≈ 0.9  
- densidad ≈ 0.3–0.5  
- score ≈ 45–70%

### Texto no matemático
- avg_peso ≈ 0.8 (por palabras ambiguas)  
- densidad ≈ 0.02  
- score ≈ 5–15%

---

## 5. Complejidad del Algoritmo

- Recorrido de tokens: **O(N)**
- Búsqueda en vocabulario (diccionario Python): **O(1)** promedio

Total: **O(N)**

---

## 6. Limitaciones

- Depende completamente del vocabulario matemático
- No analiza semántica profunda
- Puede confundir palabras ambiguas (“media”)

---

## 7. Mejoras Futuras

- Pesos dinámicos según textos etiquetados
- Vocabulario ampliado
- Clasificador híbrido con análisis semántico
