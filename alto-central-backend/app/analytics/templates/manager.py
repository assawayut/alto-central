"""Template manager for file-based template storage.

Handles loading, saving, and managing chart templates from YAML files.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from app.analytics.templates.schema import ChartTemplate, TemplateListItem

logger = logging.getLogger(__name__)


class TemplateManager:
    """Manages chart templates stored as YAML files.

    Directory structure:
        templates/
        ├── builtin/          # Pre-defined templates (read-only)
        │   ├── plant_efficiency.yaml
        │   └── ...
        └── custom/           # AI/user-generated templates
            └── {site_id}/
                └── *.yaml
    """

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize template manager.

        Args:
            base_path: Base path for templates directory.
                       Defaults to project_root/templates
        """
        if base_path is None:
            # Default to app_root/templates
            # app/analytics/templates/manager.py -> /app (in Docker)
            base_path = Path(__file__).parent.parent.parent.parent / "templates"

        self.base_path = Path(base_path)
        self.builtin_path = self.base_path / "builtin"
        self.custom_path = self.base_path / "custom"

        # Ensure directories exist
        self.builtin_path.mkdir(parents=True, exist_ok=True)
        self.custom_path.mkdir(parents=True, exist_ok=True)

        # Cache for loaded templates
        self._cache: Dict[str, ChartTemplate] = {}
        self._cache_loaded = False

    def _get_site_custom_path(self, site_id: str) -> Path:
        """Get custom templates path for a site."""
        path = self.custom_path / site_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _load_template_from_file(self, file_path: Path) -> Optional[ChartTemplate]:
        """Load a template from a YAML file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data is None:
                return None

            return ChartTemplate(**data)
        except Exception as e:
            logger.error(f"Failed to load template from {file_path}: {e}")
            return None

    def _save_template_to_file(self, template: ChartTemplate, file_path: Path) -> bool:
        """Save a template to a YAML file."""
        try:
            # Convert to dict, handling datetime serialization
            data = template.model_dump(mode="json")

            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)

            return True
        except Exception as e:
            logger.error(f"Failed to save template to {file_path}: {e}")
            return False

    def load_all_templates(self, force_reload: bool = False) -> Dict[str, ChartTemplate]:
        """Load all templates (builtin + custom) into cache.

        Args:
            force_reload: Force reload even if cache exists

        Returns:
            Dict mapping template_id -> ChartTemplate
        """
        if self._cache_loaded and not force_reload:
            return self._cache

        self._cache.clear()

        # Load builtin templates
        for file_path in self.builtin_path.glob("*.yaml"):
            template = self._load_template_from_file(file_path)
            if template:
                self._cache[template.template_id] = template
                logger.debug(f"Loaded builtin template: {template.template_id}")

        # Load custom templates from all sites
        for site_dir in self.custom_path.iterdir():
            if site_dir.is_dir():
                for file_path in site_dir.glob("*.yaml"):
                    template = self._load_template_from_file(file_path)
                    if template:
                        # Prefix with site_id to avoid conflicts
                        cache_key = f"{site_dir.name}:{template.template_id}"
                        self._cache[cache_key] = template
                        logger.debug(f"Loaded custom template: {cache_key}")

        self._cache_loaded = True
        logger.info(f"Loaded {len(self._cache)} templates")
        return self._cache

    def get_template(
        self, template_id: str, site_id: Optional[str] = None
    ) -> Optional[ChartTemplate]:
        """Get a template by ID.

        First checks site-specific custom templates, then builtin.

        Args:
            template_id: Template identifier
            site_id: Optional site ID for custom templates

        Returns:
            ChartTemplate if found, None otherwise
        """
        self.load_all_templates()

        # Try site-specific custom template first
        if site_id:
            cache_key = f"{site_id}:{template_id}"
            if cache_key in self._cache:
                return self._cache[cache_key]

        # Try builtin template
        if template_id in self._cache:
            return self._cache[template_id]

        return None

    def list_templates(
        self,
        site_id: Optional[str] = None,
        category: Optional[str] = None,
        include_builtin: bool = True,
        include_custom: bool = True,
    ) -> List[TemplateListItem]:
        """List available templates with optional filtering.

        Args:
            site_id: Filter custom templates by site
            category: Filter by category
            include_builtin: Include builtin templates
            include_custom: Include custom templates

        Returns:
            List of TemplateListItem summaries
        """
        self.load_all_templates()

        results = []

        for cache_key, template in self._cache.items():
            # Determine if builtin or custom
            is_custom = ":" in cache_key

            if is_custom and not include_custom:
                continue
            if not is_custom and not include_builtin:
                continue

            # Filter by site
            if is_custom and site_id:
                key_site = cache_key.split(":")[0]
                if key_site != site_id:
                    continue

            # Filter by category
            if category and template.metadata.category != category:
                continue

            results.append(
                TemplateListItem(
                    template_id=template.template_id,
                    title=template.metadata.title,
                    description=template.metadata.description,
                    category=template.metadata.category,
                    created_by=template.created_by,
                    version=template.version,
                    usage_count=template.usage_count,
                    tags=template.metadata.tags,
                )
            )

        # Sort by usage count (most used first)
        results.sort(key=lambda x: x.usage_count, reverse=True)
        return results

    def save_template(
        self,
        template: ChartTemplate,
        site_id: str,
        overwrite: bool = False,
    ) -> bool:
        """Save a custom template for a site.

        Args:
            template: Template to save
            site_id: Site ID for the custom template
            overwrite: Whether to overwrite existing template

        Returns:
            True if saved successfully
        """
        site_path = self._get_site_custom_path(site_id)
        file_path = site_path / f"{template.template_id}.yaml"

        # Check for existing template
        if file_path.exists() and not overwrite:
            logger.warning(f"Template {template.template_id} already exists for site {site_id}")
            return False

        # Update timestamps
        template.updated_at = datetime.utcnow()
        if not file_path.exists():
            template.created_at = datetime.utcnow()

        success = self._save_template_to_file(template, file_path)

        if success:
            # Update cache
            cache_key = f"{site_id}:{template.template_id}"
            self._cache[cache_key] = template
            logger.info(f"Saved template: {cache_key}")

        return success

    def update_template(
        self,
        template_id: str,
        site_id: str,
        updates: Dict,
    ) -> Optional[ChartTemplate]:
        """Update an existing custom template.

        Args:
            template_id: Template to update
            site_id: Site ID
            updates: Dict of fields to update

        Returns:
            Updated template if successful, None otherwise
        """
        template = self.get_template(template_id, site_id)
        if template is None:
            logger.warning(f"Template {template_id} not found for site {site_id}")
            return None

        # Check if it's a custom template (can't update builtin)
        cache_key = f"{site_id}:{template_id}"
        if cache_key not in self._cache:
            logger.warning(f"Cannot update builtin template: {template_id}")
            return None

        # Apply updates
        template_data = template.model_dump()
        for key, value in updates.items():
            if key in template_data:
                template_data[key] = value

        # Bump version
        version_parts = template.version.split(".")
        version_parts[-1] = str(int(version_parts[-1]) + 1)
        template_data["version"] = ".".join(version_parts)
        template_data["updated_at"] = datetime.utcnow()

        try:
            updated_template = ChartTemplate(**template_data)
        except Exception as e:
            logger.error(f"Invalid update data: {e}")
            return None

        if self.save_template(updated_template, site_id, overwrite=True):
            return updated_template
        return None

    def delete_template(self, template_id: str, site_id: str) -> bool:
        """Delete a custom template.

        Args:
            template_id: Template to delete
            site_id: Site ID

        Returns:
            True if deleted successfully
        """
        site_path = self._get_site_custom_path(site_id)
        file_path = site_path / f"{template_id}.yaml"

        if not file_path.exists():
            logger.warning(f"Template {template_id} not found for site {site_id}")
            return False

        try:
            file_path.unlink()
            cache_key = f"{site_id}:{template_id}"
            if cache_key in self._cache:
                del self._cache[cache_key]
            logger.info(f"Deleted template: {cache_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete template: {e}")
            return False

    def record_usage(self, template_id: str, site_id: Optional[str] = None) -> None:
        """Record that a template was used.

        Updates usage_count and last_used timestamp.
        """
        template = self.get_template(template_id, site_id)
        if template is None:
            return

        template.usage_count += 1
        template.last_used = datetime.utcnow()

        # Only save if it's a custom template
        if site_id:
            cache_key = f"{site_id}:{template_id}"
            if cache_key in self._cache:
                self.save_template(template, site_id, overwrite=True)


# Global singleton
_manager: Optional[TemplateManager] = None


def get_template_manager() -> TemplateManager:
    """Get the global template manager instance."""
    global _manager
    if _manager is None:
        _manager = TemplateManager()
    return _manager
