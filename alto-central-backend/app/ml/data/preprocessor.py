"""Data preprocessing for ML training.

Handles data cleaning, validation, and feature engineering.
"""

import logging
from typing import Any, Dict, Tuple

try:
    import pandas as pd
    import numpy as np

    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

logger = logging.getLogger(__name__)


class ChillerDataPreprocessor:
    """Preprocess chiller data for ML training.

    Handles:
    - Filtering to running periods
    - Removing invalid/missing data
    - Outlier detection
    - Data validation
    """

    # Validation thresholds
    MIN_POWER_KW = 10.0  # Minimum meaningful power
    MIN_COOLING_LOAD_RT = 10.0  # Minimum meaningful cooling load
    MAX_POWER_KW = 2000.0  # Sanity check maximum
    MIN_RLA_PERCENT = 5.0  # Minimum meaningful RLA
    MAX_RLA_PERCENT = 120.0  # Maximum RLA (can exceed 100% briefly)
    TEMP_MIN_F = 30.0  # Minimum reasonable temperature
    TEMP_MAX_F = 120.0  # Maximum reasonable temperature

    def preprocess_for_gordon_ng(
        self,
        df: "pd.DataFrame",
        min_samples: int = 100,
        power_col: str = "power",
        cooling_load_col: str = "cooling_load",
        evap_temp_col: str = "evap_lwt",
        cond_temp_col: str = "cond_ewt",
        status_col: str = "status",
    ) -> Tuple["pd.DataFrame", Dict[str, Any]]:
        """Preprocess data for Gordon-Ng model training.

        Args:
            df: Raw training DataFrame
            min_samples: Minimum required samples after preprocessing
            power_col: Column name for power
            cooling_load_col: Column name for cooling load
            evap_temp_col: Column name for evaporator temperature
            cond_temp_col: Column name for condenser temperature
            status_col: Column name for chiller status

        Returns:
            Tuple of (cleaned_df, stats_dict)

        Raises:
            ValueError: If insufficient data after preprocessing
        """
        if not HAS_PANDAS:
            raise ImportError("pandas is required for preprocessing")

        stats = {
            "original_rows": len(df),
            "removed_offline": 0,
            "removed_invalid": 0,
            "removed_outliers": 0,
            "final_rows": 0,
        }

        df = df.copy()

        # Filter to only when chiller is running
        if status_col in df.columns:
            before = len(df)
            df = df[df[status_col] >= 1]
            stats["removed_offline"] = before - len(df)

        # Remove rows with missing required values
        required_cols = [power_col, cooling_load_col, evap_temp_col, cond_temp_col]
        existing_cols = [c for c in required_cols if c in df.columns]

        before = len(df)
        df = df.dropna(subset=existing_cols)
        stats["removed_invalid"] = before - len(df)

        # Apply sanity checks
        before = len(df)
        conditions = []

        if power_col in df.columns:
            conditions.append(df[power_col] >= self.MIN_POWER_KW)
            conditions.append(df[power_col] <= self.MAX_POWER_KW)

        if cooling_load_col in df.columns:
            conditions.append(df[cooling_load_col] >= self.MIN_COOLING_LOAD_RT)

        if evap_temp_col in df.columns:
            conditions.append(df[evap_temp_col] >= self.TEMP_MIN_F)
            conditions.append(df[evap_temp_col] <= self.TEMP_MAX_F)

        if cond_temp_col in df.columns:
            conditions.append(df[cond_temp_col] >= self.TEMP_MIN_F)
            conditions.append(df[cond_temp_col] <= self.TEMP_MAX_F)

        if conditions:
            combined_condition = conditions[0]
            for cond in conditions[1:]:
                combined_condition = combined_condition & cond
            df = df[combined_condition]

        stats["removed_outliers"] = before - len(df)
        stats["final_rows"] = len(df)

        if len(df) < min_samples:
            raise ValueError(
                f"Insufficient data: {len(df)} samples < {min_samples} minimum. "
                f"Stats: {stats}"
            )

        logger.info(
            f"Preprocessed Gordon-Ng data: {stats['original_rows']} -> "
            f"{stats['final_rows']} rows"
        )

        return df, stats

    def preprocess_for_rla_regression(
        self,
        df: "pd.DataFrame",
        min_samples: int = 50,
        rla_col: str = "percentage_rla",
        power_col: str = "power",
        status_col: str = "status",
    ) -> Tuple["pd.DataFrame", Dict[str, Any]]:
        """Preprocess data for RLA-to-Power regression.

        Args:
            df: Raw training DataFrame
            min_samples: Minimum required samples
            rla_col: Column name for RLA percentage
            power_col: Column name for power
            status_col: Column name for status

        Returns:
            Tuple of (cleaned_df, stats_dict)

        Raises:
            ValueError: If insufficient data
        """
        if not HAS_PANDAS:
            raise ImportError("pandas is required for preprocessing")

        stats = {
            "original_rows": len(df),
            "removed_offline": 0,
            "removed_invalid": 0,
            "removed_outliers": 0,
            "final_rows": 0,
        }

        df = df.copy()

        # Filter to only when chiller is running
        if status_col in df.columns:
            before = len(df)
            df = df[df[status_col] >= 1]
            stats["removed_offline"] = before - len(df)

        # Remove rows with missing required values
        required_cols = [rla_col, power_col]
        existing_cols = [c for c in required_cols if c in df.columns]

        before = len(df)
        df = df.dropna(subset=existing_cols)
        stats["removed_invalid"] = before - len(df)

        # Apply sanity checks
        before = len(df)
        conditions = []

        if rla_col in df.columns:
            conditions.append(df[rla_col] >= self.MIN_RLA_PERCENT)
            conditions.append(df[rla_col] <= self.MAX_RLA_PERCENT)

        if power_col in df.columns:
            conditions.append(df[power_col] >= self.MIN_POWER_KW)
            conditions.append(df[power_col] <= self.MAX_POWER_KW)

        if conditions:
            combined_condition = conditions[0]
            for cond in conditions[1:]:
                combined_condition = combined_condition & cond
            df = df[combined_condition]

        stats["removed_outliers"] = before - len(df)
        stats["final_rows"] = len(df)

        if len(df) < min_samples:
            raise ValueError(
                f"Insufficient data: {len(df)} samples < {min_samples} minimum. "
                f"Stats: {stats}"
            )

        logger.info(
            f"Preprocessed RLA data: {stats['original_rows']} -> "
            f"{stats['final_rows']} rows"
        )

        return df, stats

    def remove_outliers_iqr(
        self,
        df: "pd.DataFrame",
        columns: list,
        multiplier: float = 1.5,
    ) -> "pd.DataFrame":
        """Remove outliers using IQR method.

        Args:
            df: DataFrame to filter
            columns: Columns to check for outliers
            multiplier: IQR multiplier (default: 1.5)

        Returns:
            Filtered DataFrame
        """
        if not HAS_PANDAS:
            raise ImportError("pandas is required")

        df = df.copy()

        for col in columns:
            if col not in df.columns:
                continue

            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1

            lower = Q1 - multiplier * IQR
            upper = Q3 + multiplier * IQR

            df = df[(df[col] >= lower) & (df[col] <= upper)]

        return df
