from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from material_qualification_demo.branding import BRAND_CSS, INDIGO
from material_qualification_demo.simulators.tungsten import (
    TungstenQualificationConfig,
    TungstenQualificationSimulator,
)


INPUT_COLUMNS = ["dpa", "irradiation_temperature_c", "impurity_fraction"]
OUTPUT_COLUMNS = [
    "lower_yield_stress_mpa",
    "hardness_gpa",
    "thermal_diffusivity_mm2_s",
]
INPUT_LABELS = {
    "dpa": "dpa",
    "irradiation_temperature_c": "Irradiation temperature (°C)",
    "impurity_fraction": "Impurity fraction",
}
OUTPUT_LABELS = {
    "lower_yield_stress_mpa": "Lower yield stress (MPa)",
    "hardness_gpa": "Hardness (GPa)",
    "thermal_diffusivity_mm2_s": "Thermal diffusivity (mm²/s)",
}


def to_dataframe(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def split_inputs_outputs(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    return df[INPUT_COLUMNS].copy(), df[OUTPUT_COLUMNS].copy()


def ensure_experiment_state(anchor_records: list[dict], domain_signature: tuple[float, ...]) -> None:
    if "experiment_records" not in st.session_state:
        st.session_state.experiment_records = list(anchor_records)
        st.session_state.domain_signature = domain_signature
        return

    if st.session_state.get("domain_signature") != domain_signature:
        st.session_state.experiment_records = list(anchor_records)
        st.session_state.domain_signature = domain_signature


def reset_to_anchors(anchor_records: list[dict], domain_signature: tuple[float, ...]) -> None:
    st.session_state.experiment_records = list(anchor_records)
    st.session_state.domain_signature = domain_signature


def main() -> None:
    st.set_page_config(
        page_title="material-qualification-demo",
        # page_icon="🧪",
        layout="wide",
    )
    st.markdown(BRAND_CSS, unsafe_allow_html=True)

    assets_dir = Path(__file__).resolve().parents[2] / "assets"
    logo_path = assets_dir / "digiLab logo.png"
    if not logo_path.exists():
        candidates = sorted(assets_dir.glob("*logo*"))
        logo_path = candidates[0] if candidates else None

    cols = st.columns([1, 4])
    with cols[0]:
        if logo_path and logo_path.exists():
            st.image(str(logo_path), use_container_width=True)
    with cols[1]:
        st.title("Material Qualification Demo")
        st.caption(
            "Stylised tungsten irradiation qualification simulator for surrogate-modelling and "
            "active-learning demonstrations."
        )

    st.markdown(
        """
        <div class="digilab-card">
        <b>Inputs</b>: dpa, irradiation temperature, impurity fraction<br>
        <b>Outputs</b>: lower yield stress, hardness, thermal diffusivity<br>
        <span class="metric-caption">
        The initial design of experiments uses two anchor points at the minimum and maximum
        corners of the chosen input domain.
        </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    sim = TungstenQualificationSimulator(TungstenQualificationConfig())

    with st.sidebar:
        st.header("Input domain")
        dpa_min = st.number_input("dpa min", min_value=0.0, value=0.0, step=0.1)
        dpa_max = st.number_input("dpa max", min_value=0.0, value=3.0, step=0.1)

        temp_min = st.number_input(
            "Irradiation temperature min (°C)",
            min_value=-273.15,
            value=300.0,
            step=10.0,
        )
        temp_max = st.number_input(
            "Irradiation temperature max (°C)",
            min_value=-273.15,
            value=1400.0,
            step=10.0,
        )

        impurity_min = st.number_input(
            "Impurity fraction min",
            min_value=0.0,
            max_value=0.05,
            value=0.001,
            step=0.001,
            format="%.4f",
        )
        impurity_max = st.number_input(
            "Impurity fraction max",
            min_value=0.0,
            max_value=0.05,
            value=0.020,
            step=0.001,
            format="%.4f",
        )

    if dpa_min > dpa_max or temp_min > temp_max or impurity_min > impurity_max:
        st.error("Each minimum must be less than or equal to its corresponding maximum.")
        return

    anchor_points = sim.anchor_points(
        dpa_bounds=(dpa_min, dpa_max),
        temperature_bounds=(temp_min, temp_max),
        impurity_bounds=(impurity_min, impurity_max),
    )
    anchor_records = sim.forward(anchor_points)
    domain_signature = (dpa_min, dpa_max, temp_min, temp_max, impurity_min, impurity_max)
    ensure_experiment_state(anchor_records, domain_signature)

    st.subheader("Run Experiment")
    i1, i2, i3 = st.columns(3)
    with i1:
        dpa_eval = st.number_input("dpa", min_value=0.0, value=1.0, step=0.1)
    with i2:
        temp_eval = st.number_input(
            "Irradiation temperature (°C)",
            min_value=-273.15,
            value=800.0,
            step=10.0,
        )
    with i3:
        impurity_eval = st.number_input(
            "Impurity fraction",
            min_value=0.0,
            max_value=0.05,
            value=0.005,
            step=0.001,
            format="%.4f",
        )

    b1, b2, b3 = st.columns(3)
    with b1:
        run_experiment = st.button("Run experiment", type="primary", use_container_width=True)
    with b2:
        remove_last = st.button("Remove last", use_container_width=True)
    with b3:
        reset_experiment = st.button("Reset", use_container_width=True)

    if run_experiment:
        st.session_state.experiment_records.append(
            sim.evaluate(
                dpa=dpa_eval,
                irradiation_temperature_c=temp_eval,
                impurity_fraction=impurity_eval,
            )
        )
    if remove_last:
        if len(st.session_state.experiment_records) > 2:
            st.session_state.experiment_records.pop()
        else:
            st.info("Only the two anchor points remain; nothing to remove.")
    if reset_experiment:
        reset_to_anchors(anchor_records, domain_signature)

    experiment_df = to_dataframe(st.session_state.experiment_records)
    experiment_df["point_type"] = ["anchor", "anchor"] + ["experiment"] * (
        len(experiment_df) - 2
    )
    experiment_df["sample_id"] = [f"sample_{i+1}" for i in range(len(experiment_df))]

    st.subheader("Scatter Plot")
    p1, p2 = st.columns(2)
    with p1:
        selected_input = st.selectbox(
            "Select input (x-axis)",
            options=INPUT_COLUMNS,
            format_func=lambda x: INPUT_LABELS[x],
        )
    with p2:
        selected_output = st.selectbox(
            "Select output (y-axis)",
            options=OUTPUT_COLUMNS,
            format_func=lambda x: OUTPUT_LABELS[x],
        )

    fig = go.Figure()
    anchor_mask = experiment_df["point_type"] == "anchor"
    exp_mask = experiment_df["point_type"] == "experiment"

    fig.add_trace(
        go.Scatter(
            x=experiment_df.loc[anchor_mask, selected_input],
            y=experiment_df.loc[anchor_mask, selected_output],
            mode="markers",
            marker={"size": 11, "color": INDIGO, "symbol": "diamond"},
            name="anchor",
            text=experiment_df.loc[anchor_mask, "sample_id"],
            hovertemplate=(
                "%{text}<br>"
                + f"{INPUT_LABELS[selected_input]}: %{{x:.4g}}<br>"
                + f"{OUTPUT_LABELS[selected_output]}: %{{y:.4g}}<extra></extra>"
            ),
        )
    )
    if exp_mask.any():
        fig.add_trace(
            go.Scatter(
                x=experiment_df.loc[exp_mask, selected_input],
                y=experiment_df.loc[exp_mask, selected_output],
                mode="markers",
                marker={"size": 10, "color": "#16D5C2", "symbol": "circle"},
                name="experiment",
                text=experiment_df.loc[exp_mask, "sample_id"],
                hovertemplate=(
                    "%{text}<br>"
                    + f"{INPUT_LABELS[selected_input]}: %{{x:.4g}}<br>"
                    + f"{OUTPUT_LABELS[selected_output]}: %{{y:.4g}}<extra></extra>"
                ),
            )
        )
    fig.update_layout(
        height=450,
        xaxis_title=INPUT_LABELS[selected_input],
        yaxis_title=OUTPUT_LABELS[selected_output],
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Final Data")
    final_inputs_df, final_outputs_df = split_inputs_outputs(experiment_df)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Inputs**")
        st.dataframe(final_inputs_df, use_container_width=True)
        st.download_button(
            "Download inputs CSV",
            data=final_inputs_df.to_csv(index=False).encode("utf-8"),
            file_name="experiment_inputs.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with c2:
        st.markdown("**Outputs**")
        st.dataframe(final_outputs_df, use_container_width=True)
        st.download_button(
            "Download outputs CSV",
            data=final_outputs_df.to_csv(index=False).encode("utf-8"),
            file_name="experiment_outputs.csv",
            mime="text/csv",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
