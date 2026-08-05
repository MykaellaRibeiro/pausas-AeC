from datetime import date, datetime, timedelta
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


APP_DIR = Path(__file__).parent
DEFAULT_CSV = APP_DIR / "data" / "colaboradores.csv"
DB_PATH = APP_DIR / "data" / "faltas.db"
TARGET_SUPERVISORS = {
    "DANYELLA LAYSE SILVA TAVARES": "Danyella",
    "OLÍVIA LETÍCIA GOMES VIANA": "Olívia",
}
SUPERVISOR_ORDER = {
    "DANYELLA LAYSE SILVA TAVARES": 1,
    "OLÍVIA LETÍCIA GOMES VIANA": 2,
}
# A escala de cada colaborador (supervisora e horário de entrada) vem
# diretamente das colunas SUPERVISOR e HORÁRIO do arquivo data/colaboradores.csv.
# Para adicionar, remover ou mudar um colaborador, basta editar a planilha
# (ou enviar um CSV atualizado pelo app) — não é necessário mexer no código.
WORKDAY_MINUTES = 6 * 60 + 20
PAUSE_1_OFFSET = 90
MEAL_OFFSET = 195
PAUSE_2_OFFSET = 315


st.set_page_config(
    page_title="Controle de Pausas",
    page_icon="⏱️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@500;600;700&display=swap');

    :root {
        /* Paleta "quadro de turno": tinta indigo quase-preta sobre ardósia clara,
           com latão (o carimbo do relógio de ponto) como cor de assinatura. */
        --bg: #e9edf4;
        --surface: #ffffff;
        --surface-soft: #f3f5f9;
        --ink: #10182b;
        --muted: #5c6780;
        --line: #d7dce8;
        --brass: #a8710a;
        --brass-soft: #fbf1de;
        --signal: #22409b;
        --signal-soft: #eaeefb;
        --ok: #15754f;
        --ok-soft: #e7f6ee;
        --danger: #b3261e;
        --danger-soft: #fbeae9;
        --font-sans: 'IBM Plex Sans', 'Segoe UI', sans-serif;
        --font-mono: 'IBM Plex Mono', 'SFMono-Regular', Consolas, monospace;
    }

    .stApp {
        background:
            linear-gradient(180deg, rgba(16, 24, 43, 0.04), rgba(16, 24, 43, 0) 220px),
            var(--bg);
    }

    .block-container {
        padding-top: 1.1rem;
        padding-bottom: 2.5rem;
        max-width: 1120px;
    }

    html, body, [class*="css"] {
        font-family: var(--font-sans);
    }

    h1, h2, h3 {
        color: var(--ink);
        letter-spacing: -0.01em;
        font-family: var(--font-sans);
    }

    h2, h3 {
        font-weight: 700;
    }

    p, label, span {
        color: var(--ink);
    }

    div[data-testid="stCaptionContainer"] p {
        color: var(--muted);
        font-size: 0.94rem;
    }

    /* ---------- Cabeçalho / quadro de turno ---------- */
    .app-hero {
        position: relative;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1.5rem;
        background: var(--ink);
        border-radius: 10px;
        padding: 1.35rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 16px 32px rgba(16, 24, 43, 0.18);
        overflow: hidden;
    }

    .app-hero::before {
        content: "";
        position: absolute;
        inset: 0;
        background:
            repeating-linear-gradient(90deg, rgba(255,255,255,0.035) 0 1px, transparent 1px 34px);
        pointer-events: none;
    }

    .app-hero .hero-eyebrow {
        font-family: var(--font-mono);
        text-transform: uppercase;
        letter-spacing: 0.16em;
        font-size: 0.72rem;
        color: var(--brass);
        font-weight: 600;
        margin: 0 0 0.3rem 0;
    }

    .app-hero h1 {
        color: #ffffff;
        margin: 0;
        font-size: 1.85rem;
        font-weight: 700;
    }

    .app-hero p {
        color: #b9c1d6;
        margin: 0.4rem 0 0 0;
        max-width: 620px;
        font-size: 0.94rem;
        line-height: 1.5;
    }

    .hero-stamp {
        flex-shrink: 0;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.16);
        border-radius: 8px;
        padding: 0.6rem 1.1rem;
        background: rgba(255,255,255,0.04);
    }

    .hero-stamp .stamp-label {
        font-family: var(--font-mono);
        font-size: 0.64rem;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        color: #8b96b3;
        margin-bottom: 0.2rem;
    }

    .hero-stamp .stamp-value {
        font-family: var(--font-mono);
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--brass);
        letter-spacing: 0.02em;
    }

    @media (max-width: 700px) {
        .app-hero {
            flex-direction: column;
            align-items: flex-start;
        }
    }

    /* ---------- Chips de contagem ---------- */
    .supervisor-chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: -0.3rem 0 1.1rem 0;
    }

    .supervisor-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 6px;
        padding: 0.4rem 0.8rem;
        font-size: 0.83rem;
        font-weight: 600;
        color: var(--muted);
    }

    .supervisor-chip b {
        font-family: var(--font-mono);
        color: var(--ink);
        font-weight: 700;
    }

    .supervisor-chip.total {
        background: var(--ink);
        border-color: var(--ink);
        color: #b9c1d6;
    }

    .supervisor-chip.total b {
        color: var(--brass);
    }

    /* ---------- Painéis / expanders / inputs ---------- */
    div[data-testid="stExpander"] {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 8px;
        box-shadow: 0 8px 20px rgba(16, 24, 43, 0.05);
    }

    div[data-testid="stExpander"] summary {
        font-weight: 650;
    }

    div[data-testid="stSelectbox"] label,
    div[data-testid="stMultiSelect"] label,
    div[data-testid="stTextInput"] label,
    div[data-testid="stFileUploader"] label,
    div[data-testid="stDateInput"] label {
        color: var(--ink);
        font-weight: 650;
        font-size: 0.88rem;
    }

    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    div[data-baseweb="base-input"] {
        background: var(--surface);
        border-color: var(--line) !important;
        border-radius: 6px;
        min-height: 46px;
    }

    div[data-baseweb="tag"] {
        background: var(--signal) !important;
        border-radius: 4px !important;
    }

    /* ---------- KPIs ---------- */
    .kpi-card {
        background: var(--surface);
        border: 1px solid var(--line);
        border-left: 3px solid var(--signal);
        border-radius: 8px;
        padding: 0.85rem 1rem;
        min-height: 92px;
    }

    .kpi-card .kpi-label {
        font-family: var(--font-mono);
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--muted);
        font-size: 0.72rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    .kpi-card .kpi-value {
        color: var(--ink);
        font-family: var(--font-mono);
        font-size: 1.85rem;
        line-height: 1;
        font-weight: 700;
    }

    .kpi-card.time {
        border-left-color: var(--brass);
    }

    .kpi-card.workday {
        border-left-color: var(--ok);
    }

    .kpi-card.absences {
        border-left-color: var(--danger);
    }

    /* ---------- Tabela ---------- */
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 8px;
        overflow: hidden;
    }

    div[data-testid="stTabs"] button {
        color: var(--muted);
        font-weight: 650;
    }

    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--ink);
        border-bottom-color: var(--brass) !important;
    }

    /* ---------- Botões ---------- */
    div[data-testid="stDownloadButton"] button,
    div[data-testid="stFormSubmitButton"] button,
    div.stButton button[kind="primary"] {
        border-radius: 6px;
        border: 1px solid var(--ink);
        background: var(--ink);
        color: white;
        font-weight: 650;
        min-height: 44px;
    }

    div[data-testid="stDownloadButton"] button:hover,
    div.stButton button[kind="primary"]:hover {
        border-color: var(--brass);
        background: #1a2340;
        color: white;
    }

    /* ---------- Cartão de escala + linha do tempo ---------- */
    .schedule-card {
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.85rem;
        background: var(--surface);
        position: relative;
    }

    .schedule-card::before {
        content: "";
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 3px;
        border-radius: 8px 0 0 8px;
        background: var(--signal);
    }

    .schedule-card.absent::before {
        background: var(--danger);
    }

    .schedule-card.absent {
        background: var(--danger-soft);
    }

    .card-top {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 0.75rem;
    }

    .schedule-card strong {
        display: block;
        color: var(--ink);
        font-size: 1.02rem;
        font-weight: 700;
        line-height: 1.3;
    }

    .schedule-card .card-meta {
        color: var(--muted);
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 0.15rem;
    }

    .card-meta .clock {
        font-family: var(--font-mono);
        color: var(--ink);
        font-weight: 600;
    }

    .absence-badge {
        flex-shrink: 0;
        display: inline-block;
        padding: 0.28rem 0.55rem;
        border-radius: 5px;
        background: var(--danger);
        color: white;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        white-space: nowrap;
    }

    .absence-summary {
        border: 1px solid #f3c6c3;
        border-left: 3px solid var(--danger);
        border-radius: 8px;
        background: var(--danger-soft);
        color: #7a201a;
        font-weight: 650;
        padding: 0.8rem 1rem;
        margin: 0.85rem 0 1rem 0;
        font-size: 0.92rem;
    }

    /* timeline: barra proporcional do turno com os 3 intervalos de pausa */
    .shift-timeline {
        margin-top: 0.75rem;
    }

    .timeline-bar {
        display: flex;
        width: 100%;
        height: 10px;
        border-radius: 5px;
        overflow: hidden;
        border: 1px solid var(--line);
        background: var(--surface-soft);
    }

    .timeline-bar span {
        height: 100%;
    }

    .timeline-bar .seg-work {
        background: var(--signal-soft);
    }

    .timeline-bar .seg-p1,
    .timeline-bar .seg-p2 {
        background: var(--brass);
    }

    .timeline-bar .seg-lunch {
        background: var(--ok);
    }

    .timeline-labels {
        display: flex;
        justify-content: space-between;
        margin-top: 0.3rem;
        font-family: var(--font-mono);
        font-size: 0.72rem;
        color: var(--muted);
        font-weight: 600;
    }

    .pause-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.45rem;
        margin-top: 0.75rem;
    }

    .pause-pill {
        background: var(--surface-soft);
        border: 1px solid var(--line);
        border-left: 3px solid var(--signal);
        border-radius: 6px;
        padding: 0.5rem 0.65rem;
        font-size: 0.82rem;
        color: var(--ink);
        font-weight: 600;
    }

    .pause-pill .clock {
        font-family: var(--font-mono);
        font-weight: 650;
    }

    .pause-pill.p1,
    .pause-pill.p2 {
        background: var(--brass-soft);
        border-left-color: var(--brass);
    }

    .pause-pill.p20 {
        background: var(--ok-soft);
        border-left-color: var(--ok);
    }

    .pause-pill.supervisor {
        background: var(--signal-soft);
        border-left-color: var(--signal);
    }

    .pause-pill.done {
        background: var(--ok-soft);
        border-color: #b7e0c9;
        border-left-color: var(--ok);
        color: #0e4b32;
    }

    .pause-checks {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.55rem;
        margin: -0.25rem 0 0.9rem 0.1rem;
    }

    .pause-checks label {
        font-weight: 650;
        font-size: 0.85rem;
    }

    /* ---------- Histórico ---------- */
    .history-item {
        border: 1px solid var(--line);
        border-left: 3px solid var(--danger);
        border-radius: 8px;
        background: var(--surface);
        padding: 0.7rem 0.9rem;
        min-height: 70px;
    }

    .history-person {
        color: var(--ink);
        font-weight: 700;
        line-height: 1.25;
        margin-bottom: 0.3rem;
    }

    .history-meta {
        color: var(--muted);
        font-size: 0.83rem;
        font-weight: 600;
        line-height: 1.5;
    }

    .history-meta .clock {
        font-family: var(--font-mono);
    }

    @media (max-width: 700px) {
        .block-container {
            padding-left: 0.7rem;
            padding-right: 0.7rem;
        }

        .app-hero h1 {
            font-size: 1.4rem;
        }

        .pause-grid {
            grid-template-columns: 1fr;
        }

        .pause-checks {
            grid-template-columns: 1fr;
        }

        .kpi-card {
            padding: 0.75rem;
            min-height: 82px;
        }

        .kpi-card .kpi-value {
            font-size: 1.5rem;
        }

        .history-item {
            min-height: auto;
        }

        div[data-baseweb="select"] > div {
            min-height: 44px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def read_csv_with_fallback(source) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            if hasattr(source, "seek"):
                source.seek(0)
            return pd.read_csv(source, encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Não foi possível ler o arquivo CSV com uma codificação conhecida.")


@st.cache_data(show_spinner=False)
def load_default_data(csv_mtime: float) -> pd.DataFrame:
    _ = csv_mtime
    return read_csv_with_fallback(DEFAULT_CSV)


def normalize_data(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized.columns = [column.strip().upper() for column in normalized.columns]

    required = {"NOME", "SUPERVISOR", "STATUS", "HORÁRIO"}
    missing = sorted(required - set(normalized.columns))
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"O arquivo precisa ter estas colunas: {missing_text}.")

    for column in ("NOME", "SUPERVISOR", "STATUS", "HORÁRIO"):
        normalized[column] = normalized[column].fillna("").astype(str).str.strip()

    normalized["NOME"] = normalized["NOME"].str.upper()
    normalized["SUPERVISOR"] = normalized["SUPERVISOR"].str.upper()
    normalized["STATUS"] = normalized["STATUS"].str.upper()
    normalized["HORÁRIO"] = normalized["HORÁRIO"].str.slice(0, 5)

    total_rows = len(normalized)
    normalized = normalized[normalized["STATUS"].eq("ATIVO")].copy()
    normalized = normalized[normalized["NOME"].ne("")].copy()
    normalized = normalized[normalized["SUPERVISOR"].isin(TARGET_SUPERVISORS)].copy()

    normalized["HORÁRIO_ORDENACAO"] = pd.to_datetime(
        normalized["HORÁRIO"], format="%H:%M", errors="coerce"
    )
    ignored_rows = total_rows - len(normalized.dropna(subset=["HORÁRIO_ORDENACAO"]))
    normalized = normalized.dropna(subset=["HORÁRIO_ORDENACAO"])
    normalized = normalized.drop_duplicates(subset=["NOME", "SUPERVISOR"], keep="last")
    normalized = normalized.sort_values(["SUPERVISOR", "HORÁRIO_ORDENACAO", "NOME"])

    normalized.attrs["ignored_rows"] = ignored_rows
    normalized.attrs["total_rows"] = total_rows
    return normalized


def parse_clock(value: str) -> datetime:
    return datetime.strptime(value.strip(), "%H:%M")


def format_clock(moment: datetime) -> str:
    return moment.strftime("%H:%M")


def interval(start: datetime, duration_minutes: int) -> str:
    end = start + timedelta(minutes=duration_minutes)
    return f"{format_clock(start)} - {format_clock(end)}"


def extract_interval_start(value: str) -> str:
    return str(value).split("-")[0].strip()


def safe_parse_clock(value: str, field_name: str, collaborator: str) -> datetime:
    try:
        return parse_clock(str(value))
    except ValueError:
        raise ValueError(
            f"Horário inválido em {field_name} de {collaborator}. Use o formato HH:MM."
        )


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS faltas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                colaborador TEXT NOT NULL,
                supervisor TEXT NOT NULL,
                registrado_em TEXT NOT NULL,
                UNIQUE(data, colaborador)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ajustes_horarios (
                data TEXT NOT NULL,
                colaborador TEXT NOT NULL,
                supervisor TEXT NOT NULL,
                entrada TEXT NOT NULL,
                pausa_1_inicio TEXT NOT NULL,
                pausa_20_inicio TEXT NOT NULL,
                pausa_2_inicio TEXT NOT NULL,
                modo TEXT NOT NULL,
                atualizado_em TEXT NOT NULL,
                PRIMARY KEY (data, colaborador)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS status_pausas (
                data TEXT NOT NULL,
                colaborador TEXT NOT NULL,
                pausa TEXT NOT NULL,
                feito INTEGER NOT NULL,
                atualizado_em TEXT NOT NULL,
                PRIMARY KEY (data, colaborador, pausa)
            )
            """
        )


def load_absences(absence_date: date) -> list[str]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT colaborador FROM faltas WHERE data = ? ORDER BY colaborador",
            (absence_date.isoformat(),),
        ).fetchall()
    return [row[0] for row in rows]


def save_absences(absence_date: date, selected_rows: pd.DataFrame) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM faltas WHERE data = ?", (absence_date.isoformat(),))
        conn.executemany(
            """
            INSERT INTO faltas (data, colaborador, supervisor, registrado_em)
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    absence_date.isoformat(),
                    row["Colaborador"],
                    row["Supervisor"],
                    datetime.now().isoformat(timespec="seconds"),
                )
                for _, row in selected_rows.iterrows()
            ],
        )


def delete_absences(records: list[tuple[str, str]]) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.executemany(
            "DELETE FROM faltas WHERE data = ? AND colaborador = ?",
            records,
        )


def load_pause_status(status_date: date) -> set[tuple[str, str]]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            """
            SELECT colaborador, pausa
            FROM status_pausas
            WHERE data = ? AND feito = 1
            """,
            (status_date.isoformat(),),
        ).fetchall()
    return {(row[0], row[1]) for row in rows}


def save_pause_status(
    status_date: date,
    collaborator: str,
    pause: str,
    done: bool,
) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO status_pausas (
                data, colaborador, pausa, feito, atualizado_em
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                status_date.isoformat(),
                collaborator,
                pause,
                int(done),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )


def load_time_adjustments(adjustment_date: date) -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        adjustments = pd.read_sql_query(
            """
            SELECT colaborador, supervisor, entrada, pausa_1_inicio, pausa_20_inicio,
                   pausa_2_inicio, modo
            FROM ajustes_horarios
            WHERE data = ?
            ORDER BY colaborador
            """,
            conn,
            params=(adjustment_date.isoformat(),),
        )
    return adjustments


def save_time_adjustments(
    adjustment_date: date,
    edited_rows: pd.DataFrame,
    mode: str,
) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.executemany(
            """
            INSERT OR REPLACE INTO ajustes_horarios (
                data, colaborador, supervisor, entrada, pausa_1_inicio,
                pausa_20_inicio, pausa_2_inicio, modo, atualizado_em
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    adjustment_date.isoformat(),
                    row["Colaborador"],
                    row["Supervisor"],
                    row["Entrada"],
                    row["Pausa 1 início"],
                    row["Pausa 20 início"],
                    row["Pausa 2 início"],
                    mode,
                    datetime.now().isoformat(timespec="seconds"),
                )
                for _, row in edited_rows.iterrows()
            ],
        )


def apply_time_adjustments(editable: pd.DataFrame, adjustment_date: date) -> pd.DataFrame:
    adjustments = load_time_adjustments(adjustment_date)
    if adjustments.empty or editable.empty:
        return editable

    adjusted = editable.copy()
    adjustment_map = adjustments.set_index("colaborador").to_dict("index")
    for index, row in adjusted.iterrows():
        saved = adjustment_map.get(row["Colaborador"])
        if not saved:
            continue

        adjusted.at[index, "Entrada"] = saved["entrada"]
        adjusted.at[index, "Pausa 1 início"] = saved["pausa_1_inicio"]
        adjusted.at[index, "Pausa 20 início"] = saved["pausa_20_inicio"]
        adjusted.at[index, "Pausa 2 início"] = saved["pausa_2_inicio"]

    return adjusted


def load_absence_history() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        history = pd.read_sql_query(
            """
            SELECT data, colaborador, supervisor, registrado_em
            FROM faltas
            ORDER BY data DESC, colaborador
            """,
            conn,
        )

    if history.empty:
        return history

    history["Data ISO"] = history["data"]
    history["Data"] = pd.to_datetime(history["data"]).dt.strftime("%d/%m/%Y")
    history["registrado_em"] = pd.to_datetime(history["registrado_em"]).dt.strftime(
        "%d/%m/%Y %H:%M"
    )
    history = history.rename(
        columns={
            "colaborador": "Colaborador",
            "supervisor": "Supervisor",
            "registrado_em": "Registrado em",
        }
    )
    return history[["Data ISO", "Data", "Colaborador", "Supervisor", "Registrado em"]]


def build_schedule(
    df: pd.DataFrame,
    pause_1_offset: int,
    meal_offset: int,
    pause_2_offset: int,
) -> pd.DataFrame:
    rows = []

    for _, row in df.iterrows():
        start = parse_clock(row["HORÁRIO"])
        pause_1_start = start + timedelta(minutes=pause_1_offset)
        meal_start = start + timedelta(minutes=meal_offset)
        pause_2_start = start + timedelta(minutes=pause_2_offset)
        end = start + timedelta(minutes=WORKDAY_MINUTES)

        rows.append(
            {
                "Colaborador": row["NOME"].title(),
                "Supervisor": TARGET_SUPERVISORS.get(row["SUPERVISOR"], row["SUPERVISOR"].title()),
                "Entrada": format_clock(start),
                "Pausa 1 (10 min)": interval(pause_1_start, 10),
                "Pausa 20 min": interval(meal_start, 20),
                "Pausa 2 (10 min)": interval(pause_2_start, 10),
                "Saída": format_clock(end),
            }
        )

    schedule = pd.DataFrame(rows)
    if schedule.empty:
        return schedule

    schedule["__entrada_ordem"] = pd.to_datetime(
        schedule["Entrada"], format="%H:%M", errors="coerce"
    )
    schedule = schedule.sort_values(["__entrada_ordem", "Colaborador"]).drop(
        columns=["__entrada_ordem"]
    )
    return schedule.reset_index(drop=True)


def prepare_editable_schedule(schedule: pd.DataFrame) -> pd.DataFrame:
    if schedule.empty:
        return schedule

    editable = schedule[
        [
            "Colaborador",
            "Supervisor",
            "Entrada",
            "Pausa 1 (10 min)",
            "Pausa 20 min",
            "Pausa 2 (10 min)",
        ]
    ].copy()
    editable["Pausa 1 início"] = editable["Pausa 1 (10 min)"].apply(extract_interval_start)
    editable["Pausa 20 início"] = editable["Pausa 20 min"].apply(extract_interval_start)
    editable["Pausa 2 início"] = editable["Pausa 2 (10 min)"].apply(extract_interval_start)
    return editable[
        [
            "Colaborador",
            "Supervisor",
            "Entrada",
            "Pausa 1 início",
            "Pausa 20 início",
            "Pausa 2 início",
        ]
    ]


def calculate_adjusted_schedule(
    editable: pd.DataFrame,
    auto_pauses: bool,
) -> pd.DataFrame:
    rows = []

    for _, row in editable.iterrows():
        collaborator = row["Colaborador"]
        start = safe_parse_clock(row["Entrada"], "entrada", collaborator)

        if auto_pauses:
            pause_1_start = start + timedelta(minutes=PAUSE_1_OFFSET)
            meal_start = start + timedelta(minutes=MEAL_OFFSET)
            pause_2_start = start + timedelta(minutes=PAUSE_2_OFFSET)
        else:
            pause_1_start = safe_parse_clock(row["Pausa 1 início"], "pausa 1", collaborator)
            meal_start = safe_parse_clock(row["Pausa 20 início"], "pausa de 20", collaborator)
            pause_2_start = safe_parse_clock(row["Pausa 2 início"], "pausa 2", collaborator)

        end = start + timedelta(minutes=WORKDAY_MINUTES)
        rows.append(
            {
                "Colaborador": collaborator,
                "Supervisor": row["Supervisor"],
                "Entrada": format_clock(start),
                "Pausa 1 (10 min)": interval(pause_1_start, 10),
                "Pausa 20 min": interval(meal_start, 20),
                "Pausa 2 (10 min)": interval(pause_2_start, 10),
                "Saída": format_clock(end),
            }
        )

    adjusted = pd.DataFrame(rows)
    if adjusted.empty:
        return adjusted

    adjusted["__entrada_ordem"] = pd.to_datetime(
        adjusted["Entrada"], format="%H:%M", errors="coerce"
    )
    adjusted = adjusted.sort_values(["__entrada_ordem", "Colaborador"]).drop(
        columns=["__entrada_ordem"]
    )
    return adjusted.reset_index(drop=True)


def build_shift_timeline(row: pd.Series) -> str:
    """Barra proporcional do turno com os 3 intervalos de pausa marcados.

    É construída a partir dos horários reais da linha (funciona tanto para a
    escala automática quanto para horários ajustados manualmente).
    """
    try:
        entrada = parse_clock(row["Entrada"])
        saida = parse_clock(row["Saída"])
        p1_start = parse_clock(extract_interval_start(row["Pausa 1 (10 min)"]))
        lunch_start = parse_clock(extract_interval_start(row["Pausa 20 min"]))
        p2_start = parse_clock(extract_interval_start(row["Pausa 2 (10 min)"]))
    except ValueError:
        return ""

    total = (saida - entrada).total_seconds() / 60
    if total <= 0:
        return ""

    segments = [
        ("seg-work", max((p1_start - entrada).total_seconds() / 60, 0)),
        ("seg-p1", 10),
        ("seg-work", max((lunch_start - (p1_start + timedelta(minutes=10))).total_seconds() / 60, 0)),
        ("seg-lunch", 20),
        ("seg-work", max((p2_start - (lunch_start + timedelta(minutes=20))).total_seconds() / 60, 0)),
        ("seg-p2", 10),
        ("seg-work", max((saida - (p2_start + timedelta(minutes=10))).total_seconds() / 60, 0)),
    ]

    bar = "".join(
        f'<span class="{css_class}" style="width:{(minutes / total) * 100:.2f}%"></span>'
        for css_class, minutes in segments
        if minutes > 0
    )

    return f"""<div class="shift-timeline">
<div class="timeline-bar">{bar}</div>
<div class="timeline-labels"><span>{row["Entrada"]}</span><span>{row["Saída"]}</span></div>
</div>"""


def render_mobile_cards(
    schedule: pd.DataFrame,
    absent_names: set[str],
    pause_status: set[tuple[str, str]],
    status_date: date,
) -> None:
    for _, row in schedule.iterrows():
        collaborator = row["Colaborador"]
        is_absent = row["Colaborador"] in absent_names
        absent_class = " absent" if is_absent else ""
        absent_badge = '<div class="absence-badge">Faltou</div>' if is_absent else ""
        pause_1_done = (collaborator, "pausa_1") in pause_status
        pause_20_done = (collaborator, "pausa_20") in pause_status
        pause_2_done = (collaborator, "pausa_2") in pause_status
        pause_1_class = " done" if pause_1_done else ""
        pause_20_class = " done" if pause_20_done else ""
        pause_2_class = " done" if pause_2_done else ""
        timeline_html = build_shift_timeline(row)
        st.markdown(
            f"""<div class="schedule-card{absent_class}">
<div class="card-top">
<div>
<strong>{row["Colaborador"]}</strong>
<div class="card-meta">Entrada <span class="clock">{row["Entrada"]}</span> · Saída <span class="clock">{row["Saída"]}</span></div>
</div>
{absent_badge}
</div>
{timeline_html}
<div class="pause-grid">
<div class="pause-pill p1{pause_1_class}">Pausa 1 <span class="clock">{row["Pausa 1 (10 min)"]}</span></div>
<div class="pause-pill p20{pause_20_class}">Almoço <span class="clock">{row["Pausa 20 min"]}</span></div>
<div class="pause-pill p2{pause_2_class}">Pausa 2 <span class="clock">{row["Pausa 2 (10 min)"]}</span></div>
<div class="pause-pill supervisor">Supervisora {row["Supervisor"]}</div>
</div>
</div>""",
            unsafe_allow_html=True,
        )
        check_cols = st.columns(3)
        pause_controls = [
            ("pausa_1", "Pausa 1 OK", pause_1_done),
            ("pausa_20", "Pausa 20 OK", pause_20_done),
            ("pausa_2", "Pausa 2 OK", pause_2_done),
        ]
        for col, (pause_key, label, current_value) in zip(check_cols, pause_controls):
            with col:
                new_value = st.checkbox(
                    label,
                    value=current_value,
                    key=f"pause_status_{status_date.isoformat()}_{collaborator}_{pause_key}",
                )
                if new_value != current_value:
                    save_pause_status(status_date, collaborator, pause_key, new_value)
                    st.rerun()


def style_schedule_table(
    df: pd.DataFrame,
    absent_names: set[str],
    pause_status: set[tuple[str, str]],
):
    def mark_absent_rows(row: pd.Series) -> list[str]:
        if row["Colaborador"] in absent_names:
            return [
                "background-color: #fbeae9; color: #7a201a; font-weight: 700;"
                for _ in row
            ]
        return ["" for _ in row]

    def mark_done_pauses(row: pd.Series) -> list[str]:
        styles = ["" for _ in row]
        column_names = list(row.index)
        pause_columns = {
            "Pausa 1 (10 min)": "pausa_1",
            "Pausa 20 min": "pausa_20",
            "Pausa 2 (10 min)": "pausa_2",
        }
        for column_name, pause_key in pause_columns.items():
            if (row["Colaborador"], pause_key) in pause_status and column_name in column_names:
                styles[column_names.index(column_name)] = (
                    "background-color: #e7f6ee; color: #0e4b32; font-weight: 800;"
                )
        return styles

    clock_columns = ["Entrada", "Pausa 1 (10 min)", "Pausa 20 min", "Pausa 2 (10 min)", "Saída"]

    return (
        df.style.set_table_styles(
            [
                {
                    "selector": "thead th",
                    "props": [
                        ("background-color", "#10182b"),
                        ("color", "#ffffff"),
                        ("font-weight", "700"),
                        ("font-family", "'IBM Plex Sans', sans-serif"),
                        ("text-transform", "uppercase"),
                        ("letter-spacing", "0.04em"),
                        ("font-size", "0.78rem"),
                        ("border-color", "#10182b"),
                    ],
                },
                {
                    "selector": "tbody td",
                    "props": [
                        ("border-color", "#d7dce8"),
                        ("font-family", "'IBM Plex Sans', sans-serif"),
                    ],
                },
                {
                    "selector": "tbody tr:hover td",
                    "props": [("background-color", "#f3f5f9")],
                },
            ]
        )
        .set_properties(
            subset=[c for c in clock_columns if c in df.columns],
            **{"font-family": "'IBM Plex Mono', monospace", "font-weight": "600"},
        )
        .set_properties(
            subset=["Pausa 1 (10 min)"],
            **{"background-color": "#fbf1de"},
        )
        .set_properties(
            subset=["Pausa 20 min"],
            **{"background-color": "#e7f6ee"},
        )
        .set_properties(
            subset=["Pausa 2 (10 min)"],
            **{"background-color": "#fbf1de"},
        )
        .apply(mark_absent_rows, axis=1)
        .apply(mark_done_pauses, axis=1)
    )


def schedule_to_excel_bytes(schedule: pd.DataFrame) -> bytes:
    from io import BytesIO

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        schedule.to_excel(writer, index=False, sheet_name="Escala")
        worksheet = writer.sheets["Escala"]
        for column_cells in worksheet.columns:
            max_length = max(len(str(cell.value)) for cell in column_cells if cell.value is not None)
            worksheet.column_dimensions[column_cells[0].column_letter].width = max_length + 4
    return buffer.getvalue()


def render_kpi(label: str, value: str | int, variant: str = "") -> None:
    st.markdown(
        f"""
        <div class="kpi-card {variant}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_history_rows(df: pd.DataFrame, key_prefix: str) -> None:
    if df.empty:
        return

    for index, row in df.reset_index(drop=True).iterrows():
        info_col, action_col = st.columns([0.92, 0.08], vertical_alignment="center")
        with info_col:
            st.markdown(
                f"""<div class="history-item">
<div class="history-person">{row["Colaborador"]}</div>
<div class="history-meta">{row["Data"]} · {row["Supervisor"]} · registrado em {row["Registrado em"]}</div>
</div>""",
                unsafe_allow_html=True,
            )
        with action_col:
            if st.button(
                "",
                key=f"{key_prefix}_delete_{index}_{row['Data ISO']}_{row['Colaborador']}",
                help=f"Apagar falta de {row['Colaborador']} em {row['Data']}",
                icon=":material/delete:",
                use_container_width=True,
            ):
                delete_absences([(row["Data ISO"], row["Colaborador"])])
                st.success("Falta apagada com sucesso.")
                st.rerun()


st.markdown(
    f"""
    <section class="app-hero">
        <div>
            <p class="hero-eyebrow">Quadro de turno · Operação</p>
            <h1>Controle de Pausas</h1>
            <p>Escala por supervisora, controle de faltas por data e histórico para acompanhar a operação.</p>
        </div>
        <div class="hero-stamp">
            <div class="stamp-label">Hoje</div>
            <div class="stamp-value">{datetime.now().strftime('%d/%m/%Y')}</div>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

with st.expander("Atualizar base de colaboradores", expanded=False):
    uploaded_file = st.file_uploader(
        "Enviar CSV atualizado",
        type=["csv"],
        help="Use um arquivo com as colunas NOME, SUPERVISOR, STATUS e HORÁRIO.",
    )

try:
    if uploaded_file is not None:
        raw_data = read_csv_with_fallback(uploaded_file)
    elif DEFAULT_CSV.exists():
        raw_data = load_default_data(DEFAULT_CSV.stat().st_mtime)
    else:
        st.info("Envie um CSV para começar.")
        st.stop()

    data = normalize_data(raw_data)
except Exception as error:
    st.error(str(error))
    st.stop()

init_db()

ignored_rows = data.attrs.get("ignored_rows", 0)
if ignored_rows:
    st.warning(
        f"{ignored_rows} linha(s) da planilha foram ignoradas por falta de SUPERVISOR "
        "válido, HORÁRIO em formato HH:MM ou STATUS diferente de ATIVO."
    )

supervisor_options = sorted(
    data["SUPERVISOR"].unique(),
    key=lambda value: SUPERVISOR_ORDER.get(value, 99),
)
supervisor_labels = [TARGET_SUPERVISORS.get(value, value.title()) for value in supervisor_options]
label_to_supervisor = dict(zip(supervisor_labels, supervisor_options))

supervisor_counts = data["SUPERVISOR"].value_counts()
chips_html = "".join(
    f'<span class="supervisor-chip">{TARGET_SUPERVISORS.get(sup, sup.title())} '
    f'<b>{supervisor_counts.get(sup, 0)}</b></span>'
    for sup in supervisor_options
)
st.markdown(
    f'<div class="supervisor-chip-row">{chips_html}'
    f'<span class="supervisor-chip total">Total <b>{len(data)}</b></span></div>',
    unsafe_allow_html=True,
)

filter_col_1, filter_col_2, filter_col_3 = st.columns([1.1, 0.8, 1.1])
selected_labels = filter_col_1.multiselect(
    "Supervisora",
    supervisor_labels,
    default=supervisor_labels,
    help="Marque uma ou mais opções para visualizar.",
)
selected_supervisors = [label_to_supervisor[label] for label in selected_labels]

if not selected_supervisors:
    st.info("Selecione pelo menos uma supervisora para visualizar a escala.")
    st.stop()

supervisor_data = data[data["SUPERVISOR"].isin(selected_supervisors)].copy()
time_options = ["Todos"] + sorted(supervisor_data["HORÁRIO"].unique(), key=lambda value: parse_clock(value))
selected_time = filter_col_2.selectbox("Horário de entrada", time_options)

if selected_time != "Todos":
    supervisor_data = supervisor_data[supervisor_data["HORÁRIO"].eq(selected_time)]

search_query = filter_col_3.text_input(
    "Buscar colaborador",
    placeholder="Digite um nome...",
    help="Filtra a escala pelo nome do colaborador.",
)
if search_query.strip():
    supervisor_data = supervisor_data[
        supervisor_data["NOME"].str.contains(search_query.strip(), case=False, na=False)
    ]

date_col, absence_col = st.columns([0.85, 1.6])
selected_date = date_col.date_input(
    "Data da escala",
    value=date.today(),
    format="DD/MM/YYYY",
    key="schedule_date",
)
formatted_date = selected_date.strftime("%d/%m/%Y")

schedule = build_schedule(
    supervisor_data,
    PAUSE_1_OFFSET,
    MEAL_OFFSET,
    PAUSE_2_OFFSET,
)

with st.expander("Ajustar horários do dia", expanded=False):
    if schedule.empty:
        st.info("Nenhum colaborador disponível para ajuste nos filtros atuais.")
    else:
        adjustment_mode = st.radio(
            "Como calcular as pausas?",
            ["Automático pela entrada", "Editar pausas manualmente"],
            horizontal=True,
            help=(
                "Use automático para atrasos na chegada. Use manual quando a pausa saiu "
                "em outro horário, por exemplo por ligação."
            ),
        )
        auto_pauses = adjustment_mode == "Automático pela entrada"
        editable_schedule = apply_time_adjustments(
            prepare_editable_schedule(schedule),
            selected_date,
        )

        if auto_pauses:
            editor_data = editable_schedule[["Colaborador", "Supervisor", "Entrada"]].copy()
            disabled_columns = ["Colaborador", "Supervisor"]
        else:
            editor_data = editable_schedule.copy()
            disabled_columns = ["Colaborador", "Supervisor"]

        editor_key = f"schedule_editor_{abs(hash((tuple(selected_labels), selected_time, adjustment_mode)))}"
        edited_schedule = st.data_editor(
            editor_data,
            hide_index=True,
            use_container_width=True,
            disabled=disabled_columns,
            key=editor_key,
            column_config={
                "Entrada": st.column_config.TextColumn(
                    "Entrada",
                    help="Use HH:MM. A saída será entrada + 6h20.",
                ),
                "Pausa 1 início": st.column_config.TextColumn("Pausa 1 início"),
                "Pausa 20 início": st.column_config.TextColumn("Pausa 20 início"),
                "Pausa 2 início": st.column_config.TextColumn("Pausa 2 início"),
            },
        )

        try:
            schedule = calculate_adjusted_schedule(edited_schedule, auto_pauses)
        except ValueError as error:
            st.error(str(error))
            st.stop()

        adjustment_rows_to_save = prepare_editable_schedule(schedule)
        save_adjustment_col, save_adjustment_status_col = st.columns([0.35, 1])
        if save_adjustment_col.button("Salvar ajustes", use_container_width=True):
            save_time_adjustments(
                selected_date,
                adjustment_rows_to_save,
                adjustment_mode,
            )
            save_adjustment_status_col.success(
                f"Ajustes de horário de {formatted_date} salvos com sucesso."
            )

absence_options = sorted(schedule["Colaborador"].tolist()) if not schedule.empty else []
saved_absences = [
    collaborator
    for collaborator in load_absences(selected_date)
    if collaborator in absence_options
]
absent_collaborators = absence_col.multiselect(
    "Colaboradores que faltaram",
    absence_options,
    default=saved_absences,
    placeholder="Selecione um ou mais colaboradores",
)
absent_names = set(absent_collaborators)
pause_status = load_pause_status(selected_date)

selected_absence_rows = schedule[schedule["Colaborador"].isin(absent_names)].copy()
save_col, status_col = st.columns([0.35, 1])
if save_col.button("Salvar faltas", use_container_width=True):
    save_absences(selected_date, selected_absence_rows)
    status_col.success(f"Faltas de {formatted_date} salvas com sucesso.")

if absent_names:
    st.markdown(
        f"""
        <div class="absence-summary">
            {len(absent_names)} colaborador(es) faltaram em {formatted_date}.
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"""
        <div class="absence-summary">
            Nenhuma falta registrada em {formatted_date}.
        </div>
        """,
        unsafe_allow_html=True,
    )

metric_col_1, metric_col_2, metric_col_3, metric_col_4 = st.columns(4)
with metric_col_1:
    render_kpi("Colaboradores", len(schedule))
with metric_col_2:
    render_kpi("Horários", supervisor_data["HORÁRIO"].nunique(), "time")
with metric_col_3:
    render_kpi("Jornada", "6h20", "workday")
with metric_col_4:
    render_kpi("Faltas no dia", len(absent_names), "absences")

schedule_header_col, export_csv_col, export_xlsx_col = st.columns([2.2, 0.9, 0.9])
schedule_header_col.subheader("Escala de pausas")

if schedule.empty:
    st.info("Nenhum colaborador encontrado para os filtros selecionados.")
else:
    export_csv_col.download_button(
        "Baixar CSV",
        data=schedule.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"escala_pausas_{selected_date.isoformat()}.csv",
        mime="text/csv",
        use_container_width=True,
    )
    export_xlsx_col.download_button(
        "Baixar Excel",
        data=schedule_to_excel_bytes(schedule),
        file_name=f"escala_pausas_{selected_date.isoformat()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    card_tab, table_tab = st.tabs(["Cartões", "Tabela"])
    with card_tab:
        render_mobile_cards(schedule, absent_names, pause_status, selected_date)
    with table_tab:
        st.dataframe(
            style_schedule_table(schedule, absent_names, pause_status),
            hide_index=True,
            use_container_width=True,
        )

st.subheader("Histórico de faltas")
history = load_absence_history()

if history.empty:
    st.info("Nenhuma falta salva no histórico ainda.")
else:
    history_by_period_tab, history_by_collaborator_tab = st.tabs(
        ["Relatório por período", "Relatório por colaborador"]
    )

    with history_by_period_tab:
        history_dates = pd.to_datetime(history["Data ISO"]).dt.date
        min_history_date = history_dates.min()
        max_history_date = history_dates.max()
        period_col_1, period_col_2 = st.columns(2)
        start_date = period_col_1.date_input(
            "Data inicial",
            value=min_history_date,
            format="DD/MM/YYYY",
            key="history_start_date",
        )
        end_date = period_col_2.date_input(
            "Data final",
            value=max_history_date,
            format="DD/MM/YYYY",
            key="history_end_date",
        )

        if start_date > end_date:
            st.warning("A data inicial precisa ser menor ou igual à data final.")
        else:
            period_history = history[
                pd.to_datetime(history["Data ISO"]).dt.date.between(start_date, end_date)
            ].copy()
            render_kpi("Faltas no período", len(period_history), "absences")

            if period_history.empty:
                st.info("Nenhuma falta encontrada nesse período.")
            else:
                render_history_rows(period_history, "period")

    with history_by_collaborator_tab:
        collaborators = sorted(history["Colaborador"].unique())
        selected_collaborator = st.selectbox("Colaborador", collaborators)
        collaborator_history = history[history["Colaborador"].eq(selected_collaborator)]
        render_kpi("Faltas do colaborador", len(collaborator_history), "absences")
        render_history_rows(collaborator_history, "collaborator")
