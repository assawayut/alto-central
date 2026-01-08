"""Model registry for ML module.

Central registry for managing ML models with caching support.
"""

import logging
from typing import Dict, List, Optional, Type

from app.ml.models.base import BaseChillerModel, ModelMetadata
from app.ml.models.gordon_ng import GordonNgModel
from app.ml.models.rla_regression import RLARegressionModel
from app.ml.storage.file_store import FileModelStore

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Central registry for ML models.

    Handles:
    - Model storage and retrieval
    - Version management
    - Model caching for fast inference
    """

    MODEL_CLASSES: Dict[str, Type[BaseChillerModel]] = {
        "gordon_ng": GordonNgModel,
        "rla_regression": RLARegressionModel,
    }

    def __init__(self, store: Optional[FileModelStore] = None):
        """Initialize model registry.

        Args:
            store: File store instance (created if not provided)
        """
        self.store = store or FileModelStore()
        self._model_cache: Dict[str, BaseChillerModel] = {}

    async def save_model(
        self,
        model: BaseChillerModel,
        metadata: ModelMetadata,
    ) -> str:
        """Save a trained model.

        Args:
            model: Trained model instance
            metadata: Model metadata

        Returns:
            Path to saved model file
        """
        parameters = model.get_parameters()
        path = self.store.save_model(parameters, metadata)

        # Update cache
        cache_key = self._get_cache_key(
            metadata.site_id,
            metadata.model_type,
            metadata.equipment_id,
        )
        model.metadata = metadata
        self._model_cache[cache_key] = model

        logger.info(f"Saved model {metadata.model_id} to {path}")
        return path

    async def load_model(
        self,
        site_id: str,
        model_type: str,
        equipment_id: str,
        version: Optional[str] = None,
        use_cache: bool = True,
    ) -> BaseChillerModel:
        """Load a model (from cache if available).

        Args:
            site_id: Site identifier
            model_type: Model type
            equipment_id: Equipment identifier
            version: Specific version (None = latest)
            use_cache: Whether to use cached model (only for latest)

        Returns:
            Loaded model instance

        Raises:
            FileNotFoundError: If model not found
            ValueError: If unknown model type
        """
        cache_key = self._get_cache_key(site_id, model_type, equipment_id)

        # Check cache (only for latest version)
        if use_cache and version is None and cache_key in self._model_cache:
            logger.debug(f"Returning cached model for {cache_key}")
            return self._model_cache[cache_key]

        # Load from storage
        parameters, metadata = self.store.load_model(
            site_id, model_type, equipment_id, version
        )

        # Instantiate model
        model_class = self.MODEL_CLASSES.get(model_type)
        if model_class is None:
            raise ValueError(f"Unknown model type: {model_type}")

        # Create model with appropriate constructor args
        if model_type == "rla_regression":
            model = model_class(
                site_id,
                equipment_id,
                degree=parameters.get("degree", 2),
                include_temperature=parameters.get("include_temperature", False),
            )
        else:
            model = model_class(site_id, equipment_id)

        model.set_parameters(parameters)
        model.metadata = metadata

        # Cache if latest version
        if version is None:
            self._model_cache[cache_key] = model

        logger.debug(f"Loaded model {metadata.model_id}")
        return model

    async def get_model_versions(
        self,
        site_id: str,
        model_type: str,
        equipment_id: str,
    ) -> List[str]:
        """Get all versions for a model.

        Args:
            site_id: Site identifier
            model_type: Model type
            equipment_id: Equipment identifier

        Returns:
            List of version strings
        """
        return self.store.get_versions(site_id, model_type, equipment_id)

    async def list_models(
        self,
        site_id: Optional[str] = None,
        model_type: Optional[str] = None,
    ) -> List[ModelMetadata]:
        """List all models with optional filtering.

        Args:
            site_id: Filter by site
            model_type: Filter by model type

        Returns:
            List of ModelMetadata objects
        """
        return self.store.list_models(site_id, model_type)

    async def delete_model(
        self,
        site_id: str,
        model_type: str,
        equipment_id: str,
        version: str,
    ) -> bool:
        """Delete a specific model version.

        Args:
            site_id: Site identifier
            model_type: Model type
            equipment_id: Equipment identifier
            version: Version to delete

        Returns:
            True if deleted
        """
        # Clear from cache
        cache_key = self._get_cache_key(site_id, model_type, equipment_id)
        if cache_key in self._model_cache:
            del self._model_cache[cache_key]

        return self.store.delete_model(site_id, model_type, equipment_id, version)

    def _get_cache_key(
        self,
        site_id: str,
        model_type: str,
        equipment_id: str,
    ) -> str:
        """Generate cache key for a model."""
        return f"{site_id}:{model_type}:{equipment_id}"

    def clear_cache(self, site_id: Optional[str] = None) -> None:
        """Clear model cache.

        Args:
            site_id: Clear only for specific site (None = all)
        """
        if site_id:
            keys_to_remove = [
                k for k in self._model_cache if k.startswith(f"{site_id}:")
            ]
            for k in keys_to_remove:
                del self._model_cache[k]
        else:
            self._model_cache.clear()

        logger.info(f"Cleared model cache for site={site_id or 'all'}")


# Global registry instance
_registry: Optional[ModelRegistry] = None


def get_model_registry() -> ModelRegistry:
    """Get the global model registry instance."""
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry
