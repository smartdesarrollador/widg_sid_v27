"""
Project Export Manager - Gestión de exportación e importación de proyectos

Permite exportar proyectos completos a JSON con todas sus relaciones y componentes,
e importar proyectos desde archivos JSON.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ProjectExportManager:
    """Gestor de exportación e importación de proyectos"""

    def __init__(self, db_manager):
        self.db = db_manager

    def export_project(self, project_id: int, file_path: str = None) -> Optional[str]:
        """
        Exporta un proyecto completo a JSON

        Args:
            project_id: ID del proyecto a exportar
            file_path: Ruta del archivo de destino (opcional, si no se provee se genera)

        Returns:
            Ruta del archivo creado, o None si hay error
        """
        try:
            # Obtener datos del proyecto
            project = self.db.get_project(project_id)
            if not project:
                logger.error(f"Proyecto {project_id} no encontrado")
                return None

            # Construir estructura de exportación
            export_data = {
                'version': '1.0',
                'export_date': datetime.now().isoformat(),
                'project': {
                    'name': project['name'],
                    'description': project.get('description', ''),
                    'color': project.get('color', '#3498db'),
                    'icon': project.get('icon', '📁'),
                },
                'relations': [],
                'components': []
            }

            # Obtener relaciones con contenido completo
            relations = self.db.get_project_relations(project_id)
            for relation in relations:
                relation_data = {
                    'entity_type': relation['entity_type'],
                    'entity_id': relation['entity_id'],
                    'description': relation.get('description', ''),
                    'order_index': relation.get('order_index', 0),
                }

                # Agregar metadata del elemento
                try:
                    if relation['entity_type'] == 'tag':
                        tag = self.db.get_tag_by_id(relation['entity_id'])
                        if tag:
                            relation_data['entity_data'] = {'name': tag.get('name', '')}

                    elif relation['entity_type'] == 'item':
                        # Buscar item en todas las categorías
                        item = None
                        for cat in self.db.get_categories():
                            items = self.db.get_items_by_category(cat['id'])
                            for i in items:
                                if i.get('id') == relation['entity_id']:
                                    item = i
                                    break
                            if item:
                                break

                        if item:
                            relation_data['entity_data'] = {
                                'label': item.get('label', ''),
                                'content': item.get('content', ''),
                                'item_type': item.get('item_type', 'TEXT'),
                            }

                    elif relation['entity_type'] == 'category':
                        category = self.db.get_category_by_id(relation['entity_id'])
                        if category:
                            relation_data['entity_data'] = {
                                'name': category.get('name', ''),
                                'icon': category.get('icon', '📂'),
                            }

                    elif relation['entity_type'] == 'list':
                        lista = self.db.get_lista(relation['entity_id'])
                        if lista:
                            relation_data['entity_data'] = {
                                'name': lista.get('name', ''),
                            }

                    elif relation['entity_type'] == 'table':
                        table = self.db.get_table(relation['entity_id'])
                        if table:
                            relation_data['entity_data'] = {
                                'name': table.get('name', ''),
                            }

                    elif relation['entity_type'] == 'process':
                        process = self.db.get_process(relation['entity_id'])
                        if process:
                            relation_data['entity_data'] = {
                                'name': process.get('name', ''),
                            }

                except Exception as e:
                    logger.warning(f"Error obteniendo datos de {relation['entity_type']}#{relation['entity_id']}: {e}")
                    relation_data['entity_data'] = None

                export_data['relations'].append(relation_data)

            # Obtener componentes
            components = self.db.get_project_components(project_id)
            for component in components:
                export_data['components'].append({
                    'component_type': component['component_type'],
                    'content': component.get('content', ''),
                    'order_index': component.get('order_index', 0),
                })

            # Generar nombre de archivo si no se provee
            if not file_path:
                safe_name = "".join(c for c in project['name'] if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_name = safe_name.replace(' ', '_')
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_path = f"proyecto_{safe_name}_{timestamp}.json"

            # Escribir archivo
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Proyecto exportado a: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Error exportando proyecto: {e}", exc_info=True)
            return None

    def import_project(self, file_path: str, import_mode: str = 'new') -> Optional[int]:
        """
        Importa un proyecto desde JSON

        Args:
            file_path: Ruta del archivo JSON a importar
            import_mode: 'new' = crear nuevo proyecto, 'merge' = fusionar con existente

        Returns:
            ID del proyecto importado, o None si hay error
        """
        try:
            # Leer archivo
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            # Validar estructura
            if 'project' not in import_data:
                logger.error("Archivo JSON inválido: falta 'project'")
                return None

            project_data = import_data['project']

            # Crear proyecto (con nombre único si ya existe)
            project_name = project_data['name']

            # Verificar si el nombre ya existe y agregar sufijo si es necesario
            all_projects = self.db.get_all_projects(active_only=False)
            existing_names = [p['name'] for p in all_projects]

            if project_name in existing_names:
                # Agregar sufijo numérico
                counter = 1
                while True:
                    new_name = f"{project_name} ({counter})"
                    if new_name not in existing_names:
                        project_name = new_name
                        break
                    counter += 1

                logger.info(f"Nombre duplicado, renombrando a: {project_name}")

            project_id = self.db.add_project(
                name=project_name,
                description=project_data.get('description', ''),
                color=project_data.get('color', '#3498db'),
                icon=project_data.get('icon', '📁')
            )

            if not project_id:
                logger.error("Error creando proyecto al importar")
                return None

            logger.info(f"Proyecto '{project_data['name']}' creado con ID: {project_id}")

            # Importar relaciones
            imported_relations = 0
            if 'relations' in import_data:
                for relation in import_data['relations']:
                    # Solo importar si el elemento existe
                    entity_type = relation['entity_type']
                    entity_id = relation['entity_id']

                    # Verificar existencia del elemento
                    exists = self._entity_exists(entity_type, entity_id)
                    if not exists:
                        logger.warning(f"Saltando {entity_type}#{entity_id} - no existe en BD")
                        continue

                    # Agregar relación
                    success = self.db.add_project_relation(
                        project_id=project_id,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        description=relation.get('description', ''),
                        order_index=relation.get('order_index', 0)
                    )

                    if success:
                        imported_relations += 1

            logger.info(f"Relaciones importadas: {imported_relations}/{len(import_data.get('relations', []))}")

            # Importar componentes
            imported_components = 0
            if 'components' in import_data:
                for component in import_data['components']:
                    success = self.db.add_project_component(
                        project_id=project_id,
                        component_type=component['component_type'],
                        content=component.get('content', ''),
                        order_index=component.get('order_index', 0)
                    )

                    if success:
                        imported_components += 1

            logger.info(f"Componentes importados: {imported_components}/{len(import_data.get('components', []))}")

            return project_id

        except Exception as e:
            logger.error(f"Error importando proyecto: {e}", exc_info=True)
            return None

    def _entity_exists(self, entity_type: str, entity_id: int) -> bool:
        """Verifica si una entidad existe en la base de datos"""
        try:
            if entity_type == 'tag':
                return self.db.get_tag_by_id(entity_id) is not None

            elif entity_type == 'item':
                # Buscar item en todas las categorías
                for cat in self.db.get_categories():
                    items = self.db.get_items_by_category(cat['id'])
                    for i in items:
                        if i.get('id') == entity_id:
                            return True
                return False

            elif entity_type == 'category':
                return self.db.get_category_by_id(entity_id) is not None
            elif entity_type == 'list':
                return self.db.get_lista(entity_id) is not None
            elif entity_type == 'table':
                return self.db.get_table(entity_id) is not None
            elif entity_type == 'process':
                return self.db.get_process(entity_id) is not None
            return False
        except:
            return False

    def export_all_projects(self, output_dir: str = "exports") -> List[str]:
        """
        Exporta todos los proyectos activos a archivos JSON individuales

        Args:
            output_dir: Directorio donde guardar los archivos

        Returns:
            Lista de rutas de archivos creados
        """
        try:
            # Crear directorio si no existe
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            # Obtener todos los proyectos activos
            projects = self.db.get_all_projects(active_only=True)

            exported_files = []
            for project in projects:
                safe_name = "".join(c for c in project['name'] if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_name = safe_name.replace(' ', '_')
                file_path = Path(output_dir) / f"{safe_name}_{project['id']}.json"

                result = self.export_project(project['id'], str(file_path))
                if result:
                    exported_files.append(result)

            logger.info(f"Exportados {len(exported_files)} proyectos a {output_dir}")
            return exported_files

        except Exception as e:
            logger.error(f"Error exportando todos los proyectos: {e}", exc_info=True)
            return []

    def get_export_summary(self, project_id: int) -> Dict[str, Any]:
        """
        Obtiene un resumen de lo que se exportará

        Args:
            project_id: ID del proyecto

        Returns:
            Diccionario con estadísticas del proyecto
        """
        try:
            project = self.db.get_project(project_id)
            if not project:
                return {}

            relations = self.db.get_project_relations(project_id)
            components = self.db.get_project_components(project_id)

            # Contar por tipo
            relations_by_type = {}
            for rel in relations:
                entity_type = rel['entity_type']
                relations_by_type[entity_type] = relations_by_type.get(entity_type, 0) + 1

            components_by_type = {}
            for comp in components:
                comp_type = comp['component_type']
                components_by_type[comp_type] = components_by_type.get(comp_type, 0) + 1

            return {
                'project_name': project['name'],
                'total_relations': len(relations),
                'relations_by_type': relations_by_type,
                'total_components': len(components),
                'components_by_type': components_by_type,
            }

        except Exception as e:
            logger.error(f"Error obteniendo resumen de exportación: {e}")
            return {}
