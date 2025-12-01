"""
Project Manager - Gestión de lógica de negocio de proyectos

Responsabilidades:
- Gestión de proyectos con caché
- Validaciones de negocio
- Emisión de señales PyQt6
- Métodos de utilidad
"""

import logging
from typing import List, Dict, Optional, Tuple, Any
from PyQt6.QtCore import QObject, pyqtSignal

from src.database.db_manager import DBManager
from src.models.project import Project, ProjectRelation, ProjectComponent, validate_entity_type

logger = logging.getLogger(__name__)


class ProjectManager(QObject):
    """
    Manager para gestión de proyectos

    Maneja lógica de negocio, caché y señales para el sistema de proyectos
    """

    # Señales
    project_created = pyqtSignal(dict)  # project_data
    project_updated = pyqtSignal(dict)  # project_data
    project_deleted = pyqtSignal(int)   # project_id
    relation_added = pyqtSignal(int, str, int)  # project_id, entity_type, entity_id
    relation_removed = pyqtSignal(int, str, int)
    component_added = pyqtSignal(int, str)  # project_id, component_type
    component_removed = pyqtSignal(int)  # component_id

    def __init__(self, db_manager: DBManager):
        super().__init__()
        self.db = db_manager
        self._projects_cache: Dict[int, Dict] = {}
        self._cache_enabled = True
        logger.info("ProjectManager initialized")

    # ==================== CACHE ====================

    def invalidate_cache(self):
        """Invalida el caché de proyectos"""
        self._projects_cache.clear()
        logger.debug("Projects cache invalidated")

    def _cache_project(self, project: Dict):
        """Agrega un proyecto al caché"""
        if self._cache_enabled and project:
            self._projects_cache[project['id']] = project

    def _get_from_cache(self, project_id: int) -> Optional[Dict]:
        """Obtiene un proyecto del caché"""
        if self._cache_enabled:
            return self._projects_cache.get(project_id)
        return None

    # ==================== CRUD PROYECTOS ====================

    def create_project(self, name: str, description: str = "",
                      color: str = "#3498db", icon: str = "📁") -> Optional[Dict]:
        """
        Crea un nuevo proyecto con validación

        Args:
            name: Nombre del proyecto
            description: Descripción
            color: Color en formato hex
            icon: Emoji icono

        Returns:
            Diccionario con datos del proyecto creado o None si falla
        """
        # Validar nombre
        is_valid, error_msg = self.validate_project_name(name)
        if not is_valid:
            logger.error(f"Validación fallida: {error_msg}")
            return None

        try:
            project_id = self.db.add_project(name, description, color, icon)
            project = self.db.get_project(project_id)

            if project:
                self._cache_project(project)
                self.project_created.emit(project)
                logger.info(f"Proyecto creado: {name} (ID: {project_id})")

            return project

        except Exception as e:
            logger.error(f"Error creando proyecto: {e}")
            return None

    def get_project(self, project_id: int) -> Optional[Dict]:
        """Obtiene un proyecto (usa caché)"""
        # Intentar desde caché
        cached = self._get_from_cache(project_id)
        if cached:
            return cached

        # Obtener de BD
        project = self.db.get_project(project_id)
        if project:
            self._cache_project(project)

        return project

    def get_all_projects(self, active_only: bool = True) -> List[Dict]:
        """Obtiene todos los proyectos"""
        return self.db.get_all_projects(active_only)

    def update_project(self, project_id: int, **kwargs) -> bool:
        """Actualiza un proyecto"""
        success = self.db.update_project(project_id, **kwargs)

        if success:
            # Invalidar caché de este proyecto
            if project_id in self._projects_cache:
                del self._projects_cache[project_id]

            # Obtener proyecto actualizado y emitir señal
            project = self.get_project(project_id)
            if project:
                self.project_updated.emit(project)

            logger.info(f"Proyecto {project_id} actualizado")

        return success

    def delete_project(self, project_id: int) -> bool:
        """Elimina un proyecto"""
        success = self.db.delete_project(project_id)

        if success:
            # Remover del caché
            if project_id in self._projects_cache:
                del self._projects_cache[project_id]

            self.project_deleted.emit(project_id)
            logger.info(f"Proyecto {project_id} eliminado")

        return success

    # ==================== RELACIONES ====================

    def add_entity_to_project(self, project_id: int, entity_type: str,
                             entity_id: int, description: str = "",
                             order_index: int = None) -> bool:
        """
        Agrega una entidad al proyecto

        Args:
            project_id: ID del proyecto
            entity_type: Tipo de entidad
            entity_id: ID de la entidad
            description: Descripción contextual
            order_index: Índice de orden (None = al final)

        Returns:
            True si se agregó exitosamente
        """
        # Validar tipo de entidad
        if not validate_entity_type(entity_type):
            logger.error(f"Tipo de entidad inválido: {entity_type}")
            return False

        # Si no se especifica orden, agregar al final
        if order_index is None:
            # Obtener el order_index máximo actual
            relations = self.db.get_project_relations(project_id)
            components = self.db.get_project_components(project_id)

            max_order = -1
            for rel in relations:
                rel_order = rel.get('order_index')
                # Manejar None explícitamente
                if rel_order is not None and rel_order > max_order:
                    max_order = rel_order
            for comp in components:
                comp_order = comp.get('order_index')
                # Manejar None explícitamente
                if comp_order is not None and comp_order > max_order:
                    max_order = comp_order

            order_index = max_order + 1

        try:
            relation_id = self.db.add_project_relation(
                project_id, entity_type, entity_id, description, order_index
            )

            if relation_id:
                self.relation_added.emit(project_id, entity_type, entity_id)
                logger.info(f"Entidad agregada: {entity_type}#{entity_id} -> Proyecto#{project_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error agregando entidad al proyecto: {e}")
            return False

    def remove_entity_from_project(self, project_id: int, entity_type: str,
                                   entity_id: int) -> bool:
        """Elimina una entidad del proyecto"""
        success = self.db.remove_project_relation_by_entity(
            project_id, entity_type, entity_id
        )

        if success:
            self.relation_removed.emit(project_id, entity_type, entity_id)

        return success

    def add_component_to_project(self, project_id: int, component_type: str,
                                content: str = "", order_index: int = None) -> bool:
        """Agrega un componente estructural al proyecto"""
        if order_index is None:
            relations = self.db.get_project_relations(project_id)
            components = self.db.get_project_components(project_id)
            order_index = len(relations) + len(components)

        try:
            component_id = self.db.add_project_component(
                project_id, component_type, content, order_index
            )

            if component_id:
                self.component_added.emit(project_id, component_type)
                return True

            return False

        except Exception as e:
            logger.error(f"Error agregando componente: {e}")
            return False

    # ==================== UTILIDADES ====================

    def get_project_entities_grouped(self, project_id: int) -> Dict[str, List]:
        """
        Obtiene todas las entidades del proyecto agrupadas por tipo

        Returns:
            Diccionario con listas por tipo de entidad
        """
        relations = self.db.get_project_relations(project_id)

        grouped = {
            'tags': [],
            'processes': [],
            'lists': [],
            'tables': [],
            'categories': [],
            'items': []
        }

        for rel in relations:
            entity_type = rel['entity_type']
            key = entity_type + 's'  # 'tag' -> 'tags'
            if key in grouped:
                grouped[key].append(rel)

        return grouped

    def get_entity_metadata(self, entity_type: str, entity_id: int) -> Dict:
        """
        Obtiene metadata de una entidad (nombre, icono, etc)

        Returns:
            Diccionario con metadata de la entidad
        """
        from src.models.project import get_entity_type_icon, get_entity_type_label

        metadata = {
            'type': entity_type,
            'id': entity_id,
            'icon': get_entity_type_icon(entity_type),
            'label': get_entity_type_label(entity_type),
            'name': '',
            'content': ''
        }

        # Obtener nombre/contenido desde BD
        try:
            if entity_type == 'tag':
                result = self.db.execute_query(
                    "SELECT name FROM tags WHERE id = ?", (entity_id,)
                )
                if result:
                    metadata['name'] = result[0]['name']

            elif entity_type == 'item':
                result = self.db.execute_query(
                    "SELECT label, content FROM items WHERE id = ?", (entity_id,)
                )
                if result:
                    metadata['name'] = result[0]['label']
                    metadata['content'] = result[0]['content']

            elif entity_type == 'list':
                result = self.db.execute_query(
                    "SELECT name FROM listas WHERE id = ?", (entity_id,)
                )
                if result:
                    metadata['name'] = result[0]['name']

            elif entity_type == 'process':
                result = self.db.execute_query(
                    "SELECT name FROM processes WHERE id = ?", (entity_id,)
                )
                if result:
                    metadata['name'] = result[0]['name']

            elif entity_type == 'table':
                result = self.db.execute_query(
                    "SELECT name FROM tables WHERE id = ?", (entity_id,)
                )
                if result:
                    metadata['name'] = result[0]['name']

            elif entity_type == 'category':
                result = self.db.execute_query(
                    "SELECT name FROM categories WHERE id = ?", (entity_id,)
                )
                if result:
                    metadata['name'] = result[0]['name']

        except Exception as e:
            logger.error(f"Error obteniendo metadata de {entity_type}#{entity_id}: {e}")

        return metadata

    def validate_project_name(self, name: str, exclude_id: int = None) -> Tuple[bool, str]:
        """
        Valida el nombre del proyecto

        Returns:
            Tupla (es_valido, mensaje_error)
        """
        if not name or not name.strip():
            return False, "El nombre no puede estar vacío"

        if len(name) > 100:
            return False, "El nombre es demasiado largo (máx 100 caracteres)"

        # Verificar unicidad
        all_projects = self.db.get_all_projects(active_only=False)
        for project in all_projects:
            if project['name'].lower() == name.lower():
                if exclude_id is None or project['id'] != exclude_id:
                    return False, f"Ya existe un proyecto con el nombre '{name}'"

        return True, ""

    def duplicate_project(self, project_id: int, new_name: str = None) -> Optional[Dict]:
        """
        Duplica un proyecto con todas sus relaciones y componentes

        Args:
            project_id: ID del proyecto a duplicar
            new_name: Nombre del nuevo proyecto (None = auto-generar)

        Returns:
            Proyecto duplicado o None si falla
        """
        # Obtener proyecto original
        original = self.db.get_project(project_id)
        if not original:
            logger.error(f"Proyecto {project_id} no encontrado")
            return None

        # Generar nombre si no se especifica
        if not new_name:
            new_name = f"{original['name']} (Copia)"

        # Crear nuevo proyecto
        new_project = self.create_project(
            name=new_name,
            description=original['description'],
            color=original['color'],
            icon=original['icon']
        )

        if not new_project:
            return None

        new_project_id = new_project['id']

        # Copiar relaciones
        relations = self.db.get_project_relations(project_id)
        for rel in relations:
            self.db.add_project_relation(
                new_project_id,
                rel['entity_type'],
                rel['entity_id'],
                rel['description'],
                rel['order_index']
            )

        # Copiar componentes
        components = self.db.get_project_components(project_id)
        for comp in components:
            self.db.add_project_component(
                new_project_id,
                comp['component_type'],
                comp['content'],
                comp['order_index']
            )

        logger.info(f"Proyecto duplicado: {original['name']} -> {new_name}")
        return new_project

    def get_project_summary(self, project_id: int) -> Dict[str, Any]:
        """Obtiene resumen completo del proyecto"""
        return self.db.get_project_summary(project_id)

    def search_projects(self, query: str) -> List[Dict]:
        """Busca proyectos por nombre o descripción"""
        return self.db.search_projects(query)
