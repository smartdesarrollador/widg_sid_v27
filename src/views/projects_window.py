"""
Projects Window - Ventana de gestión de proyectos

MVP Features:
- Lista de proyectos con búsqueda
- Panel de detalles con información básica
- Modo Edición y Modo Vista Amigable
- Canvas con elementos y componentes ordenados
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QListWidget,
                             QListWidgetItem, QTextEdit, QScrollArea, QFrame,
                             QMessageBox, QColorDialog, QApplication, QDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
import logging

from src.core.project_manager import ProjectManager
from src.core.project_export_manager import ProjectExportManager
from src.database.db_manager import DBManager
from src.views.widgets.project_relation_widget import ProjectRelationWidget
from src.views.widgets.project_component_widget import ProjectComponentWidget

logger = logging.getLogger(__name__)


class ProjectsWindow(QMainWindow):
    """Ventana principal de gestión de proyectos"""

    closed = pyqtSignal()

    def __init__(self, db_manager: DBManager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.project_manager = ProjectManager(db_manager)
        self.export_manager = ProjectExportManager(db_manager)
        self.current_project_id = None
        self._view_mode = 'edit'  # 'edit' o 'clean'

        self.init_ui()
        self.load_projects()

        logger.info("ProjectsWindow initialized")

    def init_ui(self):
        """Inicializa la interfaz"""
        self.setWindowTitle("📁 Gestión de Proyectos")
        self.showMaximized()  # Maximizada por defecto

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal horizontal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Panel izquierdo: Lista de proyectos (25%)
        left_panel = self._create_projects_list_panel()
        left_panel.setMaximumWidth(300)
        main_layout.addWidget(left_panel, 1)

        # Panel derecho: Espacio del proyecto (75%)
        right_panel = self._create_project_space_panel()
        main_layout.addWidget(right_panel, 3)

        # Styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border-color: #00ff88;
            }
            QPushButton:pressed {
                background-color: #1e1e1e;
            }
            QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                padding: 8px;
                border-radius: 4px;
            }
            QTextEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                padding: 8px;
                border-radius: 4px;
            }
            QLabel {
                color: #ffffff;
            }
            QListWidget {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #00ff88;
                color: #000000;
            }
        """)

    def _create_projects_list_panel(self) -> QWidget:
        """Crea el panel izquierdo con lista de proyectos"""
        panel = QWidget()
        panel.setStyleSheet("background-color: #252525; border-right: 2px solid #3d3d3d;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header = QLabel("📁 Mis Proyectos")
        header.setStyleSheet("font-size: 14pt; font-weight: bold; padding: 10px;")
        layout.addWidget(header)

        # Búsqueda
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar proyectos...")
        self.search_input.textChanged.connect(self.on_search_changed)
        layout.addWidget(self.search_input)

        # Botón nuevo proyecto
        new_btn = QPushButton("+ Nuevo Proyecto")
        new_btn.clicked.connect(self.on_new_project)
        layout.addWidget(new_btn)

        # Botones de importar/exportar
        import_export_layout = QHBoxLayout()

        import_btn = QPushButton("📥 Importar")
        import_btn.setToolTip("Importar proyecto desde JSON")
        import_btn.clicked.connect(self.on_import_project)
        import_export_layout.addWidget(import_btn)

        export_btn = QPushButton("📤 Exportar")
        export_btn.setToolTip("Exportar proyecto seleccionado a JSON")
        export_btn.clicked.connect(self.on_export_project)
        import_export_layout.addWidget(export_btn)

        layout.addLayout(import_export_layout)

        # Lista de proyectos
        self.projects_list = QListWidget()
        self.projects_list.itemClicked.connect(self.on_project_selected)
        layout.addWidget(self.projects_list)

        return panel

    def _create_project_space_panel(self) -> QWidget:
        """Crea el panel derecho con espacio del proyecto"""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1e1e1e;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header con info del proyecto y toggle de modo
        header_layout = QHBoxLayout()

        self.project_name_label = QLabel("Selecciona un proyecto")
        self.project_name_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        header_layout.addWidget(self.project_name_label)

        header_layout.addStretch()

        # Botón refrescar proyecto
        self.refresh_btn = QPushButton("🔄 Actualizar")
        self.refresh_btn.setVisible(False)  # Oculto hasta seleccionar proyecto
        self.refresh_btn.clicked.connect(self.on_refresh_project)
        self.refresh_btn.setToolTip("Actualizar la vista del proyecto")
        header_layout.addWidget(self.refresh_btn)

        # Botón editar proyecto
        self.edit_project_btn = QPushButton("✏️ Editar")
        self.edit_project_btn.setVisible(False)  # Oculto hasta seleccionar proyecto
        self.edit_project_btn.clicked.connect(self.on_edit_project)
        header_layout.addWidget(self.edit_project_btn)

        # Toggle modo vista
        self.mode_toggle_btn = QPushButton("👁️ Vista Limpia")
        self.mode_toggle_btn.clicked.connect(self.toggle_view_mode)
        header_layout.addWidget(self.mode_toggle_btn)

        layout.addLayout(header_layout)

        # Descripción
        self.project_desc_label = QLabel("")
        self.project_desc_label.setWordWrap(True)
        layout.addWidget(self.project_desc_label)

        # Toolbar (solo en modo edición)
        self.toolbar = self._create_toolbar()
        layout.addWidget(self.toolbar)

        # Canvas scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")

        self.canvas_widget = QWidget()
        self.canvas_layout = QVBoxLayout(self.canvas_widget)
        self.canvas_layout.setSpacing(5)
        self.canvas_layout.addStretch()

        scroll.setWidget(self.canvas_widget)
        layout.addWidget(scroll)

        # Botones inferiores (solo en modo edición)
        self.bottom_buttons = QWidget()
        bottom_layout = QHBoxLayout(self.bottom_buttons)

        save_btn = QPushButton("💾 Guardar")
        save_btn.clicked.connect(self.on_save)
        bottom_layout.addWidget(save_btn)

        close_btn = QPushButton("❌ Cerrar")
        close_btn.clicked.connect(self.close)
        bottom_layout.addWidget(close_btn)

        layout.addWidget(self.bottom_buttons)

        return panel

    def _create_toolbar(self) -> QWidget:
        """Crea el toolbar con botones para agregar elementos"""
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 10, 0, 10)

        # Botones para agregar elementos
        add_tag_btn = QPushButton("🏷️ Tag")
        add_tag_btn.clicked.connect(lambda: self.add_element_to_project('tag'))
        toolbar_layout.addWidget(add_tag_btn)

        add_item_btn = QPushButton("📄 Item")
        add_item_btn.clicked.connect(lambda: self.add_element_to_project('item'))
        toolbar_layout.addWidget(add_item_btn)

        add_category_btn = QPushButton("📂 Categoría")
        add_category_btn.clicked.connect(lambda: self.add_element_to_project('category'))
        toolbar_layout.addWidget(add_category_btn)

        add_list_btn = QPushButton("📋 Lista")
        add_list_btn.clicked.connect(lambda: self.add_element_to_project('list'))
        toolbar_layout.addWidget(add_list_btn)

        add_table_btn = QPushButton("📊 Tabla")
        add_table_btn.clicked.connect(lambda: self.add_element_to_project('table'))
        toolbar_layout.addWidget(add_table_btn)

        add_process_btn = QPushButton("⚙️ Proceso")
        add_process_btn.clicked.connect(lambda: self.add_element_to_project('process'))
        toolbar_layout.addWidget(add_process_btn)

        # Separador
        sep = QLabel("|")
        sep.setStyleSheet("color: #555555; font-size: 16pt;")
        toolbar_layout.addWidget(sep)

        # Componentes estructurales
        add_comment_btn = QPushButton("💬 Comentario")
        add_comment_btn.clicked.connect(lambda: self.add_component('comment'))
        toolbar_layout.addWidget(add_comment_btn)

        add_note_btn = QPushButton("📌 Nota")
        add_note_btn.clicked.connect(lambda: self.add_component('note'))
        toolbar_layout.addWidget(add_note_btn)

        add_alert_btn = QPushButton("⚠️ Alerta")
        add_alert_btn.clicked.connect(lambda: self.add_component('alert'))
        toolbar_layout.addWidget(add_alert_btn)

        add_divider_btn = QPushButton("─ Divisor")
        add_divider_btn.clicked.connect(lambda: self.add_component('divider'))
        toolbar_layout.addWidget(add_divider_btn)

        toolbar_layout.addStretch()

        return toolbar

    # ==================== EVENTOS ====================

    def load_projects(self):
        """Carga todos los proyectos en la lista"""
        self.projects_list.clear()
        projects = self.project_manager.get_all_projects(active_only=True)

        for project in projects:
            item = QListWidgetItem(f"{project['icon']} {project['name']}")
            item.setData(Qt.ItemDataRole.UserRole, project['id'])
            self.projects_list.addItem(item)

    def on_search_changed(self, text):
        """Filtra proyectos por búsqueda"""
        if not text:
            self.load_projects()
            return

        results = self.project_manager.search_projects(text)
        self.projects_list.clear()

        for project in results:
            item = QListWidgetItem(f"{project['icon']} {project['name']}")
            item.setData(Qt.ItemDataRole.UserRole, project['id'])
            self.projects_list.addItem(item)

    def on_new_project(self):
        """Crea un nuevo proyecto"""
        from PyQt6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "Nuevo Proyecto", "Nombre del proyecto:")
        if ok and name:
            project = self.project_manager.create_project(name)
            if project:
                self.load_projects()
                QMessageBox.information(self, "Éxito", f"Proyecto '{name}' creado")
            else:
                QMessageBox.warning(self, "Error", "No se pudo crear el proyecto")

    def on_project_selected(self, item):
        """Cuando se selecciona un proyecto de la lista"""
        project_id = item.data(Qt.ItemDataRole.UserRole)
        self.load_project(project_id)

    def load_project(self, project_id: int):
        """Carga un proyecto y muestra su contenido"""
        self.current_project_id = project_id
        project = self.project_manager.get_project(project_id)

        if not project:
            return

        # Actualizar header
        self.project_name_label.setText(f"{project['icon']} {project['name']}")
        self.project_desc_label.setText(project['description'])
        self.refresh_btn.setVisible(True)  # Mostrar botón refrescar
        self.edit_project_btn.setVisible(True)  # Mostrar botón editar

        # Limpiar canvas
        self._clear_canvas()

        # Cargar contenido ordenado
        content = self.db.get_project_content_ordered(project_id)

        for item in content:
            if item['type'] == 'relation':
                self._add_relation_widget(item)
            else:  # component
                self._add_component_widget(item)

    def _clear_canvas(self):
        """Limpia el canvas eliminando todos los widgets"""
        while self.canvas_layout.count() > 1:  # Mantener el stretch
            child = self.canvas_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _add_relation_widget(self, relation):
        """Agrega un widget de relación al canvas"""
        # Obtener metadata
        metadata = self.project_manager.get_entity_metadata(
            relation['entity_type'],
            relation['entity_id']
        )

        # Crear widget especializado
        widget = ProjectRelationWidget(
            relation_data=relation,
            metadata=metadata,
            view_mode=self._view_mode,
            parent=self.canvas_widget
        )

        # Conectar señales
        widget.copy_requested.connect(self._copy_to_clipboard)
        widget.delete_requested.connect(self._on_relation_delete)
        widget.edit_description_requested.connect(self._on_relation_description_edit)
        widget.move_up_requested.connect(self._on_move_up)
        widget.move_down_requested.connect(self._on_move_down)

        self.canvas_layout.insertWidget(self.canvas_layout.count() - 1, widget)

    def _add_component_widget(self, component):
        """Agrega un widget de componente al canvas"""
        # Crear widget especializado
        widget = ProjectComponentWidget(
            component_data=component,
            view_mode=self._view_mode,
            parent=self.canvas_widget
        )

        # Conectar señales
        widget.delete_requested.connect(self._on_component_delete)
        widget.edit_content_requested.connect(self._on_component_content_edit)
        widget.move_up_requested.connect(self._on_move_up)
        widget.move_down_requested.connect(self._on_move_down)

        self.canvas_layout.insertWidget(self.canvas_layout.count() - 1, widget)

    def _on_relation_delete(self, relation_id: int):
        """Maneja eliminación de relación"""
        try:
            success = self.db.remove_project_relation(relation_id)
            if success:
                logger.info(f"Relation {relation_id} deleted")
                self.load_project(self.current_project_id)
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar la relación")
        except Exception as e:
            logger.error(f"Error deleting relation: {e}")
            QMessageBox.critical(self, "Error", f"Error al eliminar: {str(e)}")

    def _on_relation_description_edit(self, relation_id: int, new_description: str):
        """Maneja edición de descripción de relación"""
        try:
            success = self.db.update_relation_description(relation_id, new_description)
            if success:
                logger.info(f"Relation {relation_id} description updated")
        except Exception as e:
            logger.error(f"Error updating relation description: {e}")

    def _on_component_delete(self, component_id: int):
        """Maneja eliminación de componente"""
        try:
            success = self.db.remove_project_component(component_id)
            if success:
                logger.info(f"Component {component_id} deleted")
                self.load_project(self.current_project_id)
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar el componente")
        except Exception as e:
            logger.error(f"Error deleting component: {e}")
            QMessageBox.critical(self, "Error", f"Error al eliminar: {str(e)}")

    def _on_component_content_edit(self, component_id: int, new_content: str):
        """Maneja edición de contenido de componente"""
        try:
            success = self.db.update_component_content(component_id, new_content)
            if success:
                logger.info(f"Component {component_id} content updated")
        except Exception as e:
            logger.error(f"Error updating component content: {e}")

    def _on_move_up(self, item_id: int):
        """Maneja mover elemento hacia arriba"""
        if not self.current_project_id:
            return

        try:
            logger.info(f"Move up requested for item_id: {item_id}")

            # Obtener todo el contenido ordenado
            content = self.db.get_project_content_ordered(self.current_project_id)
            logger.info(f"Total content items: {len(content)}")

            # Encontrar el índice del item
            current_index = None
            for i, item in enumerate(content):
                # Verificar si es relación o componente
                # Un item es relación si entity_type NO es NULL
                # Un item es componente si component_type NO es NULL
                if item.get('id') == item_id:
                    current_index = i
                    if item.get('entity_type') is not None:
                        logger.info(f"Found relation at index {i}, entity_type: {item.get('entity_type')}")
                    elif item.get('component_type') is not None:
                        logger.info(f"Found component at index {i}, type: {item.get('component_type')}")
                    break

            if current_index is None:
                logger.warning(f"Item {item_id} not found in content")
                return

            if current_index == 0:
                logger.info("Item already at top")
                return  # Ya está al inicio

            # Intercambiar order_index con el elemento anterior
            current_item = content[current_index]
            prev_item = content[current_index - 1]

            logger.info(f"Swapping: current order_index={current_item['order_index']}, prev order_index={prev_item['order_index']}")

            # Actualizar order_index
            # Determinar tipo del item actual
            if current_item.get('entity_type') is not None:
                logger.info(f"Updating relation {current_item['id']} (type: {current_item['entity_type']}) to order {prev_item['order_index']}")
                self.db.update_relation_order(current_item['id'], prev_item['order_index'])
            elif current_item.get('component_type') is not None:
                logger.info(f"Updating component {current_item['id']} (type: {current_item['component_type']}) to order {prev_item['order_index']}")
                self.db.update_component_order(current_item['id'], prev_item['order_index'])

            # Determinar tipo del item anterior
            if prev_item.get('entity_type') is not None:
                logger.info(f"Updating relation {prev_item['id']} (type: {prev_item['entity_type']}) to order {current_item['order_index']}")
                self.db.update_relation_order(prev_item['id'], current_item['order_index'])
            elif prev_item.get('component_type') is not None:
                logger.info(f"Updating component {prev_item['id']} (type: {prev_item['component_type']}) to order {current_item['order_index']}")
                self.db.update_component_order(prev_item['id'], current_item['order_index'])

            # Recargar proyecto
            logger.info("Reloading project after move")
            self.load_project(self.current_project_id)

        except Exception as e:
            logger.error(f"Error moving item up: {e}")

    def _on_move_down(self, item_id: int):
        """Maneja mover elemento hacia abajo"""
        if not self.current_project_id:
            return

        try:
            logger.info(f"Move down requested for item_id: {item_id}")

            # Obtener todo el contenido ordenado
            content = self.db.get_project_content_ordered(self.current_project_id)
            logger.info(f"Total content items: {len(content)}")

            # Encontrar el índice del item
            current_index = None
            for i, item in enumerate(content):
                # Verificar si es relación o componente
                # Un item es relación si entity_type NO es NULL
                # Un item es componente si component_type NO es NULL
                if item.get('id') == item_id:
                    current_index = i
                    if item.get('entity_type') is not None:
                        logger.info(f"Found relation at index {i}, entity_type: {item.get('entity_type')}")
                    elif item.get('component_type') is not None:
                        logger.info(f"Found component at index {i}, type: {item.get('component_type')}")
                    break

            if current_index is None:
                logger.warning(f"Item {item_id} not found in content")
                return

            if current_index >= len(content) - 1:
                logger.info("Item already at bottom")
                return  # Ya está al final

            # Intercambiar order_index con el elemento siguiente
            current_item = content[current_index]
            next_item = content[current_index + 1]

            logger.info(f"Swapping: current order_index={current_item['order_index']}, next order_index={next_item['order_index']}")

            # Actualizar order_index
            # Determinar tipo del item actual
            if current_item.get('entity_type') is not None:
                logger.info(f"Updating relation {current_item['id']} (type: {current_item['entity_type']}) to order {next_item['order_index']}")
                self.db.update_relation_order(current_item['id'], next_item['order_index'])
            elif current_item.get('component_type') is not None:
                logger.info(f"Updating component {current_item['id']} (type: {current_item['component_type']}) to order {next_item['order_index']}")
                self.db.update_component_order(current_item['id'], next_item['order_index'])

            # Determinar tipo del item siguiente
            if next_item.get('entity_type') is not None:
                logger.info(f"Updating relation {next_item['id']} (type: {next_item['entity_type']}) to order {current_item['order_index']}")
                self.db.update_relation_order(next_item['id'], current_item['order_index'])
            elif next_item.get('component_type') is not None:
                logger.info(f"Updating component {next_item['id']} (type: {next_item['component_type']}) to order {current_item['order_index']}")
                self.db.update_component_order(next_item['id'], current_item['order_index'])

            # Recargar proyecto
            logger.info("Reloading project after move")
            self.load_project(self.current_project_id)

        except Exception as e:
            logger.error(f"Error moving item down: {e}")

    def _copy_to_clipboard(self, text: str):
        """Copia texto al portapapeles"""
        QApplication.clipboard().setText(text)
        logger.info(f"Copied to clipboard: {text[:50]}...")

    def toggle_view_mode(self):
        """Alterna entre Modo Edición y Modo Vista Amigable"""
        if self._view_mode == 'edit':
            self._view_mode = 'clean'
            self._apply_clean_view_mode()
        else:
            self._view_mode = 'edit'
            self._apply_edit_view_mode()

    def _apply_edit_view_mode(self):
        """Aplica estilo de Modo Edición"""
        self.toolbar.setVisible(True)
        self.bottom_buttons.setVisible(True)
        self.mode_toggle_btn.setText("👁️ Vista Limpia")

        if self.current_project_id:
            self.load_project(self.current_project_id)

    def _apply_clean_view_mode(self):
        """Aplica estilo de Modo Vista Amigable"""
        self.toolbar.setVisible(False)
        self.bottom_buttons.setVisible(False)
        self.mode_toggle_btn.setText("📝 Modo Edición")

        if self.current_project_id:
            self.load_project(self.current_project_id)

    def add_element_to_project(self, entity_type: str):
        """Agrega un elemento al proyecto"""
        if not self.current_project_id:
            QMessageBox.warning(self, "Error", "Selecciona un proyecto primero")
            return

        try:
            # Abrir selector de entidad
            from src.views.dialogs.project_entity_selector import ProjectEntitySelector

            selector = ProjectEntitySelector(
                entity_type=entity_type,
                db_manager=self.db,
                project_id=self.current_project_id,  # Pasar project_id
                parent=self
            )

            # Conectar señal
            selector.entity_selected.connect(self._on_entity_selected)

            selector.exec()

        except Exception as e:
            logger.error(f"Error opening entity selector: {e}")
            QMessageBox.critical(self, "Error", f"Error al abrir selector:\n{str(e)}")

    def _on_entity_selected(self, entity_type: str, entity_id: int, description: str):
        """Maneja la selección de una entidad desde el selector"""
        try:
            success = self.project_manager.add_entity_to_project(
                self.current_project_id, entity_type, entity_id, description
            )

            if success:
                logger.info(f"Added {entity_type} #{entity_id} to project {self.current_project_id}")
                self.load_project(self.current_project_id)
                QMessageBox.information(self, "Éxito", f"{entity_type.title()} agregado al proyecto")
            else:
                QMessageBox.warning(self, "Error", "No se pudo agregar el elemento")

        except Exception as e:
            logger.error(f"Error adding entity to project: {e}")
            QMessageBox.critical(self, "Error", f"Error al agregar:\n{str(e)}")

    def add_component(self, component_type: str):
        """Agrega un componente estructural"""
        if not self.current_project_id:
            QMessageBox.warning(self, "Error", "Selecciona un proyecto primero")
            return

        content = ""
        if component_type != 'divider':
            from PyQt6.QtWidgets import QInputDialog
            content, ok = QInputDialog.getText(self, "Agregar Componente", "Contenido:")
            if not ok:
                return

        success = self.project_manager.add_component_to_project(
            self.current_project_id, component_type, content
        )

        if success:
            self.load_project(self.current_project_id)

    def on_refresh_project(self):
        """Recarga el proyecto actual sin cerrar la ventana"""
        if not self.current_project_id:
            return

        logger.info(f"Refreshing project {self.current_project_id}")
        self.load_project(self.current_project_id)

    def on_edit_project(self):
        """Abre el diálogo de edición de proyecto"""
        if not self.current_project_id:
            return

        try:
            from src.views.dialogs.project_editor_dialog import ProjectEditorDialog

            # Obtener datos del proyecto
            project = self.project_manager.get_project(self.current_project_id)
            if not project:
                QMessageBox.warning(self, "Error", "No se pudo cargar el proyecto")
                return

            # Abrir diálogo
            dialog = ProjectEditorDialog(
                project_data=project,
                db_manager=self.db,
                parent=self
            )

            # Conectar señal
            dialog.project_updated.connect(self._on_project_updated)

            result = dialog.exec()

            # Si se eliminó el proyecto, limpiar vista
            if result == QDialog.DialogCode.Accepted:
                # Verificar si el proyecto todavía existe
                updated_project = self.project_manager.get_project(self.current_project_id)
                if not updated_project:
                    # Proyecto eliminado
                    self.current_project_id = None
                    self.project_name_label.setText("Selecciona un proyecto")
                    self.project_desc_label.setText("")
                    self.refresh_btn.setVisible(False)
                    self.edit_project_btn.setVisible(False)
                    self._clear_canvas()
                    self.load_projects()

        except Exception as e:
            logger.error(f"Error opening project editor: {e}")
            QMessageBox.critical(self, "Error", f"Error al abrir editor:\n{str(e)}")

    def _on_project_updated(self, project_id: int):
        """Maneja la actualización de un proyecto"""
        # Recargar proyectos en la lista
        self.load_projects()

        # Recargar proyecto actual si es el mismo
        if project_id == self.current_project_id:
            self.load_project(project_id)

    def on_export_project(self):
        """Maneja la exportación del proyecto actual"""
        if not self.current_project_id:
            QMessageBox.warning(self, "Error", "Selecciona un proyecto primero")
            return

        try:
            from src.views.dialogs.project_export_dialog import ProjectExportDialog

            project = self.project_manager.get_project(self.current_project_id)
            if not project:
                QMessageBox.warning(self, "Error", "No se pudo cargar el proyecto")
                return

            dialog = ProjectExportDialog(
                project_data=project,
                export_manager=self.export_manager,
                parent=self
            )

            dialog.export_completed.connect(self._on_export_completed)
            dialog.exec()

        except Exception as e:
            logger.error(f"Error abriendo diálogo de exportación: {e}")
            QMessageBox.critical(self, "Error", f"Error:\n{str(e)}")

    def _on_export_completed(self, file_path: str):
        """Maneja la finalización de la exportación"""
        logger.info(f"Exportación completada: {file_path}")

    def on_import_project(self):
        """Maneja la importación de un proyecto"""
        try:
            from src.views.dialogs.project_import_dialog import ProjectImportDialog

            dialog = ProjectImportDialog(
                export_manager=self.export_manager,
                parent=self
            )

            dialog.import_completed.connect(self._on_import_completed)
            dialog.exec()

        except Exception as e:
            logger.error(f"Error abriendo diálogo de importación: {e}")
            QMessageBox.critical(self, "Error", f"Error:\n{str(e)}")

    def _on_import_completed(self, project_id: int):
        """Maneja la finalización de la importación"""
        logger.info(f"Importación completada: Proyecto ID {project_id}")

        # Recargar lista de proyectos
        self.load_projects()

        # Seleccionar el proyecto importado
        self.load_project(project_id)

    def on_save(self):
        """Guarda cambios (placeholder)"""
        QMessageBox.information(self, "Info", "Los cambios se guardan automáticamente")

    def closeEvent(self, event):
        """Al cerrar la ventana"""
        logger.info("ProjectsWindow closed")
        self.closed.emit()
        event.accept()
