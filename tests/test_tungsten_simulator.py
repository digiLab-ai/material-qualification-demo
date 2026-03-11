from material_qualification_demo.simulators.tungsten import (
    TungstenQualificationConfig,
    TungstenQualificationSimulator,
)


def test_forward_returns_expected_number_of_results():
    sim = TungstenQualificationSimulator(TungstenQualificationConfig())
    X = [
        [0.0, 300.0, 0.001],
        [1.0, 900.0, 0.005],
    ]
    y = sim.forward(X)
    assert len(y) == 2


def test_damage_increases_strength_and_hardness_and_reduces_diffusivity():
    sim = TungstenQualificationSimulator(
        TungstenQualificationConfig(dpa_measurement_relative_std=0.0)
    )
    low = sim.evaluate(dpa=0.0, irradiation_temperature_c=500.0, impurity_fraction=0.001)
    high = sim.evaluate(dpa=3.0, irradiation_temperature_c=500.0, impurity_fraction=0.001)

    assert high["lower_yield_stress_mpa"] > low["lower_yield_stress_mpa"]
    assert high["hardness_gpa"] > low["hardness_gpa"]
    assert high["thermal_diffusivity_mm2_s"] < low["thermal_diffusivity_mm2_s"]


def test_higher_temperature_recovers_some_hardening():
    sim = TungstenQualificationSimulator(
        TungstenQualificationConfig(dpa_measurement_relative_std=0.0)
    )
    cold = sim.evaluate(dpa=2.0, irradiation_temperature_c=500.0, impurity_fraction=0.005)
    hot = sim.evaluate(dpa=2.0, irradiation_temperature_c=1400.0, impurity_fraction=0.005)

    assert hot["lower_yield_stress_mpa"] < cold["lower_yield_stress_mpa"]
    assert hot["hardness_gpa"] < cold["hardness_gpa"]


def test_anchor_points_are_domain_corners():
    sim = TungstenQualificationSimulator(TungstenQualificationConfig())
    pts = sim.anchor_points((0.0, 2.0), (300.0, 1200.0), (0.001, 0.02))
    assert pts == [
        [0.0, 300.0, 0.001],
        [2.0, 1200.0, 0.02],
    ]


def test_dpa_measurement_noise_changes_reported_dpa_when_enabled():
    sim = TungstenQualificationSimulator(
        TungstenQualificationConfig(dpa_measurement_relative_std=0.05, random_seed=7)
    )
    result = sim.evaluate(dpa=2.0, irradiation_temperature_c=800.0, impurity_fraction=0.005)
    assert result["dpa"] != 2.0


def test_impurity_fraction_is_snapped_to_nearest_available_sample():
    sim = TungstenQualificationSimulator(
        TungstenQualificationConfig(
            dpa_measurement_relative_std=0.0,
            available_impurity_fractions=(0.001, 0.003, 0.006, 0.01),
        )
    )
    result = sim.evaluate(dpa=1.0, irradiation_temperature_c=800.0, impurity_fraction=0.005)
    assert result["impurity_fraction"] == 0.006
