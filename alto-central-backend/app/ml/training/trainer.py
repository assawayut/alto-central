"""Model training orchestrator.

Coordinates data fetching, preprocessing, model training, and storage.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Type

from app.ml.models.base import BaseChillerModel, ModelMetadata
from app.ml.models.gordon_ng import GordonNgModel
from app.ml.models.rla_regression import RLARegressionModel
from app.ml.data.fetcher import MLDataFetcher
from app.ml.data.preprocessor import ChillerDataPreprocessor
from app.ml.storage.registry import ModelRegistry

logger = logging.getLogger(__name__)


class ModelTrainer:
    """Orchestrates model training.

    Handles the complete training pipeline:
    1. Fetch data from TimescaleDB
    2. Preprocess data
    3. Train model
    4. Calculate metrics
    5. Save to registry
    """

    MODEL_CLASSES: Dict[str, Type[BaseChillerModel]] = {
        "gordon_ng": GordonNgModel,
        "rla_regression": RLARegressionModel,
    }

    def __init__(self, registry: ModelRegistry):
        """Initialize trainer.

        Args:
            registry: Model registry for storage
        """
        self.registry = registry
        self.preprocessor = ChillerDataPreprocessor()

    async def train_model(
        self,
        site_id: str,
        model_type: str,
        equipment_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        training_params: Optional[Dict] = None,
    ) -> ModelMetadata:
        """Train a model for a specific equipment.

        Args:
            site_id: Site identifier
            model_type: "gordon_ng" or "rla_regression"
            equipment_id: Chiller ID (e.g., "chiller_1") or combination
                         (e.g., "chiller_1+chiller_2")
            start_date: Training data start (default: 6 months ago)
            end_date: Training data end (default: now)
            training_params: Model-specific training parameters

        Returns:
            ModelMetadata for the trained model

        Raises:
            ValueError: If unknown model type or insufficient data
        """
        # Default date range
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=180)

        training_params = training_params or {}

        # Get model class
        model_class = self.MODEL_CLASSES.get(model_type)
        if model_class is None:
            raise ValueError(f"Unknown model type: {model_type}")

        # Fetch training data
        fetcher = MLDataFetcher(site_id)

        if "+" in equipment_id:
            # Combination model
            chiller_ids = equipment_id.split("+")
            raw_data = await fetcher.fetch_combination_training_data(
                chiller_ids, start_date, end_date
            )
            if raw_data.empty:
                raise ValueError(
                    f"No data found for combination {equipment_id} "
                    f"between {start_date} and {end_date}"
                )
        else:
            # Single chiller model
            chiller_data = await fetcher.fetch_chiller_training_data(
                equipment_id, start_date, end_date
            )
            raw_data = chiller_data.to_dataframe()

        logger.info(
            f"Fetched {len(raw_data)} rows for {site_id}/{equipment_id}"
        )

        # Preprocess data
        if model_type == "gordon_ng":
            df, preprocess_stats = self.preprocessor.preprocess_for_gordon_ng(
                raw_data
            )
        else:
            df, preprocess_stats = self.preprocessor.preprocess_for_rla_regression(
                raw_data
            )

        logger.info(
            f"After preprocessing: {preprocess_stats['final_rows']} rows "
            f"(removed: offline={preprocess_stats['removed_offline']}, "
            f"invalid={preprocess_stats['removed_invalid']}, "
            f"outliers={preprocess_stats['removed_outliers']})"
        )

        # Create and train model
        if model_type == "rla_regression":
            model = model_class(
                site_id,
                equipment_id,
                degree=training_params.get("degree", 2),
                include_temperature=training_params.get("include_temperature", False),
            )
        else:
            model = model_class(site_id, equipment_id)

        model.fit(df, **training_params)

        # Calculate metrics
        metrics = model.calculate_metrics(df)

        logger.info(
            f"Trained {model_type} for {equipment_id}: "
            f"R²={metrics['r2']:.4f}, MAE={metrics['mae']:.2f}, RMSE={metrics['rmse']:.2f}"
        )

        # Generate version
        existing_versions = await self.registry.get_model_versions(
            site_id, model_type, equipment_id
        )
        new_version = self._get_next_version(existing_versions)

        # Create metadata
        safe_equipment_id = equipment_id.replace("+", "_")
        model_id = f"{site_id}_{model_type}_{safe_equipment_id}_{new_version}"

        metadata = ModelMetadata(
            model_id=model_id,
            model_type=model_type,
            version=new_version,
            site_id=site_id,
            equipment_id=equipment_id,
            created_at=datetime.utcnow(),
            trained_at=datetime.utcnow(),
            training_data_start=start_date,
            training_data_end=end_date,
            training_samples=len(df),
            parameters=model.get_parameters(),
            metrics=metrics,
            status="trained",
            tags=[f"auto_trained_{datetime.utcnow().strftime('%Y%m%d')}"],
        )

        model.metadata = metadata

        # Save model
        await self.registry.save_model(model, metadata)

        return metadata

    async def train_all_chillers(
        self,
        site_id: str,
        model_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **kwargs,
    ) -> List[ModelMetadata]:
        """Train models for all chillers at a site.

        Args:
            site_id: Site identifier
            model_type: Model type to train
            start_date: Training data start
            end_date: Training data end
            **kwargs: Additional training parameters

        Returns:
            List of ModelMetadata for successfully trained models
        """
        fetcher = MLDataFetcher(site_id)
        chillers = await fetcher.get_available_chillers()

        logger.info(f"Training {model_type} for {len(chillers)} chillers at {site_id}")

        results = []
        for chiller_id in chillers:
            try:
                metadata = await self.train_model(
                    site_id,
                    model_type,
                    chiller_id,
                    start_date=start_date,
                    end_date=end_date,
                    training_params=kwargs,
                )
                results.append(metadata)
                logger.info(f"Successfully trained model for {chiller_id}")
            except Exception as e:
                logger.error(f"Failed to train {model_type} for {chiller_id}: {e}")

        return results

    async def train_all_combinations(
        self,
        site_id: str,
        model_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **kwargs,
    ) -> List[ModelMetadata]:
        """Train models for all chiller combinations at a site.

        Args:
            site_id: Site identifier
            model_type: Model type to train
            start_date: Training data start
            end_date: Training data end
            **kwargs: Additional training parameters

        Returns:
            List of ModelMetadata for successfully trained models
        """
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=180)

        fetcher = MLDataFetcher(site_id)
        combinations = await fetcher.get_chiller_combinations_in_data(
            start_date, end_date
        )

        logger.info(
            f"Training {model_type} for {len(combinations)} combinations at {site_id}"
        )

        results = []
        for combo in combinations:
            if len(combo) < 2:
                # Skip single chillers (handled by train_all_chillers)
                continue

            equipment_id = "+".join(combo)
            try:
                metadata = await self.train_model(
                    site_id,
                    model_type,
                    equipment_id,
                    start_date=start_date,
                    end_date=end_date,
                    training_params=kwargs,
                )
                results.append(metadata)
                logger.info(f"Successfully trained model for {equipment_id}")
            except Exception as e:
                logger.error(
                    f"Failed to train {model_type} for {equipment_id}: {e}"
                )

        return results

    def _get_next_version(self, existing_versions: List[str]) -> str:
        """Calculate next semantic version.

        Args:
            existing_versions: List of existing version strings

        Returns:
            Next version string (e.g., "2.0.0")
        """
        if not existing_versions:
            return "1.0.0"

        # Parse versions and find max major
        max_major = 0
        for v in existing_versions:
            try:
                parts = v.split(".")
                major = int(parts[0])
                if major > max_major:
                    max_major = major
            except (ValueError, IndexError):
                continue

        return f"{max_major + 1}.0.0"
