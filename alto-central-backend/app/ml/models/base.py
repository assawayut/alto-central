"""Base model classes for ML module.

Provides abstract base class for all chiller models and metadata structure.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ModelMetadata:
    """Metadata for a trained model."""

    model_id: str
    model_type: str  # "gordon_ng", "rla_regression", etc.
    version: str  # Semantic versioning: "1.0.0"
    site_id: str
    equipment_id: str  # "chiller_1" or "chiller_1+chiller_2" for combinations
    created_at: datetime
    trained_at: datetime
    training_data_start: datetime
    training_data_end: datetime
    training_samples: int
    parameters: Dict[str, Any]  # Model-specific parameters
    metrics: Dict[str, float]  # R2, MAE, RMSE, etc.
    status: str = "trained"  # "trained", "deployed", "archived"
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "model_id": self.model_id,
            "model_type": self.model_type,
            "version": self.version,
            "site_id": self.site_id,
            "equipment_id": self.equipment_id,
            "created_at": self.created_at.isoformat(),
            "trained_at": self.trained_at.isoformat(),
            "training_data_start": self.training_data_start.isoformat(),
            "training_data_end": self.training_data_end.isoformat(),
            "training_samples": self.training_samples,
            "parameters": self.parameters,
            "metrics": self.metrics,
            "status": self.status,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelMetadata":
        """Create from dictionary."""
        data = data.copy()
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["trained_at"] = datetime.fromisoformat(data["trained_at"])
        data["training_data_start"] = datetime.fromisoformat(data["training_data_start"])
        data["training_data_end"] = datetime.fromisoformat(data["training_data_end"])
        return cls(**data)


class BaseChillerModel(ABC):
    """Abstract base class for chiller power prediction models."""

    MODEL_TYPE: str = "base"

    def __init__(self, site_id: str, equipment_id: str):
        self.site_id = site_id
        self.equipment_id = equipment_id
        self.metadata: Optional[ModelMetadata] = None
        self._is_fitted = False

    @abstractmethod
    def fit(self, df: Any, **kwargs) -> "BaseChillerModel":
        """Train the model on data.

        Args:
            df: Training data (pandas DataFrame)
            **kwargs: Model-specific training parameters

        Returns:
            Self for method chaining
        """
        pass

    @abstractmethod
    def predict(self, *args, **kwargs) -> Any:
        """Make predictions.

        Returns:
            Predicted values (numpy array)
        """
        pass

    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """Get model parameters for storage.

        Returns:
            Dictionary of model parameters
        """
        pass

    @abstractmethod
    def set_parameters(self, params: Dict[str, Any]) -> None:
        """Set model parameters from storage.

        Args:
            params: Dictionary of model parameters
        """
        pass

    @abstractmethod
    def calculate_metrics(self, df: Any, **kwargs) -> Dict[str, float]:
        """Calculate model performance metrics.

        Args:
            df: Validation data

        Returns:
            Dictionary of metrics (r2, mae, rmse, etc.)
        """
        pass

    @property
    def is_fitted(self) -> bool:
        """Check if model has been trained."""
        return self._is_fitted

    def validate_input(self) -> None:
        """Validate that model is ready for prediction."""
        if not self._is_fitted:
            raise ValueError("Model has not been fitted yet")
