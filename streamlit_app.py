import logging
import os
from html import escape
from pathlib import Path
from urllib.parse import quote

import streamlit as st
from dotenv import load_dotenv

from rag_engine import GROQ_DEFAULT_MODEL, get_car_comparison_analysis, groq_is_ready
from vehicle_data import build_fallback_profile, build_years, get_makes, get_models, get_variant_profiles


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

LOGGER = logging.getLogger("car_comparison_streamlit")
if not LOGGER.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


st.set_page_config(
    page_title="Luxury Car Comparison AI",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def load_makes():
    return get_makes()


@st.cache_data(show_spinner=False)
def load_models(year, make):
    return get_models(year, make)


@st.cache_data(show_spinner=False)
def load_variant_profiles(year, make, model):
    return get_variant_profiles(year, make, model)


def sync_streamlit_secrets_to_env():
    secret_keys = (
        "GROQ_API_KEY",
        "GROQ_MODEL",
        "GROQ_TEMPERATURE",
        "GROQ_MAX_TOKENS",
    )
    try:
        for key in secret_keys:
            if not os.getenv(key) and key in st.secrets:
                os.environ[key] = str(st.secrets[key])
    except Exception:
        return


def inject_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=Space+Grotesk:wght@500;700&display=swap');

        :root {
            --sand: #f8f2e7;
            --muted: rgba(248, 242, 231, 0.72);
            --line: rgba(233, 179, 63, 0.18);
            --panel: rgba(7, 15, 27, 0.76);
            --panel-strong: rgba(7, 15, 27, 0.9);
            --teal: #53d4c7;
            --gold: #e9b33f;
            --sky: #7ac0ff;
            --shadow: 0 28px 80px rgba(0, 0, 0, 0.38);
        }

        .stApp {
            background:
                radial-gradient(circle at 12% 14%, rgba(83, 212, 199, 0.12), transparent 24%),
                radial-gradient(circle at 84% 18%, rgba(122, 192, 255, 0.11), transparent 24%),
                radial-gradient(circle at 70% 82%, rgba(233, 179, 63, 0.12), transparent 20%),
                linear-gradient(180deg, #07111f 0%, #091627 48%, #030914 100%);
            color: var(--sand);
            font-family: "Manrope", sans-serif;
        }

        .block-container {
            max-width: 1380px;
            padding-top: 2.2rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3 {
            font-family: "Space Grotesk", sans-serif;
            letter-spacing: -0.04em;
            color: var(--sand);
        }

        [data-testid="stSidebar"] {
            background: rgba(5, 10, 18, 0.86);
        }

        .stMarkdown, .stCaption, label, p, li {
            color: var(--sand);
        }

        div[data-baseweb="select"] > div,
        div[data-baseweb="select"] input,
        .stTextInput input {
            background: rgba(10, 20, 35, 0.82) !important;
            border-color: rgba(122, 192, 255, 0.18) !important;
            color: var(--sand) !important;
            border-radius: 16px !important;
        }

        div[data-baseweb="select"] > div:hover {
            border-color: rgba(122, 192, 255, 0.38) !important;
        }

        .stButton > button {
            width: 100%;
            min-height: 3.2rem;
            border: 0;
            border-radius: 18px;
            color: #08101c;
            font-family: "Space Grotesk", sans-serif;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            background: linear-gradient(135deg, #f0b94a 0%, #ffd77e 42%, #53d4c7 100%);
            box-shadow: 0 16px 36px rgba(233, 179, 63, 0.22);
        }

        .stButton > button:hover {
            box-shadow: 0 20px 42px rgba(83, 212, 199, 0.24);
        }

        .stButton > button:disabled {
            opacity: 0.42;
            box-shadow: none;
        }

        .hero-shell {
            padding: 2rem;
            border-radius: 30px;
            border: 1px solid var(--line);
            background:
                linear-gradient(135deg, rgba(233, 179, 63, 0.08), transparent 34%),
                linear-gradient(180deg, rgba(7, 15, 27, 0.92), rgba(7, 15, 27, 0.72));
            box-shadow: var(--shadow);
            margin-bottom: 1.5rem;
        }

        .eyebrow {
            margin: 0 0 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.18em;
            font-size: 0.78rem;
            color: #9fe1da;
            font-weight: 700;
        }

        .hero-title {
            margin: 0;
            font-size: clamp(2.4rem, 4.8vw, 5rem);
            line-height: 0.95;
            max-width: 920px;
        }

        .hero-copy {
            max-width: 760px;
            margin: 1rem 0 0;
            color: var(--muted);
            line-height: 1.7;
            font-size: 1rem;
        }

        .pill-row {
            display: flex;
            gap: 0.75rem;
            flex-wrap: wrap;
            margin-top: 1.4rem;
        }

        .pill {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.55rem 0.95rem;
            border-radius: 999px;
            border: 1px solid rgba(248, 242, 231, 0.08);
            background: rgba(248, 242, 231, 0.05);
            color: var(--sand);
            font-size: 0.84rem;
        }

        .panel-kicker {
            text-transform: uppercase;
            letter-spacing: 0.14em;
            color: #9fe1da;
            font-size: 0.75rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }

        .panel-title {
            font-size: 1.45rem;
            font-family: "Space Grotesk", sans-serif;
            margin-bottom: 0.2rem;
        }

        .panel-badge {
            display: inline-flex;
            padding: 0.45rem 0.8rem;
            border-radius: 999px;
            border: 1px solid rgba(122, 192, 255, 0.18);
            background: rgba(122, 192, 255, 0.08);
            color: #d7ebff;
            font-size: 0.8rem;
            margin-bottom: 1rem;
        }

        [data-testid="stImage"] img {
            border-radius: 24px;
            border: 1px solid rgba(122, 192, 255, 0.14);
        }

        .vehicle-meta {
            margin-top: 0.9rem;
            padding: 1rem 1.05rem;
            border-radius: 22px;
            border: 1px solid rgba(248, 242, 231, 0.06);
            background: rgba(248, 242, 231, 0.04);
            color: var(--muted);
            line-height: 1.7;
        }

        .vehicle-meta strong {
            color: var(--sand);
        }

        .metric-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.8rem;
            margin-top: 0.95rem;
        }

        .metric-card,
        .empty-card {
            padding: 0.95rem;
            border-radius: 20px;
            border: 1px solid rgba(248, 242, 231, 0.06);
            background: rgba(248, 242, 231, 0.035);
        }

        .metric-label {
            display: block;
            font-size: 0.76rem;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .metric-value {
            display: block;
            margin-top: 0.45rem;
            font-size: 1rem;
            color: var(--sand);
            font-weight: 700;
        }

        .versus-stack {
            display: grid;
            justify-items: center;
            gap: 1rem;
            padding-top: 7.25rem;
        }

        .versus-chip {
            width: 96px;
            height: 96px;
            border-radius: 999px;
            display: grid;
            place-items: center;
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.2rem;
            font-weight: 700;
            letter-spacing: 0.18em;
            color: #08101c;
            background: linear-gradient(135deg, #ffd77e 0%, #53d4c7 100%);
            box-shadow: 0 18px 42px rgba(83, 212, 199, 0.22);
        }

        .versus-copy {
            color: var(--muted);
            text-align: center;
            line-height: 1.65;
            font-size: 0.95rem;
            max-width: 180px;
        }

        .matrix-shell,
        .analysis-shell {
            margin-top: 1.6rem;
            padding: 1.45rem;
            border-radius: 28px;
            border: 1px solid var(--line);
            background:
                linear-gradient(180deg, rgba(7, 15, 27, 0.9), rgba(7, 15, 27, 0.72));
            box-shadow: var(--shadow);
        }

        .matrix-head,
        .matrix-row {
            display: grid;
            grid-template-columns: minmax(0, 1fr) minmax(180px, 0.9fr) minmax(180px, 0.9fr);
            gap: 0.85rem;
            align-items: center;
            border-radius: 18px;
            padding: 0.95rem 1rem;
        }

        .matrix-head {
            background: rgba(83, 212, 199, 0.08);
            border: 1px solid rgba(83, 212, 199, 0.12);
            margin-top: 1rem;
        }

        .matrix-row {
            margin-top: 0.75rem;
            background: rgba(248, 242, 231, 0.035);
            border: 1px solid rgba(248, 242, 231, 0.05);
        }

        .matrix-label {
            color: #d9eeff;
            font-weight: 700;
        }

        .matrix-value {
            color: var(--muted);
        }

        .section-title {
            margin: 0;
            font-size: 1.65rem;
        }

        .section-copy {
            margin: 0.35rem 0 0;
            color: var(--muted);
            line-height: 1.7;
        }

        .analysis-body {
            margin-top: 1rem;
            padding: 1.2rem;
            border-radius: 22px;
            border: 1px solid rgba(248, 242, 231, 0.06);
            background: rgba(248, 242, 231, 0.035);
            color: var(--sand);
            line-height: 1.8;
            white-space: pre-wrap;
        }

        .empty-card {
            color: var(--muted);
            line-height: 1.65;
        }

        @media (max-width: 900px) {
            .metric-grid,
            .matrix-head,
            .matrix-row {
                grid-template-columns: 1fr;
            }

            .versus-stack {
                padding-top: 1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def ensure_session_defaults():
    years = [str(year) for year in build_years()]
    default_year = years[0]
    for side in ("left", "right"):
        st.session_state.setdefault(f"{side}_year", default_year)
        st.session_state.setdefault(f"{side}_make", "")
        st.session_state.setdefault(f"{side}_model", "")
        st.session_state.setdefault(f"{side}_variant", "")
    st.session_state.setdefault("comparison_result", None)
    st.session_state.setdefault("comparison_signature", None)


def set_valid_state(key, valid_options, fallback):
    if st.session_state.get(key) not in valid_options:
        st.session_state[key] = fallback


def format_select_value(value):
    return value or "Select an option"


def build_vehicle_badge(profile):
    if not profile:
        return "Awaiting selection"
    if profile["has_detailed_specs"]:
        return "Detailed specs loaded"
    return "Fallback profile"


def profile_signature(profile):
    if not profile:
        return None
    return "|".join(
        [
            str(profile.get("year", "")),
            profile.get("make", ""),
            profile.get("model", ""),
            profile.get("variant", ""),
        ]
    )


def build_vehicle_image_url(make, model):
    return (
        "https://cdn.imagin.studio/getimage"
        f"?customer=img-demo&make={quote(make)}&modelFamily={quote(model)}"
    )


def build_highlights_html(profile):
    highlights = (profile.get("display_specs") or [])[:4]
    if not highlights:
        return "<div class='empty-card'>Detailed specs are not available for this selection yet.</div>"

    cards = []
    for item in highlights:
        cards.append(
            "<div class='metric-card'>"
            f"<span class='metric-label'>{escape(item['label'])}</span>"
            f"<span class='metric-value'>{escape(item['value'])}</span>"
            "</div>"
        )
    return f"<div class='metric-grid'>{''.join(cards)}</div>"


def build_vehicle_meta_html(profile):
    if not profile:
        return (
            "<div class='vehicle-meta'>"
            "Choose a year, make, model, and variant to load the technical profile."
            "</div>"
        )

    label = f"{profile['year']} {profile['variant']}"
    return (
        "<div class='vehicle-meta'>"
        f"<strong>{escape(label)}</strong><br>"
        f"{escape(profile['source'])}"
        "</div>"
    )


def build_comparison_table_html(left_profile, right_profile):
    if not left_profile and not right_profile:
        return "<div class='empty-card'>Select two vehicles to build a side-by-side comparison matrix.</div>"

    labels = []
    left_map = {}
    right_map = {}

    for item in left_profile.get("display_specs", []) if left_profile else []:
        left_map[item["label"]] = item["value"]
        if item["label"] not in labels:
            labels.append(item["label"])

    for item in right_profile.get("display_specs", []) if right_profile else []:
        right_map[item["label"]] = item["value"]
        if item["label"] not in labels:
            labels.append(item["label"])

    if not labels:
        return "<div class='empty-card'>Specs are limited for the current selection.</div>"

    left_name = (
        f"{left_profile['make']} {left_profile['model']}"
        if left_profile
        else "Vehicle A"
    )
    right_name = (
        f"{right_profile['make']} {right_profile['model']}"
        if right_profile
        else "Vehicle B"
    )

    rows = [
        "<div class='matrix-head'>"
        "<div class='matrix-label'>Specification</div>"
        f"<div class='matrix-label'>{escape(left_name)}</div>"
        f"<div class='matrix-label'>{escape(right_name)}</div>"
        "</div>"
    ]

    for label in labels:
        rows.append(
            "<div class='matrix-row'>"
            f"<div class='matrix-label'>{escape(label)}</div>"
            f"<div class='matrix-value'>{escape(left_map.get(label, 'Not available'))}</div>"
            f"<div class='matrix-value'>{escape(right_map.get(label, 'Not available'))}</div>"
            "</div>"
        )

    return "".join(rows)


def render_vehicle_panel(side, panel_label):
    year_key = f"{side}_year"
    make_key = f"{side}_make"
    model_key = f"{side}_model"
    variant_key = f"{side}_variant"
    header_slot = st.empty()

    years = [str(year) for year in build_years()]
    set_valid_state(year_key, years, years[0])

    makes_error = None
    try:
        make_names = [item["name"] for item in load_makes()]
    except Exception as exc:
        make_names = []
        makes_error = str(exc)
    set_valid_state(make_key, [""] + make_names, "")

    primary_selectors = st.columns(2)
    with primary_selectors[0]:
        selected_year = st.selectbox("Year", years, key=year_key)
    with primary_selectors[1]:
        selected_make = st.selectbox(
            "Make",
            [""] + make_names,
            key=make_key,
            format_func=format_select_value,
        )

    model_names = []
    models_error = None
    if selected_make:
        try:
            model_names = [item["name"] for item in load_models(int(selected_year), selected_make)]
        except Exception as exc:
            models_error = str(exc)
    set_valid_state(model_key, [""] + model_names, "")

    variant_profiles = []
    variants_error = None
    secondary_selectors = st.columns(2)
    with secondary_selectors[0]:
        selected_model = st.selectbox(
            "Model",
            [""] + model_names,
            key=model_key,
            disabled=not selected_make,
            format_func=format_select_value,
        )

    if selected_make and selected_model:
        try:
            variant_profiles = load_variant_profiles(int(selected_year), selected_make, selected_model)
        except Exception as exc:
            variants_error = str(exc)
    variant_names = [profile["variant"] for profile in variant_profiles]
    default_variant = variant_names[0] if variant_names else ""
    set_valid_state(variant_key, [""] + variant_names, default_variant)
    with secondary_selectors[1]:
        selected_variant = st.selectbox(
            "Variant",
            [""] + variant_names,
            key=variant_key,
            disabled=not selected_model,
            format_func=format_select_value,
        )

    profile = None
    if selected_make and selected_model and selected_variant:
        profile = next(
            (item for item in variant_profiles if item["variant"] == selected_variant),
            None,
        )
        if profile is None:
            profile = build_fallback_profile(
                int(selected_year),
                selected_make,
                selected_model,
                variant=selected_variant,
            )

    title = "Select a car"
    if profile:
        title = f"{profile['make']} {profile['model']}"
    elif selected_make and selected_model:
        title = f"{selected_make} {selected_model}"

    header_slot.markdown(
        f"""
        <div class="panel-kicker">{escape(panel_label)}</div>
        <div class="panel-title">{escape(title)}</div>
        <div class="panel-badge">{escape(build_vehicle_badge(profile))}</div>
        """,
        unsafe_allow_html=True,
    )

    if makes_error:
        st.error(f"Unable to load makes: {makes_error}")
    if models_error:
        st.error(f"Unable to load models: {models_error}")
    if variants_error:
        st.error(f"Unable to load variants: {variants_error}")

    if profile:
        st.image(
            build_vehicle_image_url(profile["make"], profile["model"]),
            use_container_width=True,
        )

    st.markdown(build_vehicle_meta_html(profile), unsafe_allow_html=True)
    st.markdown(build_highlights_html(profile or {}), unsafe_allow_html=True)
    return profile


def render_analysis(result, left_profile, right_profile):
    left_name = f"{left_profile['make']} {left_profile['model']}" if left_profile else "Vehicle A"
    right_name = f"{right_profile['make']} {right_profile['model']}" if right_profile else "Vehicle B"
    mode_label = (
        f"Groq mode - {result['model']}"
        if result.get("groq_configured")
        else f"Local preview - {result['model']}"
    )
    analysis_text = escape(result.get("analysis", "")).replace("\n", "<br>")

    st.markdown(
        f"""
        <section class="analysis-shell">
          <p class="eyebrow">AI Comparison</p>
          <h2 class="section-title">{escape(left_name)} vs {escape(right_name)}</h2>
          <p class="section-copy">{escape(mode_label)}</p>
          <div class="analysis-body">{analysis_text}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def main():
    sync_streamlit_secrets_to_env()
    inject_styles()
    ensure_session_defaults()

    model_name = os.getenv("GROQ_MODEL", GROQ_DEFAULT_MODEL)
    ready_label = "Groq ready" if groq_is_ready() else "Groq not configured"

    st.markdown(
        f"""
        <section class="hero-shell">
          <p class="eyebrow">Groq x NHTSA vPIC x Streamlit</p>
          <h1 class="hero-title">Compare premium cars side by side with live specs and Dubai-focused AI advice.</h1>
          <p class="hero-copy">
            Build your own versus board from year, make, model, and variant data, then turn the
            technical sheet into a concise recommendation for daily life in Dubai.
          </p>
          <div class="pill-row">
            <span class="pill">Native Streamlit UI</span>
            <span class="pill">Live vPIC Data</span>
            <span class="pill">{escape(ready_label)} - {escape(model_name)}</span>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    left_col, center_col, right_col = st.columns([1, 0.22, 1], gap="large")

    with left_col:
        left_profile = render_vehicle_panel("left", "Vehicle A")

    with center_col:
        st.markdown(
            """
            <div class="versus-stack">
              <div class="versus-chip">VS</div>
              <div class="versus-copy">
                Select both variants to unlock the comparison matrix and AI recommendation.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        st.write("")

    with right_col:
        right_profile = render_vehicle_panel("right", "Vehicle B")

    can_compare = bool(left_profile and right_profile)
    current_signature = (profile_signature(left_profile), profile_signature(right_profile))
    saved_signature = st.session_state.get("comparison_signature")
    if saved_signature and saved_signature != current_signature:
        st.session_state["comparison_result"] = None
        st.session_state["comparison_signature"] = None

    compare_clicked = False
    with center_col:
        compare_clicked = st.button(
            "Compare with AI",
            type="primary",
            disabled=not can_compare,
        )

    if compare_clicked and can_compare:
        with st.spinner("Comparing vehicles..."):
            LOGGER.info(
                "Comparing %s vs %s",
                left_profile.get("variant", "Vehicle A"),
                right_profile.get("variant", "Vehicle B"),
            )
            st.session_state["comparison_result"] = get_car_comparison_analysis(
                left_profile,
                right_profile,
            )
            st.session_state["comparison_signature"] = current_signature

    st.markdown(
        f"""
        <section class="matrix-shell">
          <p class="eyebrow">Raw Spec Comparison</p>
          <h2 class="section-title">Technical snapshot</h2>
          <p class="section-copy">
            {escape('Live spec comparison ready.' if can_compare else 'Select two vehicles to unlock the full matrix.')}
          </p>
          {build_comparison_table_html(left_profile, right_profile)}
        </section>
        """,
        unsafe_allow_html=True,
    )

    result = st.session_state.get("comparison_result")
    if result and st.session_state.get("comparison_signature") == current_signature:
        render_analysis(result, left_profile, right_profile)
    elif not groq_is_ready():
        st.markdown(
            """
            <section class="analysis-shell">
              <p class="eyebrow">AI Comparison</p>
              <h2 class="section-title">Ready when you are</h2>
              <p class="section-copy">
                Add a valid <code>GROQ_API_KEY</code> in Streamlit secrets to switch from local preview mode
                to the full Groq-backed recommendation.
              </p>
            </section>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
