"""Gordon-Ng semi-empirical model for chiller power prediction.

The Gordon-Ng model is a thermodynamic model that predicts chiller power
based on cooling load and operating temperatures.

Model equation:
    1/COP = a0 + a1*(Tcond/Qe) + a2*(Tevap/(Qe*Tcond))

Rearranged for power:
    P = Qe * (a0 + a1*(Tcond/Qe) + a2*(Tevap/(Qe*Tcond)))

Where:
    P = Power (kW)
    Qe = Cooling load (kW thermal)
    Tcond = Condenser temperature (K)
    Tevap = Evaporator temperature (K)
    a0, a1, a2 = Fitted coefficients
"""

import numpy as np
from scipy.optimize import curve_fit
from typing import Any, Dict, Tuple

try:
    import pandas as pd

    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

from app.ml.models.base import BaseChillerModel


class GordonNgModel(BaseChillerModel):
    """Gordon-Ng semi-empirical model for chiller power prediction.

    Inputs:
        - cooling_load (RT) - Cooling load in refrigeration tons
        - evap_temp (°F) - Evaporator/chilled water temperature
        - cond_temp (°F) - Condenser water temperature

    Output:
        - power (kW) - Predicted power consumption
    """

    MODEL_TYPE = "gordon_ng"

    # Conversion constants
    RT_TO_KW = 3.517  # 1 RT = 3.517 kW (thermal)

    def __init__(self, site_id: str, equipment_id: str):
        super().__init__(site_id, equipment_id)
        self.a0: float = 0.0
        self.a1: float = 0.0
        self.a2: float = 0.0
        self._covariance: np.ndarray = None

    @staticmethod
    def _f_to_kelvin(temp_f: float) -> float:
        """Convert Fahrenheit to Kelvin."""
        return (temp_f + 459.67) * 5 / 9

    @staticmethod
    def _gordon_ng_equation(
        X: Tuple[np.ndarray, np.ndarray, np.ndarray],
        a0: float,
        a1: float,
        a2: float,
    ) -> np.ndarray:
        """Gordon-Ng model equation.

        Args:
            X: Tuple of (Qe_kw, Tcond_K, Tevap_K)
            a0, a1, a2: Model coefficients

        Returns:
            Predicted power (kW)
        """
        Qe_kw, Tcond_K, Tevap_K = X

        # Avoid division by zero
        Qe_kw = np.maximum(Qe_kw, 1e-6)

        # Gordon-Ng: P = Qe * (a0 + a1*(Tcond/Qe) + a2*(Tevap/(Qe*Tcond)))
        term1 = a0
        term2 = a1 * (Tcond_K / Qe_kw)
        term3 = a2 * (Tevap_K / (Qe_kw * Tcond_K))

        return Qe_kw * (term1 + term2 + term3)

    def fit(
        self,
        df: Any,
        cooling_load_col: str = "cooling_load",  # RT
        power_col: str = "power",  # kW
        evap_temp_col: str = "evap_lwt",  # F
        cond_temp_col: str = "cond_ewt",  # F
        **kwargs,
    ) -> "GordonNgModel":
        """Fit the Gordon-Ng model to training data.

        Args:
            df: DataFrame with training data
            cooling_load_col: Column name for cooling load (RT)
            power_col: Column name for power (kW)
            evap_temp_col: Column name for evaporator temperature (°F)
            cond_temp_col: Column name for condenser temperature (°F)

        Returns:
            Self for method chaining
        """
        # Extract and convert data
        Qe_rt = df[cooling_load_col].values
        Qe_kw = Qe_rt * self.RT_TO_KW
        P_actual = df[power_col].values
        Tevap_K = np.array([self._f_to_kelvin(t) for t in df[evap_temp_col].values])
        Tcond_K = np.array([self._f_to_kelvin(t) for t in df[cond_temp_col].values])

        # Prepare data for curve fitting
        X_data = (Qe_kw, Tcond_K, Tevap_K)

        # Initial guesses based on typical chiller behavior
        p0 = [0.15, 50.0, 50.0]
        bounds = (
            [0.0, 0.0, 0.0],  # Lower bounds
            [1.0, 500.0, 500.0],  # Upper bounds
        )

        try:
            popt, pcov = curve_fit(
                self._gordon_ng_equation,
                X_data,
                P_actual,
                p0=p0,
                bounds=bounds,
                maxfev=5000,
            )

            self.a0, self.a1, self.a2 = popt
            self._covariance = pcov
            self._is_fitted = True

        except Exception as e:
            raise RuntimeError(f"Failed to fit Gordon-Ng model: {e}")

        return self

    def predict(
        self,
        cooling_load_rt: np.ndarray,
        evap_temp_f: np.ndarray,
        cond_temp_f: np.ndarray,
    ) -> np.ndarray:
        """Predict chiller power.

        Args:
            cooling_load_rt: Cooling load in RT
            evap_temp_f: Evaporator temperature in °F
            cond_temp_f: Condenser temperature in °F

        Returns:
            Predicted power in kW
        """
        self.validate_input()

        Qe_kw = np.asarray(cooling_load_rt) * self.RT_TO_KW
        Tevap_K = np.array([self._f_to_kelvin(t) for t in np.asarray(evap_temp_f)])
        Tcond_K = np.array([self._f_to_kelvin(t) for t in np.asarray(cond_temp_f)])

        X_data = (Qe_kw, Tcond_K, Tevap_K)

        return self._gordon_ng_equation(X_data, self.a0, self.a1, self.a2)

    def predict_efficiency(
        self,
        cooling_load_rt: np.ndarray,
        evap_temp_f: np.ndarray,
        cond_temp_f: np.ndarray,
    ) -> np.ndarray:
        """Predict efficiency (kW/RT).

        Args:
            cooling_load_rt: Cooling load in RT
            evap_temp_f: Evaporator temperature in °F
            cond_temp_f: Condenser temperature in °F

        Returns:
            Predicted efficiency in kW/RT
        """
        power = self.predict(cooling_load_rt, evap_temp_f, cond_temp_f)
        return power / np.asarray(cooling_load_rt)

    def get_parameters(self) -> Dict[str, Any]:
        """Get model parameters for storage."""
        return {
            "a0": float(self.a0),
            "a1": float(self.a1),
            "a2": float(self.a2),
        }

    def set_parameters(self, params: Dict[str, Any]) -> None:
        """Load model parameters."""
        self.a0 = params["a0"]
        self.a1 = params["a1"]
        self.a2 = params["a2"]
        self._is_fitted = True

    def calculate_metrics(
        self,
        df: Any,
        cooling_load_col: str = "cooling_load",
        power_col: str = "power",
        evap_temp_col: str = "evap_lwt",
        cond_temp_col: str = "cond_ewt",
        **kwargs,
    ) -> Dict[str, float]:
        """Calculate model performance metrics.

        Args:
            df: Validation DataFrame
            cooling_load_col: Column for cooling load (RT)
            power_col: Column for actual power (kW)
            evap_temp_col: Column for evaporator temperature (°F)
            cond_temp_col: Column for condenser temperature (°F)

        Returns:
            Dictionary with r2, mae, rmse, mape, n_samples
        """
        y_true = df[power_col].values
        y_pred = self.predict(
            df[cooling_load_col].values,
            df[evap_temp_col].values,
            df[cond_temp_col].values,
        )

        # Calculate metrics
        residuals = y_true - y_pred
        mae = np.mean(np.abs(residuals))
        rmse = np.sqrt(np.mean(residuals**2))

        # Avoid division by zero in MAPE
        nonzero_mask = y_true != 0
        if nonzero_mask.any():
            mape = np.mean(np.abs(residuals[nonzero_mask] / y_true[nonzero_mask])) * 100
        else:
            mape = 0.0

        # R-squared
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        return {
            "r2": float(r2),
            "mae": float(mae),
            "rmse": float(rmse),
            "mape": float(mape),
            "n_samples": len(y_true),
        }
