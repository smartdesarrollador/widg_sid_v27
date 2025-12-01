"""
Project Editor Dialog - Diálogo para editar información de un proyecto
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QTextEdit, QColorDialog,
                             QMessageBox, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor
import logging

logger = logging.getLogger(__name__)


class ProjectEditorDialog(QDialog):
    """Diálogo para editar información de un proyecto"""

    project_updated = pyqtSignal(int)  # project_id

    def __init__(self, project_data: dict, db_manager, parent=None):
        """
        Args:
            project_data: Diccionario con datos del proyecto
            db_manager: Instancia de DBManager
        """
        super().__init__(parent)

        self.project_data = project_data
        self.db = db_manager
        self.selected_color = project_data.get('color', '#3498db')

        self.init_ui()

    def init_ui(self):
        """Inicializa la interfaz"""
        self.setWindowTitle("✏️ Editar Proyecto")
        self.setMinimumSize(500, 400)

        # Layout principal
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Header
        header = QLabel("✏️ Editar Proyecto")
        header.setStyleSheet("""
            QLabel {
                font-size: 14pt;
                font-weight: bold;
                color: #00ff88;
                padding: 10px;
            }
        """)
        layout.addWidget(header)

        # Nombre
        name_label = QLabel("Nombre del Proyecto:")
        name_label.setStyleSheet("font-weight: bold; color: #ffffff;")
        layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setText(self.project_data.get('name', ''))
        self.name_input.setPlaceholderText("Nombre del proyecto...")
        layout.addWidget(self.name_input)

        # Descripción
        desc_label = QLabel("Descripción:")
        desc_label.setStyleSheet("font-weight: bold; color: #ffffff;")
        layout.addWidget(desc_label)

        self.description_input = QTextEdit()
        self.description_input.setPlainText(self.project_data.get('description', ''))
        self.description_input.setPlaceholderText("Descripción del proyecto...")
        self.description_input.setMaximumHeight(100)
        layout.addWidget(self.description_input)

        # Color e Icono
        color_icon_layout = QHBoxLayout()

        # Color
        color_container = QVBoxLayout()
        color_label = QLabel("Color:")
        color_label.setStyleSheet("font-weight: bold; color: #ffffff;")
        color_container.addWidget(color_label)

        color_row = QHBoxLayout()
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(50, 50)
        self.color_preview.setStyleSheet(f"""
            QFrame {{
                background-color: {self.selected_color};
                border: 2px solid #ffffff;
                border-radius: 4px;
            }}
        """)
        color_row.addWidget(self.color_preview)

        color_btn = QPushButton("🎨 Cambiar Color")
        color_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        color_btn.clicked.connect(self.on_change_color)
        color_row.addWidget(color_btn)
        color_row.addStretch()

        color_container.addLayout(color_row)
        color_icon_layout.addLayout(color_container, 1)

        # Icono
        icon_container = QVBoxLayout()
        icon_label = QLabel("Icono (Emoji):")
        icon_label.setStyleSheet("font-weight: bold; color: #ffffff;")
        icon_container.addWidget(icon_label)

        self.icon_input = QLineEdit()
        self.icon_input.setText(self.project_data.get('icon', '📁'))
        self.icon_input.setMaxLength(4)
        self.icon_input.setPlaceholderText("📁")
        self.icon_input.setStyleSheet("font-size: 24pt; text-align: center;")
        self.icon_input.setFixedWidth(100)
        icon_container.addWidget(self.icon_input)

        color_icon_layout.addLayout(icon_container, 1)

        layout.addLayout(color_icon_layout)

        # Iconos sugeridos
        suggestions_label = QLabel("Iconos sugeridos:")
        suggestions_label.setStyleSheet("color: #888888; font-size: 9pt;")
        layout.addWidget(suggestions_label)

        icons_row = QHBoxLayout()
        suggested_icons = ['📁', '🛒', '💼', '🎯', '🚀', '⚡', '🔧', '📱', '🌐', '💡', '🎨', '📊']
        for icon in suggested_icons:
            icon_btn = QPushButton(icon)
            icon_btn.setFixedSize(35, 35)
            icon_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            icon_btn.setStyleSheet("""
                QPushButton {
                    font-size: 18pt;
                    background-color: #2d2d2d;
                    border: 1px solid #3d3d3d;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #3d3d3d;
                    border-color: #00ff88;
                }
            """)
            icon_btn.clicked.connect(lambda checked, i=icon: self.icon_input.setText(i))
            icons_row.addWidget(icon_btn)

        icons_row.addStretch()
        layout.addLayout(icons_row)

        layout.addStretch()

        # Botones
        buttons_layout = QHBoxLayout()

        delete_btn = QPushButton("🗑️ Eliminar Proyecto")
        delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        delete_btn.setStyleSheet(self._get_button_style("#e74c3c"))
        delete_btn.clicked.connect(self.on_delete_project)
        buttons_layout.addWidget(delete_btn)

        buttons_layout.addStretch()

        save_btn = QPushButton("💾 Guardar Cambios")
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_btn.setStyleSheet(self._get_button_style("#00ff88"))
        save_btn.clicked.connect(self.on_save)
        buttons_layout.addWidget(save_btn)

        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.setStyleSheet(self._get_button_style("#888888"))
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

        # Styling general
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #ffffff;
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
        """)

    def _get_button_style(self, color: str) -> str:
        """Retorna estilo para botones"""
        return f"""
            QPushButton {{
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid {color};
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 10pt;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {color};
                color: #000000;
            }}
        """

    def on_change_color(self):
        """Al hacer clic en cambiar color"""
        current_color = QColor(self.selected_color)
        color = QColorDialog.getColor(current_color, self, "Seleccionar Color")

        if color.isValid():
            self.selected_color = color.name()
            self.color_preview.setStyleSheet(f"""
                QFrame {{
                    background-color: {self.selected_color};
                    border: 2px solid #ffffff;
                    border-radius: 4px;
                }}
            """)

    def on_save(self):
        """Al hacer clic en guardar"""
        name = self.name_input.text().strip()
        description = self.description_input.toPlainText().strip()
        icon = self.icon_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Error", "El nombre del proyecto es requerido")
            return

        try:
            # Actualizar proyecto
            success = self.db.update_project(
                self.project_data['id'],
                name=name,
                description=description,
                color=self.selected_color,
                icon=icon if icon else '📁'
            )

            if success:
                logger.info(f"Project {self.project_data['id']} updated")
                self.project_updated.emit(self.project_data['id'])
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "No se pudo actualizar el proyecto")

        except Exception as e:
            logger.error(f"Error updating project: {e}")
            QMessageBox.critical(self, "Error", f"Error al actualizar:\n{str(e)}")

    def on_delete_project(self):
        """Al hacer clic en eliminar proyecto"""
        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Eliminar el proyecto '{self.project_data['name']}'?\n\n"
            "Esto eliminará todas las relaciones y componentes del proyecto.\n"
            "Los elementos originales (items, tags, etc.) NO serán eliminados.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.db.delete_project(self.project_data['id'])
                if success:
                    logger.info(f"Project {self.project_data['id']} deleted")
                    QMessageBox.information(self, "Éxito", "Proyecto eliminado")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Error", "No se pudo eliminar el proyecto")

            except Exception as e:
                logger.error(f"Error deleting project: {e}")
                QMessageBox.critical(self, "Error", f"Error al eliminar:\n{str(e)}")
