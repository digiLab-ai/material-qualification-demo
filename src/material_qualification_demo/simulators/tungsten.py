from __future__ import annotations

from typing import Literal, TypedDict

import numpy as np
from pydantic import Field, field_validator
try:
    from typeguard import typechecked
except ImportError:  # pragma: no cover
    def typechecked(obj):
        return obj

from .base import Simulator, SimulatorConfig, SimulatorMeta


class TungstenQualificationConfig(SimulatorConfig):
    base_yield_stress_mpa: float = Field(
        default=550.0,
        gt=0,
        description="Unirradiated lower yield stress baseline (MPa).",
    )
    base_hardness_gpa: float = Field(
        default=3.2,
        gt=0,
        description="Unirradiated hardness baseline (GPa).",
    )
    base_thermal_diffusivity_mm2_s: float = Field(
        default=62.0,
        gt=0,
        description="Unirradiated thermal diffusivity baseline (mm^2/s).",
    )
    damage_saturation_dpa: float = Field(
        default=0.75,
        gt=0,
        description="Characteristic dpa scale for irradiation saturation.",
    )
    recovery_temperature_c: float = Field(
        default=1100.0,
        description="Characteristic temperature for irradiation recovery.",
    )
    recovery_width_c: float = Field(
        default=180.0,
        gt=0,
        description="Temperature width controlling recovery transition.",
    )
    max_impurity_fraction: float = Field(
        default=0.05,
        gt=0,
        le=1.0,
        description="Maximum allowed impurity fraction.",
    )
    dpa_measurement_relative_std: float = Field(
        default=0.0,
        ge=0.0,
        description=(
            "Relative standard deviation for measured DPA noise. "
            "Measured DPA is sampled as requested_dpa * (1 + N(0, std))."
        ),
    )
    available_impurity_fractions: tuple[float, ...] = Field(
        default=(0.001, 0.003, 0.005, 0.01, 0.015, 0.02),
        description="Discrete impurity fractions that are experimentally available.",
    )
    random_seed: int | None = Field(
        default=12345,
        description="Seed used for reproducible DPA measurement noise.",
    )
    hardness_mode: Literal["gpa"] = Field(default="gpa", description="Hardness unit mode.")
    meta: SimulatorMeta = Field(
        default=SimulatorMeta(
            name="TungstenQualificationSimulator",
            description=(
                "Tungsten irradiation simulator."
            ),
            version="0.1.0",
            tags=["materials", "fusion", "tungsten", "irradiation", "qualification"],
        )
    )

    @field_validator("recovery_temperature_c")
    @classmethod
    def validate_recovery_temperature(cls, v: float) -> float:
        if v < -273.15:
            raise ValueError("recovery_temperature_c must be above absolute zero.")
        return v

    @field_validator("available_impurity_fractions")
    @classmethod
    def validate_available_impurity_fractions(cls, values: tuple[float, ...]) -> tuple[float, ...]:
        if not values:
            raise ValueError("available_impurity_fractions must not be empty.")
        if any(v < 0 for v in values):
            raise ValueError("available_impurity_fractions must be non-negative.")
        return tuple(sorted(float(v) for v in values))


class TungstenQualificationOutput(TypedDict):
    dpa: float
    irradiation_temperature_c: float
    impurity_fraction: float
    lower_yield_stress_mpa: float
    hardness_gpa: float
    thermal_diffusivity_mm2_s: float


@typechecked
class TungstenQualificationSimulator(Simulator):
    def __init__(self, config: TungstenQualificationConfig):
        self.config = config
        self.rng = np.random.default_rng(self.config.random_seed)

    def forward(self, X: list[list[float]]) -> list[TungstenQualificationOutput]:
        """
        Evaluate the simulator on a batch of samples.

        Each sample must contain exactly three values:
        - dpa
        - irradiation_temperature_c
        - impurity_fraction
        """
        results: list[TungstenQualificationOutput] = []
        for params in X:
            if len(params) != 3:
                raise ValueError(
                    "Each input must contain exactly three elements: "
                    "dpa, irradiation_temperature_c, impurity_fraction."
                )

            dpa, irradiation_temperature_c, impurity_fraction = params
            results.append(
                self.evaluate(
                    dpa=dpa,
                    irradiation_temperature_c=irradiation_temperature_c,
                    impurity_fraction=impurity_fraction,
                )
            )
        return results

    def evaluate(
        self,
        dpa: float,
        irradiation_temperature_c: float,
        impurity_fraction: float,
    ) -> TungstenQualificationOutput:
        """
        Compute stylised post-irradiation tungsten properties.

        Behaviour encoded in this demonstrator:
        - increasing dpa tends to increase lower yield stress
        - increasing dpa tends to increase hardness
        - increasing dpa tends to reduce thermal diffusivity
        - higher irradiation temperature allows partial damage recovery
        - higher impurity fraction tends to increase strength/hardness
          and reduce thermal diffusivity
        """
        self._validate_inputs(dpa, irradiation_temperature_c, impurity_fraction)
        measured_dpa = self._measure_dpa(dpa)
        sampled_impurity_fraction = self._nearest_available_impurity(impurity_fraction)

        damage = self._damage_saturation(measured_dpa)
        recovery = self._recovery_factor(irradiation_temperature_c)
        impurity_effect = self._impurity_effect(sampled_impurity_fraction)

        hardening_term = damage * (1.0 - 0.55 * recovery)

        lower_yield_stress_mpa = (
            self.config.base_yield_stress_mpa
            + 430.0 * hardening_term
            + 165.0 * impurity_effect
        )

        hardness_gpa = (
            self.config.base_hardness_gpa
            + 1.75 * hardening_term
            + 0.80 * impurity_effect
        )

        thermal_diffusivity_mm2_s = (
            self.config.base_thermal_diffusivity_mm2_s
            - 17.5 * damage * (1.0 - 0.25 * recovery)
            - 10.0 * impurity_effect
            - 0.006 * max(irradiation_temperature_c - 20.0, 0.0)
        )

        thermal_diffusivity_mm2_s = max(5.0, thermal_diffusivity_mm2_s)

        return {
            "dpa": float(measured_dpa),
            "irradiation_temperature_c": float(irradiation_temperature_c),
            "impurity_fraction": float(sampled_impurity_fraction),
            "lower_yield_stress_mpa": float(lower_yield_stress_mpa),
            "hardness_gpa": float(hardness_gpa),
            "thermal_diffusivity_mm2_s": float(thermal_diffusivity_mm2_s),
        }

    def anchor_points(
        self,
        dpa_bounds: tuple[float, float],
        temperature_bounds: tuple[float, float],
        impurity_bounds: tuple[float, float],
    ) -> list[list[float]]:
        """
        Return the two anchor points at the min and max corners of the domain.
        """
        dpa_min, dpa_max = dpa_bounds
        temp_min, temp_max = temperature_bounds
        imp_min, imp_max = impurity_bounds

        self._validate_inputs(dpa_min, temp_min, imp_min)
        self._validate_inputs(dpa_max, temp_max, imp_max)

        return [
            [float(dpa_min), float(temp_min), float(imp_min)],
            [float(dpa_max), float(temp_max), float(imp_max)],
        ]

    def _validate_inputs(
        self,
        dpa: float,
        irradiation_temperature_c: float,
        impurity_fraction: float,
    ) -> None:
        if dpa < 0:
            raise ValueError(f"`dpa` must be non-negative, got {dpa}.")
        if irradiation_temperature_c < -273.15:
            raise ValueError(
                f"`irradiation_temperature_c` must be above absolute zero, got {irradiation_temperature_c}."
            )
        if not 0.0 <= impurity_fraction <= self.config.max_impurity_fraction:
            raise ValueError(
                f"`impurity_fraction` must be between 0 and {self.config.max_impurity_fraction}, "
                f"got {impurity_fraction}."
            )

    def _damage_saturation(self, dpa: float) -> float:
        return float(1.0 - np.exp(-dpa / self.config.damage_saturation_dpa))

    def _recovery_factor(self, irradiation_temperature_c: float) -> float:
        z = (irradiation_temperature_c - self.config.recovery_temperature_c) / (
            self.config.recovery_width_c
        )
        return float(1.0 / (1.0 + np.exp(-z)))

    def _impurity_effect(self, impurity_fraction: float) -> float:
        scaled = impurity_fraction / self.config.max_impurity_fraction
        return float(np.sqrt(max(scaled, 0.0)))

    def _measure_dpa(self, requested_dpa: float) -> float:
        if self.config.dpa_measurement_relative_std == 0.0:
            return float(requested_dpa)
        noisy = requested_dpa * (
            1.0 + self.rng.normal(loc=0.0, scale=self.config.dpa_measurement_relative_std)
        )
        return float(max(0.0, noisy))

    def _nearest_available_impurity(self, requested_impurity_fraction: float) -> float:
        available = np.asarray(self.config.available_impurity_fractions, dtype=float)
        idx = int(np.argmin(np.abs(available - requested_impurity_fraction)))
        snapped = float(available[idx])
        return float(min(max(snapped, 0.0), self.config.max_impurity_fraction))
