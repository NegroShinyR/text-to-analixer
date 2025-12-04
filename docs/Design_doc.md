# Design Doc – Text to Analixer 📝

## 1. Objetivo del sistema

El propósito del sistema **Text to Analixer** es analizar un texto en español y calcular qué tan relacionado está con el campo de las **Matemáticas**, generando un puntaje del **0% al 100%**.

Se utiliza:

- un vocabulario matemático almacenado en SQLite,
- un algoritmo de clasificación ligero llamado **MatCompat v5**,
- una interfaz web hecha con **Streamlit**.

---

## 2. Arquitectura General

La arquitectura es simple y fácil de explicar:

```
Usuario → Streamlit (buscale.py)
          │
          ├── Carga vocabulario desde SQLite (vocab.db)
          ├── Tokeniza y normaliza texto
          ├── Detecta términos matemáticos
          └── Calcula compatibilidad (MatCompat v5)
```

Componentes:

- **buscale.py** → UI + backend
- **vocab.db** → base de datos SQLite con palabras matemáticas
- **matcompat_score()** → motor del algoritmo
- **Streamlit** → interfaz interactiva
- **Altair** → gráficos opcionales

---

## 3. Modelo de Datos

### Tabla en SQLite: `palabras_clave`

| Campo                 | Tipo   | Descripción                               |
|-----------------------|--------|-------------------------------------------|
| id                    | INT    | Llave primaria                            |
| palabra               | TEXT   | Término matemático base                   |
| porcentaje_identidad  | REAL   | Peso del término (0–100)                  |
| sinonimos             | TEXT   | Lista separada por comas                  |

Ejemplo:

```
derivada | 97.00 | derivadas,derivar
matriz   | 93.00 | matrices
integral | 97.00 | integrales,integrar
```

---

## 4. Flujo de Ejecución

1. Se carga `vocab.db`
2. Se crea un índice `token → (palabra_base, peso)`
3. Usuario pega un texto
4. Se tokeniza:
   - minúsculas
   - sin acentos
   - separación por regex
   - filtro de stopwords
5. Se detectan tokens que aparecen en el vocabulario
6. Se calcula:
   - avg_peso
   - densidad_matematica
   - puntaje MatCompat v5
7. Se muestran resultados en Streamlit

---

## 5. Decisiones de Diseño

- Se eligió **SQLite** porque:
  - no requiere servidor,
  - funciona perfecto en Render,
  - es ideal para una app de solo lectura.

- Se usa normalización de acentos:
  - “derivación”, “derivacion”, “DERIVACIÓN” → `derivacion`

- Se usa un enfoque basado en vocabulario:
  - fácil de explicar en clase,
  - comportamiento estable.

---

## 6. Pruebas

Se probaron tres tipos de textos:

- **Matemáticos puros** → score alto (80–100%)
- **Mixtos** → score medio (40–70%)
- **No matemáticos** → score bajo (0–20%)

---

## 7. Limitaciones

- No detecta contexto semántico profundo
- Puede confundir términos ambiguos (“media crema”)
- El resultado depende totalmente del vocabulario

---

## 8. Trabajo Futuro

- Expandir vocabulario con más ramas matemáticas
- Añadir aprendizaje basado en ejemplos
- Soporte para inglés
- Añadir interfaz para editar vocabulario en la app

