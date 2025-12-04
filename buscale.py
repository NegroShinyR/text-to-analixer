#!/usr/bin/env python
import re
import unicodedata
from collections import Counter
from typing import Dict, List, Tuple

import altair as alt
import pandas as pd
import streamlit as st
import sqlite3

st.set_page_config(page_title="Text Analixer", layout="centered", page_icon="📝")
DATA_FILEPATH = "litcovid.export.all.tsv"


# =========================
# Utilidades de texto
# =========================

def strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def normalize_token(s: str) -> str:
    # minúsculas + sin espacios extremos + sin acentos
    return strip_accents(str(s).strip().lower())


def tokenize(text: str) -> List[str]:
    text = strip_accents(text.lower())
    return [t for t in re.split(r"\W+", text) if t]


# Stopwords básicas en español
STOPWORDS_ES = {
    "de", "la", "las", "el", "los", "y", "o", "u", "en", "con", "por", "para",
    "a", "un", "una", "unos", "unas", "al", "del", "que", "se", "su", "sus",
    "es", "son", "como", "pero", "si", "no", "lo", "le", "este", "estos",
    "esta", "estas"
}


def tokens_significativos(toks: List[str]) -> List[str]:
    """Filtra stopwords para quedarnos solo con palabras de contenido."""
    return [t for t in toks if t not in STOPWORDS_ES]


# =========================
# Carga del TSV (lo tuyo)
# =========================
@st.cache_data
def load_data(filepath: str) -> pd.DataFrame:
    """Load data from local TSV (tu dataset existente)"""
    return pd.read_csv(filepath, sep="\t", skiprows=33).fillna("")


def search_dataframe(df: pd.DataFrame, column: str, search_str: str) -> pd.DataFrame:
    """Search a column for a substring and return results as df"""
    return df.loc[df[column].str.contains(search_str, case=False)]


def generate_barplot(results: pd.DataFrame, count_column: str, top_n: int = 10):
    """Barplot simple con Altair"""
    return alt.Chart(results).transform_aggregate(
        count='count()',
        groupby=[f'{count_column}']
    ).transform_window(
        rank='rank(count)',
        sort=[alt.SortField('count', order='descending')]
    ).transform_filter(
        alt.datum.rank < top_n
    ).mark_bar().encode(
        y=alt.Y(f'{count_column}:N', sort='-x'),
        x='count:Q',
        tooltip=[f'{count_column}:N', 'count:Q']
    ).properties(
        width=700,
        height=400
    ).interactive()


# =========================
# Vocabulario desde SQLite
# =========================
@st.cache_data
def load_vocab_from_sqlite(db_path: str = "vocab.db") -> pd.DataFrame:
    """
    Carga el vocabulario desde un archivo SQLite (vocab.db).
    Tabla: palabras_clave (palabra TEXT, porcentaje_identidad REAL, sinonimos TEXT)
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT palabra, porcentaje_identidad, sinonimos FROM palabras_clave;")
    rows = cur.fetchall()
    conn.close()

    # Pasar a DataFrame
    df = pd.DataFrame(rows, columns=["palabra", "porcentaje_identidad", "sinonimos"])
    df["palabra"] = df["palabra"].astype(str).str.strip().str.lower()
    df["peso"] = (df["porcentaje_identidad"].astype(float) / 100.0).clip(0, 1)

    def clean_syn(s: str):
        if s is None:
            return []
        parts = [p.strip().lower() for p in str(s).split(",") if p.strip()]
        return parts

    df["sinonimos"] = df["sinonimos"].apply(clean_syn)
    return df[["palabra", "peso", "sinonimos"]]


def build_vocab_index(vocab_df: pd.DataFrame) -> Dict[str, Tuple[str, float]]:
    """
    Indexa: token_normalizado -> (palabra_base_original, peso)
    Incluye la palabra base y cada sinónimo como clave.
    """
    index: Dict[str, Tuple[str, float]] = {}
    for _, row in vocab_df.iterrows():
        base = row["palabra"]
        w = float(row["peso"])

        base_key = normalize_token(base)
        index[base_key] = (base, w)

        for s in row["sinonimos"]:
            s_key = normalize_token(s)
            if s_key:
                index[s_key] = (base, w)
    return index


# =========================
# Algoritmo MatCompat v5
# =========================
def matcompat_score(text: str, vocab_index: Dict[str, Tuple[str, float]]):
    """
    Calcula la compatibilidad (0-100) con Matemáticas.

    Parámetros clave:
      - avg_peso = relevancia promedio de los términos matemáticos encontrados.
      - densidad_matematica = matched_tokens / tokens_significativos.

    Fórmula:
      score = 100 * (0.55 * avg_peso + 0.45 * densidad_matematica)
    """

    toks = tokenize(text)
    total_tokens = len(toks)

    # Tokens significativos (sin stopwords)
    sig_toks = tokens_significativos(toks)
    total_sig = len(sig_toks)

    counts = Counter()
    pesos = []

    for tk in toks:
        if tk in vocab_index:
            base, w = vocab_index[tk]
            counts[(base, w)] += 1
            pesos.append(w)

    matched_tokens = sum(counts.values())
    distinct_terms = len(counts)

    if matched_tokens == 0:
        return 0.0, {
            "matched_tokens": 0,
            "distinct_terms": 0,
            "total_tokens": total_tokens,
            "tokens_significativos": total_sig,
            "avg_peso": 0.0,
            "densidad_matematica": 0.0,
            "matches": []
        }

    avg_peso = sum(pesos) / len(pesos)

    # Densidad de matemáticas en el texto
    denom = total_sig if total_sig > 0 else total_tokens
    densidad = matched_tokens / denom

    # Fórmula final calibrada
    score = 100 * (0.55 * avg_peso + 0.45 * densidad)

    detalles = sorted(
        [
            {
                "termino": base,
                "conteo": cnt,
                "peso": w,
                "aporte": round(cnt * w, 4)
            }
            for (base, w), cnt in counts.items()
        ],
        key=lambda d: d["aporte"],
        reverse=True
    )

    return round(score, 2), {
        "matched_tokens": matched_tokens,
        "distinct_terms": distinct_terms,
        "total_tokens": total_tokens,
        "tokens_significativos": total_sig,
        "avg_peso": round(avg_peso, 4),
        "densidad_matematica": round(densidad, 4),
        "matches": detalles
    }


# =========================
# App
# =========================
def app():
    st.title("Text to analixer 📝")

    # 1) Cargar vocab de SQLite
    with st.spinner("Cargando vocabulario de Matemáticas…"):
        vocab_df = load_vocab_from_sqlite("vocab.db")
        vocab_idx = build_vocab_index(vocab_df)

    # 2) Cargar tu TSV (si lo necesitas para el resto de la app)
    df = load_data(DATA_FILEPATH)

    # 3) Entrada de texto a evaluar
    with st.form(key='Search'):
        text_query = st.text_area(label='Pega aquí el texto a evaluar', height=160)
        # (opcional) también puedes buscar en tu TSV como ya hacías:
        do_search = st.checkbox("Además, buscar en el dataset por título (demo)", value=False)
        submit_button = st.form_submit_button(label='Analizar')

    if submit_button and text_query.strip():
        # --- Algoritmo de compatibilidad ---
        score, info = matcompat_score(text_query, vocab_idx)

        st.subheader("Compatibilidad con Matemáticas")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Compatibilidad", f"{score:.2f}%")
        with col2:
            st.progress(min(1.0, score / 100.0))

        # Métricas
        st.caption(
            f"Tokens totales: {info['total_tokens']} · "
            f"Tokens significativos: {info['tokens_significativos']} · "
            f"Tokens matemáticos: {info['matched_tokens']} · "
            f"Términos matemáticos distintos: {info['distinct_terms']} · "
            f"Promedio de peso: {info['avg_peso']} · "
            f"Densidad matemática: {info['densidad_matematica']}"
        )

        # Detalle de matches como tabla
        if info["matches"]:
            st.write("**Términos detectados (ordenados por aporte):**")
            st.dataframe(pd.DataFrame(info["matches"]))
        else:
            st.info("No se detectaron términos del vocabulario en el texto.")

        # --- (opcional) búsqueda en tu TSV, como antes ---
        if do_search:
            results = search_dataframe(df, "title_e", text_query)
            st.success(f"Búsqueda en dataset: **{len(results):,}** resultados de {len(df):,}.")
            st.table(results.head(n=10))
            st.altair_chart(generate_barplot(results, "journal", 10))

    elif submit_button:
        st.warning("Pega un texto para analizar.")


if __name__ == '__main__':
    app()
