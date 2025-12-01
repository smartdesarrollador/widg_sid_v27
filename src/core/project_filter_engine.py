"""
Project Filter Engine - Filtrado global por proyecto

Responsabilidades:
- Filtrado de categorías, items y tags por proyecto activo
- Caché LRU de resultados
- Integración con filtros existentes
"""

import logging
from typing import List, Dict, Optional, Set
from functools import lru_cache

from src.database.db_manager import DBManager

logger = logging.getLogger(__name__)


class ProjectFilterEngine:
    """
    Motor de filtrado por proyecto

    Filtra categorías, items y tags según el proyecto activo seleccionado
    """

    def __init__(self, db_manager: DBManager):
        self.db = db_manager
        self._active_project_filter: Optional[int] = None
        self._entity_cache: Dict[str, Set[int]] = {}
        logger.info("ProjectFilterEngine initialized")

    # ==================== PROYECTO ACTIVO ====================

    def set_active_project(self, project_id: Optional[int]):
        """
        Establece el proyecto activo para filtrado

        Args:
            project_id: ID del proyecto o None para limpiar filtro
        """
        if self._active_project_filter != project_id:
            self._active_project_filter = project_id
            self.clear_cache()
            logger.info(f"Active project filter set to: {project_id}")

    def get_active_project(self) -> Optional[int]:
        """Retorna el ID del proyecto activo o None"""
        return self._active_project_filter

    def is_filter_active(self) -> bool:
        """Retorna True si hay un proyecto activo"""
        return self._active_project_filter is not None

    def clear_filter(self):
        """Limpia el filtro de proyecto activo"""
        self.set_active_project(None)

    # ==================== CACHE ====================

    def clear_cache(self):
        """Limpia el caché de entidades"""
        self._entity_cache.clear()
        logger.debug("Filter cache cleared")

    def _get_cached_entities(self, entity_type: str) -> Optional[Set[int]]:
        """Obtiene IDs de entidades del caché"""
        if not self._active_project_filter:
            return None
        cache_key = f"{self._active_project_filter}_{entity_type}"
        return self._entity_cache.get(cache_key)

    def _cache_entities(self, entity_type: str, entity_ids: Set[int]):
        """Guarda IDs de entidades en caché"""
        if self._active_project_filter:
            cache_key = f"{self._active_project_filter}_{entity_type}"
            self._entity_cache[cache_key] = entity_ids

    # ==================== OBTENER ENTIDADES FILTRADAS ====================

    def get_entity_ids_in_project(self, entity_type: str) -> Set[int]:
        """
        Obtiene IDs de entidades del tipo especificado en el proyecto activo

        Args:
            entity_type: Tipo de entidad ('tag', 'process', 'list', 'table', 'category', 'item')

        Returns:
            Set de IDs de entidades en el proyecto
        """
        # Si no hay filtro activo, retornar set vacío
        if not self._active_project_filter:
            return set()

        # Intentar desde caché
        cached = self._get_cached_entities(entity_type)
        if cached is not None:
            return cached

        # Obtener desde BD
        relations = self.db.get_project_relations(
            self._active_project_filter,
            entity_type=entity_type
        )

        entity_ids = {rel['entity_id'] for rel in relations}

        # Guardar en caché
        self._cache_entities(entity_type, entity_ids)

        return entity_ids

    def get_filtered_items(self) -> List[Dict]:
        """
        Obtiene items filtrados por proyecto activo

        Returns:
            Lista de items que pertenecen al proyecto activo
        """
        if not self._active_project_filter:
            return []

        item_ids = self.get_entity_ids_in_project('item')

        if not item_ids:
            return []

        # Obtener items desde BD
        all_items = self.db.get_all_items(active_only=True)

        # Filtrar por IDs del proyecto
        filtered = [item for item in all_items if item['id'] in item_ids]

        logger.debug(f"Filtered {len(filtered)} items for project {self._active_project_filter}")
        return filtered

    def get_filtered_categories(self) -> List[Dict]:
        """
        Obtiene categorías filtradas por proyecto activo

        Returns:
            Lista de categorías que pertenecen al proyecto activo
        """
        if not self._active_project_filter:
            return []

        category_ids = self.get_entity_ids_in_project('category')

        if not category_ids:
            return []

        # Obtener categorías desde BD
        all_categories = self.db.get_categories(include_inactive=False)

        # Filtrar por IDs del proyecto
        filtered = [cat for cat in all_categories if cat['id'] in category_ids]

        logger.debug(f"Filtered {len(filtered)} categories for project {self._active_project_filter}")
        return filtered

    def get_filtered_tags(self) -> List[str]:
        """
        Obtiene tags filtrados por proyecto activo

        Returns:
            Lista de nombres de tags que pertenecen al proyecto activo
        """
        if not self._active_project_filter:
            return []

        tag_ids = self.get_entity_ids_in_project('tag')

        if not tag_ids:
            return []

        # Obtener tags desde BD
        all_tags = self.db.get_all_tags()

        # Filtrar por IDs del proyecto
        filtered_tags = [tag['name'] for tag in all_tags if tag['id'] in tag_ids]

        logger.debug(f"Filtered {len(filtered_tags)} tags for project {self._active_project_filter}")
        return filtered_tags

    def get_filtered_lists(self) -> List[Dict]:
        """Obtiene listas filtradas por proyecto activo"""
        if not self._active_project_filter:
            return []

        list_ids = self.get_entity_ids_in_project('list')

        if not list_ids:
            return []

        # Obtener todas las listas
        all_lists = []
        categories = self.db.get_categories()
        for cat in categories:
            lists = self.db.get_listas_by_category_new(cat['id'])
            all_lists.extend(lists)

        # Filtrar por IDs del proyecto
        filtered = [lst for lst in all_lists if lst['id'] in list_ids]

        logger.debug(f"Filtered {len(filtered)} lists for project {self._active_project_filter}")
        return filtered

    def get_filtered_processes(self) -> List[Dict]:
        """Obtiene procesos filtrados por proyecto activo"""
        if not self._active_project_filter:
            return []

        process_ids = self.get_entity_ids_in_project('process')

        if not process_ids:
            return []

        # Obtener procesos desde BD
        all_processes = self.db.get_all_processes()

        # Filtrar por IDs del proyecto
        filtered = [proc for proc in all_processes if proc['id'] in process_ids]

        logger.debug(f"Filtered {len(filtered)} processes for project {self._active_project_filter}")
        return filtered

    def get_filtered_tables(self) -> List[Dict]:
        """Obtiene tablas filtradas por proyecto activo"""
        if not self._active_project_filter:
            return []

        table_ids = self.get_entity_ids_in_project('table')

        if not table_ids:
            return []

        # Obtener tablas desde BD
        all_tables = self.db.get_all_tables()

        # Filtrar por IDs del proyecto
        filtered = [tbl for tbl in all_tables if tbl['id'] in table_ids]

        logger.debug(f"Filtered {len(filtered)} tables for project {self._active_project_filter}")
        return filtered

    # ==================== VERIFICACIÓN ====================

    def is_entity_in_active_project(self, entity_type: str, entity_id: int) -> bool:
        """
        Verifica si una entidad está en el proyecto activo

        Args:
            entity_type: Tipo de entidad
            entity_id: ID de la entidad

        Returns:
            True si la entidad está en el proyecto activo
        """
        if not self._active_project_filter:
            return False

        entity_ids = self.get_entity_ids_in_project(entity_type)
        return entity_id in entity_ids

    def filter_items_by_project(self, items: List[Dict]) -> List[Dict]:
        """
        Filtra una lista de items por proyecto activo

        Args:
            items: Lista de items a filtrar

        Returns:
            Lista filtrada de items
        """
        if not self._active_project_filter:
            return items

        item_ids = self.get_entity_ids_in_project('item')

        if not item_ids:
            return []

        return [item for item in items if item['id'] in item_ids]

    def filter_categories_by_project(self, categories: List[Dict]) -> List[Dict]:
        """Filtra una lista de categorías por proyecto activo"""
        if not self._active_project_filter:
            return categories

        category_ids = self.get_entity_ids_in_project('category')

        if not category_ids:
            return []

        return [cat for cat in categories if cat['id'] in category_ids]

    # ==================== ESTADÍSTICAS ====================

    def get_filter_stats(self) -> Dict[str, int]:
        """
        Obtiene estadísticas del filtro activo

        Returns:
            Diccionario con conteos de entidades filtradas
        """
        if not self._active_project_filter:
            return {}

        return {
            'project_id': self._active_project_filter,
            'items': len(self.get_entity_ids_in_project('item')),
            'categories': len(self.get_entity_ids_in_project('category')),
            'tags': len(self.get_entity_ids_in_project('tag')),
            'lists': len(self.get_entity_ids_in_project('list')),
            'processes': len(self.get_entity_ids_in_project('process')),
            'tables': len(self.get_entity_ids_in_project('table'))
        }
