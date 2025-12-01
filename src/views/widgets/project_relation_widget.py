"""
Project Relation Widget - Widget para mostrar relaciones de proyecto

Muestra un elemento (tag, item, category, list, etc.) del proyecto con:
- Icono y nombre del elemento
- Botón clickeable para copiar al portapapeles
- Descripción/comentario (en modo edición)
- Controles de edición y eliminación (en modo edición)
- Botones de reordenamiento (en modo edición)
"""

from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
                             QLabel, QFrame, QTextEdit, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
import logging

logger = logging.getLogger(__name__)


class ProjectRelationWidget(QWidget):
    """Widget para mostrar una relación proyecto-entidad"""

    # Señales
    copy_requested = pyqtSignal(str)  # Emite el contenido a copiar
    delete_requested = pyqtSignal(int)  # Emite relation_id
    edit_description_requested = pyqtSignal(int, str)  # relation_id, new_description
    move_up_requested = pyqtSignal(int)  # relation_id
    move_down_requested = pyqtSignal(int)  # relation_id

    def __init__(self, relation_data: dict, metadata: dict, view_mode: str = 'edit', parent=None):
        """
        Args:
            relation_data: Diccionario con datos de la relación (id, project_id, entity_type, entity_id, description, order_index)
            metadata: Diccionario con metadata de la entidad (icon, name, content, type)
            view_mode: 'edit' o 'clean'
        """
        super().__init__(parent)

        self.relation_data = relation_data
        self.metadata = metadata
        self.view_mode = view_mode

        self.init_ui()

    def init_ui(self):
        """Inicializa la interfaz"""
        # Frame principal
        self.setObjectName("ProjectRelationWidget")

        # Layout principal
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)

        # Container con borde
        container = QFrame()
        container.setFrameStyle(QFrame.Shape.StyledPanel)
        container.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #00ff88;
                border-radius: 4px;
                padding: 4px;
            }
            QFrame:hover {
                border-color: #00ccff;
                background-color: #353535;
            }
        """)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(8, 8, 8, 8)
        container_layout.setSpacing(5)

        # Fila superior: Botón principal + controles
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        # Botón principal del elemento (clickeable para copiar)
        self.main_button = QPushButton(f"{self.metadata['icon']} {self.metadata['name']}")
        self.main_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.main_button.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #4d4d4d;
                border-radius: 4px;
                padding: 8px 12px;
                text-align: left;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00ff88,
                    stop:1 #00ccff
                );
                color: #000000;
                border-color: #00ff88;
            }
            QPushButton:pressed {
                background-color: #2d2d2d;
            }
        """)
        self.main_button.clicked.connect(self.on_copy_clicked)
        top_row.addWidget(self.main_button, 1)

        # Tipo de elemento (pequeño label)
        if self.view_mode == 'edit':
            type_label = QLabel(f"[{self.metadata['type']}]")
            type_label.setStyleSheet("""
                QLabel {
                    color: #888888;
                    font-size: 8pt;
                    font-style: italic;
                }
            """)
            top_row.addWidget(type_label)

        # Controles de edición (solo en modo edición)
        if self.view_mode == 'edit':
            # Botones de reordenamiento
            move_up_btn = QPushButton("▲")
            move_up_btn.setFixedSize(28, 28)
            move_up_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            move_up_btn.setStyleSheet(self._get_control_button_style())
            move_up_btn.setToolTip("Mover arriba")
            move_up_btn.clicked.connect(self.on_move_up)
            top_row.addWidget(move_up_btn)

            move_down_btn = QPushButton("▼")
            move_down_btn.setFixedSize(28, 28)
            move_down_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            move_down_btn.setStyleSheet(self._get_control_button_style())
            move_down_btn.setToolTip("Mover abajo")
            move_down_btn.clicked.connect(self.on_move_down)
            top_row.addWidget(move_down_btn)

            # Botón eliminar
            delete_btn = QPushButton("🗑️")
            delete_btn.setFixedSize(28, 28)
            delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3d3d3d;
                    color: #ffffff;
                    border: 1px solid #4d4d4d;
                    border-radius: 4px;
                    font-size: 10pt;
                }
                QPushButton:hover {
                    background-color: #e4475b;
                    border-color: #e4475b;
                }
            """)
            delete_btn.setToolTip("Eliminar de proyecto")
            delete_btn.clicked.connect(self.on_delete)
            top_row.addWidget(delete_btn)

        container_layout.addLayout(top_row)

        # Descripción/comentario (editable en modo edición)
        description = self.relation_data.get('description', '')
        if description or self.view_mode == 'edit':
            desc_container = QWidget()
            desc_layout = QHBoxLayout(desc_container)
            desc_layout.setContentsMargins(0, 0, 0, 0)
            desc_layout.setSpacing(5)

            if self.view_mode == 'edit':
                # TextEdit editable
                self.description_edit = QTextEdit()
                self.description_edit.setPlainText(description)
                self.description_edit.setMaximumHeight(60)
                self.description_edit.setPlaceholderText("Descripción o comentario del elemento...")
                self.description_edit.setStyleSheet("""
                    QTextEdit {
                        background-color: #252525;
                        color: #888888;
                        border: 1px solid #3d3d3d;
                        border-radius: 3px;
                        padding: 4px;
                        font-size: 9pt;
                        font-style: italic;
                    }
                """)
                self.description_edit.textChanged.connect(self.on_description_changed)
                desc_layout.addWidget(QLabel("└─"), 0)
                desc_layout.addWidget(self.description_edit, 1)
            else:
                # Label solo lectura
                if description:
                    desc_label = QLabel(f"└─ {description}")
                    desc_label.setWordWrap(True)
                    desc_label.setStyleSheet("""
                        QLabel {
                            color: #888888;
                            font-size: 9pt;
                            font-style: italic;
                        }
                    """)
                    desc_layout.addWidget(desc_label)

            container_layout.addWidget(desc_container)

        main_layout.addWidget(container)

    def _get_control_button_style(self) -> str:
        """Estilo para botones de control"""
        return """
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #4d4d4d;
                border-radius: 4px;
                font-size: 9pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00ff88;
                border-color: #00ff88;
                color: #000000;
            }
        """

    def on_copy_clicked(self):
        """Al hacer clic en el botón principal - copiar al portapapeles"""
        # Siempre copiar el nombre del elemento
        name = self.metadata.get('name', '').strip()

        if name:
            self.copy_requested.emit(name)
            logger.info(f"Copy requested (name): {name}")
        else:
            logger.warning(f"No name to copy for: {self.metadata}")

    def on_delete(self):
        """Al hacer clic en eliminar"""
        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Eliminar '{self.metadata['name']}' del proyecto?\n\nEl elemento original NO será eliminado.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            relation_id = self.relation_data['id']
            self.delete_requested.emit(relation_id)
            logger.info(f"Delete requested for relation: {relation_id}")

    def on_description_changed(self):
        """Al cambiar la descripción"""
        if self.view_mode == 'edit' and hasattr(self, 'description_edit'):
            new_description = self.description_edit.toPlainText()
            relation_id = self.relation_data['id']
            self.edit_description_requested.emit(relation_id, new_description)

    def on_move_up(self):
        """Al hacer clic en mover arriba"""
        relation_id = self.relation_data['id']
        self.move_up_requested.emit(relation_id)
        logger.info(f"Move up requested for relation: {relation_id}")

    def on_move_down(self):
        """Al hacer clic en mover abajo"""
        relation_id = self.relation_data['id']
        self.move_down_requested.emit(relation_id)
        logger.info(f"Move down requested for relation: {relation_id}")

    def set_view_mode(self, mode: str):
        """Cambia el modo de vista"""
        if mode != self.view_mode:
            self.view_mode = mode
            # Recrear el widget con el nuevo modo
            self.clear_layout()
            self.init_ui()

    def clear_layout(self):
        """Limpia el layout actual"""
        layout = self.layout()
        if layout:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
