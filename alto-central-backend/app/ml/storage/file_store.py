"""File-based model storage.

Stores trained models as pickle files with JSON metadata.

Directory structure:
    models/
    └── [site_id]/
        └── [model_type]/
            └── [equipment_id]/
                ├── v1.0.0.pkl
                ├── v1.0.0_metadata.json
                └── latest.json
"""

import json
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.ml.models.base import ModelMetadata


class FileModelStore:
    """File-based model storage.

    Stores model parameters as pickle files and metadata as JSON.
    Supports versioning and easy retrieval of latest model.
    """

    def __init__(self, base_path: str = "models"):
        """Initialize file store.

        Args:
            base_path: Base directory for model storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_model_dir(
        self,
        site_id: str,
        model_type: str,
        equipment_id: str,
    ) -> Path:
        """Get directory for a specific model.

        Args:
            site_id: Site identifier
            model_type: Model type (e.g., "gordon_ng")
            equipment_id: Equipment identifier

        Returns:
            Path to model directory
        """
        # Sanitize equipment_id for filesystem (replace + with _plus_)
        safe_equipment_id = equipment_id.replace("+", "_plus_")
        path = self.base_path / site_id / model_type / safe_equipment_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_model(
        self,
        parameters: Dict[str, Any],
        metadata: ModelMetadata,
    ) -> str:
        """Save model parameters and metadata to files.

        Args:
            parameters: Model parameters dictionary
            metadata: Model metadata

        Returns:
            Path to saved model file
        """
        model_dir = self._get_model_dir(
            metadata.site_id,
            metadata.model_type,
            metadata.equipment_id,
        )

        version = metadata.version

        # Save model parameters as pickle
        model_path = model_dir / f"v{version}.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(parameters, f)

        # Save metadata as JSON
        metadata_path = model_dir / f"v{version}_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata.to_dict(), f, indent=2)

        # Update latest pointer
        latest_path = model_dir / "latest.json"
        with open(latest_path, "w") as f:
            json.dump(
                {
                    "version": version,
                    "model_id": metadata.model_id,
                    "path": str(model_path),
                },
                f,
            )

        return str(model_path)

    def load_model(
        self,
        site_id: str,
        model_type: str,
        equipment_id: str,
        version: Optional[str] = None,
    ) -> tuple[Dict[str, Any], ModelMetadata]:
        """Load model parameters and metadata.

        Args:
            site_id: Site identifier
            model_type: Model type
            equipment_id: Equipment identifier
            version: Version to load (None = latest)

        Returns:
            Tuple of (parameters_dict, metadata)

        Raises:
            FileNotFoundError: If model not found
        """
        model_dir = self._get_model_dir(site_id, model_type, equipment_id)

        if version is None:
            # Load latest
            latest_path = model_dir / "latest.json"
            if not latest_path.exists():
                raise FileNotFoundError(
                    f"No model found for {site_id}/{model_type}/{equipment_id}"
                )
            with open(latest_path) as f:
                latest = json.load(f)
            version = latest["version"]

        # Load parameters
        model_path = model_dir / f"v{version}.pkl"
        if not model_path.exists():
            raise FileNotFoundError(f"Model version {version} not found")

        with open(model_path, "rb") as f:
            parameters = pickle.load(f)

        # Load metadata
        metadata_path = model_dir / f"v{version}_metadata.json"
        with open(metadata_path) as f:
            metadata = ModelMetadata.from_dict(json.load(f))

        return parameters, metadata

    def list_models(
        self,
        site_id: Optional[str] = None,
        model_type: Optional[str] = None,
    ) -> List[ModelMetadata]:
        """List all available models with optional filtering.

        Args:
            site_id: Filter by site (optional)
            model_type: Filter by model type (optional)

        Returns:
            List of ModelMetadata objects
        """
        results = []

        search_path = self.base_path
        if site_id:
            search_path = search_path / site_id
            if not search_path.exists():
                return results
            if model_type:
                search_path = search_path / model_type
                if not search_path.exists():
                    return results

        # Find all latest.json files and load their metadata
        for latest_file in search_path.rglob("latest.json"):
            try:
                with open(latest_file) as f:
                    latest = json.load(f)

                version = latest["version"]
                metadata_path = latest_file.parent / f"v{version}_metadata.json"

                if metadata_path.exists():
                    with open(metadata_path) as f:
                        metadata = ModelMetadata.from_dict(json.load(f))
                    results.append(metadata)
            except Exception:
                # Skip corrupted files
                continue

        return results

    def get_versions(
        self,
        site_id: str,
        model_type: str,
        equipment_id: str,
    ) -> List[str]:
        """Get all versions for a specific model.

        Args:
            site_id: Site identifier
            model_type: Model type
            equipment_id: Equipment identifier

        Returns:
            List of version strings (sorted)
        """
        model_dir = self._get_model_dir(site_id, model_type, equipment_id)

        versions = []
        for pkl_file in model_dir.glob("v*.pkl"):
            # Extract version from filename (v1.0.0.pkl -> 1.0.0)
            version = pkl_file.stem[1:]  # Remove 'v' prefix
            versions.append(version)

        return sorted(versions)

    def delete_model(
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
            True if deleted, False if not found
        """
        model_dir = self._get_model_dir(site_id, model_type, equipment_id)

        model_path = model_dir / f"v{version}.pkl"
        metadata_path = model_dir / f"v{version}_metadata.json"

        deleted = False

        if model_path.exists():
            model_path.unlink()
            deleted = True

        if metadata_path.exists():
            metadata_path.unlink()
            deleted = True

        # Update latest pointer if we deleted the latest
        latest_path = model_dir / "latest.json"
        if latest_path.exists():
            with open(latest_path) as f:
                latest = json.load(f)
            if latest["version"] == version:
                # Find the next latest version
                remaining_versions = self.get_versions(site_id, model_type, equipment_id)
                if remaining_versions:
                    new_latest = remaining_versions[-1]
                    with open(latest_path, "w") as f:
                        json.dump({"version": new_latest}, f)
                else:
                    latest_path.unlink()

        return deleted
