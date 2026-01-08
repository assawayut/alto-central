"""RLA to Power regression model.

Simple polynomial regression model that maps percentage RLA (Running Load Amps)
to power consumption (kW).

Model:
    P = a + b*RLA + c*RLA^2 + ...

Can optionally include temperature as an additional feature for better accuracy.
"""

import numpy as np
from typing import Any, Dict, Optional

try:
    from sklearn.preprocessing import PolynomialFeatures
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import Pipeline

    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

from app.ml.models.base import BaseChillerModel


class RLARegressionModel(BaseChillerModel):
    """Simple regression model for RLA to Power mapping.

    Maps percentage_rla (%) → power (kW) using polynomial regression.
    Can optionally include temperature as additional feature.

    Inputs:
        - percentage_rla (%) - Running Load Amps percentage
        - temperature (°F, optional) - Condenser temperature

    Output:
        - power (kW) - Predicted power consumption
    """

    MODEL_TYPE = "rla_regression"

    def __init__(
        self,
        site_id: str,
        equipment_id: str,
        degree: int = 2,
        include_temperature: bool = False,
    ):
        """Initialize RLA regression model.

        Args:
            site_id: Site identifier
            equipment_id: Equipment identifier (e.g., "chiller_1")
            degree: Polynomial degree (default: 2 for quadratic)
            include_temperature: Whether to include temperature as feature
        """
        if not HAS_SKLEARN:
            raise ImportError("scikit-learn is required for RLARegressionModel")

        super().__init__(site_id, equipment_id)
        self.degree = degree
        self.include_temperature = include_temperature
        self._pipeline: Optional[Pipeline] = None
        self._feature_names: list = []
        # Store fitted attributes for reconstruction
        self._n_features_in: int = 0
        self._powers: Optional[np.ndarray] = None
        self._coef: Optional[np.ndarray] = None
        self._intercept: float = 0.0

    def fit(
        self,
        df: Any,
        rla_col: str = "percentage_rla",
        power_col: str = "power",
        temp_col: str = "cond_ewt",
        **kwargs,
    ) -> "RLARegressionModel":
        """Fit the RLA regression model.

        Args:
            df: Training DataFrame
            rla_col: Column name for RLA percentage
            power_col: Column name for power (kW)
            temp_col: Column name for temperature (optional feature)

        Returns:
            Self for method chaining
        """
        # Prepare features
        if self.include_temperature:
            X = df[[rla_col, temp_col]].values
            self._feature_names = [rla_col, temp_col]
        else:
            X = df[[rla_col]].values
            self._feature_names = [rla_col]

        y = df[power_col].values

        # Create pipeline with polynomial features and ridge regression
        self._pipeline = Pipeline(
            [
                ("poly", PolynomialFeatures(degree=self.degree, include_bias=True)),
                ("ridge", Ridge(alpha=1.0)),
            ]
        )

        self._pipeline.fit(X, y)

        # Store fitted attributes for serialization
        self._n_features_in = X.shape[1]
        self._powers = self._pipeline.named_steps["poly"].powers_.copy()
        self._coef = self._pipeline.named_steps["ridge"].coef_.copy()
        self._intercept = float(self._pipeline.named_steps["ridge"].intercept_)

        self._is_fitted = True

        return self

    def predict(
        self,
        percentage_rla: np.ndarray,
        temperature: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Predict power from RLA.

        Args:
            percentage_rla: RLA percentage values
            temperature: Optional temperature values (if model uses temperature)

        Returns:
            Predicted power in kW
        """
        self.validate_input()

        rla = np.asarray(percentage_rla).reshape(-1, 1)

        if self.include_temperature:
            if temperature is None:
                raise ValueError("Temperature required for this model")
            temp = np.asarray(temperature).reshape(-1, 1)
            X = np.hstack([rla, temp])
        else:
            X = rla

        return self._pipeline.predict(X)

    def get_parameters(self) -> Dict[str, Any]:
        """Get model parameters for storage."""
        return {
            "degree": self.degree,
            "include_temperature": self.include_temperature,
            "feature_names": self._feature_names,
            "n_features_in": self._n_features_in,
            "powers": self._powers.tolist() if self._powers is not None else [],
            "coefficients": self._coef.tolist() if self._coef is not None else [],
            "intercept": self._intercept,
        }

    def set_parameters(self, params: Dict[str, Any]) -> None:
        """Load model parameters."""
        self.degree = params["degree"]
        self.include_temperature = params["include_temperature"]
        self._feature_names = params["feature_names"]
        self._n_features_in = params["n_features_in"]
        self._powers = np.array(params["powers"])
        self._coef = np.array(params["coefficients"])
        self._intercept = params["intercept"]

        # Reconstruct pipeline
        self._pipeline = Pipeline(
            [
                ("poly", PolynomialFeatures(degree=self.degree, include_bias=True)),
                ("ridge", Ridge(alpha=1.0)),
            ]
        )

        # Set fitted attributes on the polynomial features
        poly = self._pipeline.named_steps["poly"]
        poly.n_features_in_ = self._n_features_in
        poly.powers_ = self._powers
        poly._n_out_full = len(self._powers)

        # Set fitted attributes on ridge
        ridge = self._pipeline.named_steps["ridge"]
        ridge.coef_ = self._coef
        ridge.intercept_ = self._intercept
        ridge.n_features_in_ = len(self._powers)

        self._is_fitted = True

    def calculate_metrics(
        self,
        df: Any,
        rla_col: str = "percentage_rla",
        power_col: str = "power",
        temp_col: str = "cond_ewt",
        **kwargs,
    ) -> Dict[str, float]:
        """Calculate model performance metrics.

        Args:
            df: Validation DataFrame
            rla_col: Column for RLA percentage
            power_col: Column for actual power (kW)
            temp_col: Column for temperature (if used)

        Returns:
            Dictionary with r2, mae, rmse, n_samples
        """
        y_true = df[power_col].values

        if self.include_temperature:
            y_pred = self.predict(df[rla_col].values, df[temp_col].values)
        else:
            y_pred = self.predict(df[rla_col].values)

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
