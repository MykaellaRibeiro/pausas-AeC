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
    "TROCA CASADA": "Troca casada",
}
SUPERVISOR_ORDER = {
    "DANYELLA LAYSE SILVA TAVARES": 1,
    "OLÍVIA LETÍCIA GOMES VIANA": 2,
    "TROCA CASADA": 3,
}
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
    :root {
        --bg: #eef2f4;
        --surface: #ffffff;
        --surface-soft: #f6f8fa;
        --ink: #111827;
        --muted: #5b6675;
        --line: #d9e0e7;
        --primary: #0f766e;
        --primary-dark: #134e4a;
        --accent: #d97706;
        --blue: #2563eb;
        --success: #15803d;
        --danger: #dc2626;
        --danger-soft: #fff1f2;
    }

    .stApp {
        background: var(--bg);
    }

    .block-container {
        padding-top: 1.15rem;
        padding-bottom: 2.5rem;
        max-width: 1120px;
    }

    h1, h2, h3 {
        color: var(--ink);
        letter-spacing: 0;
    }

    h1 {
        font-size: 2rem;
        line-height: 1.15;
        margin-bottom: 0.25rem;
    }

    p, label, span {
        color: var(--ink);
    }

    div[data-testid="stCaptionContainer"] p {
        color: var(--muted);
        font-size: 0.96rem;
    }

    .app-hero {
        background: var(--surface);
        border: 1px solid var(--line);
        border-left: 6px solid var(--primary);
        border-radius: 8px;
        padding: 1.15rem 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 12px 28px rgba(17, 24, 39, 0.08);
    }

    .app-hero h1 {
        color: var(--ink);
        margin: 0;
        font-size: 2rem;
    }

    .app-hero p {
        color: var(--muted);
        margin: 0.35rem 0 0 0;
        max-width: 760px;
        font-size: 0.98rem;
    }

    div[data-testid="stExpander"] {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 8px;
        box-shadow: 0 10px 24px rgba(17, 24, 39, 0.06);
    }

    div[data-testid="stSelectbox"] label,
    div[data-testid="stFileUploader"] label {
        color: var(--ink);
        font-weight: 650;
    }

    div[data-baseweb="select"] > div {
        background: var(--surface);
        border-color: var(--line);
        border-radius: 8px;
        min-height: 48px;
        box-shadow: 0 8px 20px rgba(17, 24, 39, 0.05);
    }

    .kpi-card {
        background: var(--surface);
        border: 1px solid var(--line);
        border-left: 5px solid var(--primary);
        border-radius: 8px;
        padding: 0.9rem 1rem;
        box-shadow: 0 10px 24px rgba(17, 24, 39, 0.07);
        min-height: 96px;
    }

    .kpi-card .kpi-label {
        color: var(--muted);
        font-size: 0.86rem;
        font-weight: 700;
        margin-bottom: 0.4rem;
    }

    .kpi-card .kpi-value {
        color: var(--ink);
        font-size: 2rem;
        line-height: 1;
        font-weight: 750;
    }

    .kpi-card.time {
        border-left-color: var(--blue);
    }

    .kpi-card.workday {
        border-left-color: var(--accent);
    }

    .kpi-card.absences {
        border-left-color: var(--danger);
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 10px 24px rgba(17, 24, 39, 0.07);
    }

    div[data-testid="stTabs"] button {
        color: var(--muted);
        font-weight: 700;
    }

    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--primary-dark);
    }

    div[data-testid="stDownloadButton"] button {
        border-radius: 8px;
        border: 1px solid var(--primary);
        background: var(--primary);
        color: white;
        font-weight: 750;
        min-height: 46px;
    }

    div[data-testid="stDownloadButton"] button:hover {
        border-color: var(--primary-dark);
        background: var(--primary-dark);
        color: white;
    }

    .schedule-card {
        border: 1px solid var(--line);
        border-left: 5px solid var(--primary);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.85rem;
        background: var(--surface);
        box-shadow: 0 10px 24px rgba(17, 24, 39, 0.07);
    }

    .schedule-card.absent {
        border-left-color: var(--danger);
        background: var(--danger-soft);
    }

    .absence-badge {
        display: inline-block;
        margin-top: 0.55rem;
        padding: 0.28rem 0.5rem;
        border-radius: 8px;
        background: var(--danger);
        color: white;
        font-size: 0.78rem;
        font-weight: 750;
    }

    .absence-summary {
        border: 1px solid #fecaca;
        border-left: 5px solid var(--danger);
        border-radius: 8px;
        background: var(--danger-soft);
        color: #7f1d1d;
        font-weight: 700;
        padding: 0.85rem 1rem;
        margin: 0.85rem 0 1rem 0;
    }

    .history-item {
        border: 1px solid var(--line);
        border-left: 4px solid var(--danger);
        border-radius: 8px;
        background: var(--surface);
        padding: 0.75rem 0.9rem;
        min-height: 74px;
        box-shadow: 0 6px 14px rgba(17, 24, 39, 0.05);
    }

    .history-person {
        color: var(--ink);
        font-weight: 780;
        line-height: 1.25;
        margin-bottom: 0.35rem;
    }

    .history-meta {
        color: var(--muted);
        font-size: 0.86rem;
        font-weight: 620;
        line-height: 1.45;
    }

    .schedule-card strong {
        display: block;
        color: var(--ink);
        font-size: 1.03rem;
        line-height: 1.25;
        margin-bottom: 0.25rem;
    }

    .schedule-card span {
        color: var(--muted);
        font-size: 0.9rem;
        font-weight: 600;
    }

    .pause-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.45rem;
        margin-top: 0.7rem;
    }

    .pause-pill {
        background: var(--surface-soft);
        border: 1px solid var(--line);
        border-left: 4px solid var(--primary);
        border-radius: 8px;
        padding: 0.55rem 0.65rem;
        font-size: 0.86rem;
        color: var(--ink);
        font-weight: 650;
    }

    .pause-pill.p1 {
        background: #f8fafc;
        border-left-color: var(--blue);
    }

    .pause-pill.p20 {
        background: #fffaf0;
        border-left-color: var(--accent);
    }

    .pause-pill.p2 {
        background: #f7fdf9;
        border-left-color: var(--success);
    }

    .pause-pill.supervisor {
        background: #f8fafc;
        border-left-color: var(--primary);
    }

    @media (max-width: 700px) {
        .block-container {
            padding-left: 0.75rem;
            padding-right: 0.75rem;
        }

        h1 {
            font-size: 1.55rem;
        }

        .pause-grid {
            grid-template-columns: 1fr;
        }

        .kpi-card {
            padding: 0.8rem;
            min-height: 86px;
        }

        .kpi-card .kpi-value {
            font-size: 1.7rem;
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

    normalized["SUPERVISOR"] = normalized["SUPERVISOR"].str.upper()
    normalized["STATUS"] = normalized["STATUS"].str.upper()
    normalized = normalized[normalized["STATUS"].eq("ATIVO")].copy()
    normalized = normalized[normalized["SUPERVISOR"].isin(TARGET_SUPERVISORS)].copy()

    normalized["HORÁRIO_ORDENACAO"] = pd.to_datetime(
        normalized["HORÁRIO"], format="%H:%M", errors="coerce"
    )
    normalized = normalized.dropna(subset=["HORÁRIO_ORDENACAO"])
    normalized = normalized.sort_values(["SUPERVISOR", "HORÁRIO_ORDENACAO", "NOME"])
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


def render_mobile_cards(schedule: pd.DataFrame, absent_names: set[str]) -> None:
    for _, row in schedule.iterrows():
        is_absent = row["Colaborador"] in absent_names
        absent_class = " absent" if is_absent else ""
        absent_badge = '<div class="absence-badge">Faltou</div>' if is_absent else ""
        st.markdown(
            f"""<div class="schedule-card{absent_class}">
<strong>{row["Colaborador"]}</strong>
<span>Entrada {row["Entrada"]} · Saída {row["Saída"]}</span>
{absent_badge}
<div class="pause-grid">
<div class="pause-pill p1">Pausa 1: {row["Pausa 1 (10 min)"]}</div>
<div class="pause-pill p20">Pausa 20: {row["Pausa 20 min"]}</div>
<div class="pause-pill p2">Pausa 2: {row["Pausa 2 (10 min)"]}</div>
<div class="pause-pill supervisor">Supervisora: {row["Supervisor"]}</div>
</div>
</div>""",
            unsafe_allow_html=True,
        )


def style_schedule_table(df: pd.DataFrame, absent_names: set[str]):
    def mark_absent_rows(row: pd.Series) -> list[str]:
        if row["Colaborador"] in absent_names:
            return [
                "background-color: #fff1f2; color: #7f1d1d; font-weight: 700;"
                for _ in row
            ]
        return ["" for _ in row]

    return (
        df.style.set_table_styles(
            [
                {
                    "selector": "thead th",
                    "props": [
                        ("background-color", "#f6f8fa"),
                        ("color", "#111827"),
                        ("font-weight", "700"),
                        ("border-color", "#d9e0e7"),
                    ],
                },
                {
                    "selector": "tbody td",
                    "props": [
                        ("border-color", "#d3d9d2"),
                    ],
                },
            ]
        )
        .set_properties(
            subset=["Pausa 1 (10 min)"],
            **{"background-color": "#f8fafc", "font-weight": "650"},
        )
        .set_properties(
            subset=["Pausa 20 min"],
            **{"background-color": "#fffaf0", "font-weight": "650"},
        )
        .set_properties(
            subset=["Pausa 2 (10 min)"],
            **{"background-color": "#f7fdf9", "font-weight": "650"},
        )
        .apply(mark_absent_rows, axis=1)
    )


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
    """
    <section class="app-hero">
        <h1>Controle de Pausas</h1>
        <p>Escala de pausas por supervisora, controle de faltas por data e histórico para acompanhar a operação.</p>
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

supervisor_options = sorted(
    data["SUPERVISOR"].unique(),
    key=lambda value: SUPERVISOR_ORDER.get(value, 99),
)
supervisor_labels = [TARGET_SUPERVISORS.get(value, value.title()) for value in supervisor_options]
label_to_supervisor = dict(zip(supervisor_labels, supervisor_options))

filter_col_1, filter_col_2 = st.columns([1.2, 1])
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

st.subheader("Escala de pausas")

if schedule.empty:
    st.info("Nenhum colaborador encontrado para os filtros selecionados.")
else:
    card_tab, table_tab = st.tabs(["Cartões", "Tabela"])
    with card_tab:
        render_mobile_cards(schedule, absent_names)
    with table_tab:
        st.dataframe(
            style_schedule_table(schedule, absent_names),
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
