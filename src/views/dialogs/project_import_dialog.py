"""
Project Import Dialog - Diálogo para importar proyectos
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFileDialog, QMessageBox, QTextEdit,
                             QGroupBox, QRadioButton, QButtonGroup)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
import logging
import json

logger = logging.getLogger(__name__)


class ProjectImportDialog(QDialog):
    """Diálogo para importar un proyecto desde JSON"""

    import_completed = pyqtSignal(int)  # project_id

    def __init__(self, export_manager, parent=None):
        super().__init__(parent)

        self.export_manager = export_manager
        self.selected_file = None
        self.file_data = None

        self.init_ui()

    def init_ui(self):
        """Inicializa la interfaz"""
        self.setWindowTitle("📥 Importar Proyecto")
        self.setMinimumSize(500, 450)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Header
        header = QLabel("📥 Importar Proyecto desde JSON")
        header.setStyleSheet("""
            QLabel {
                font-size: 14pt;
                font-weight: bold;
                color: #00ccff;
                padding: 10px;
            }
        """)
        layout.addWidget(header)

        # Selección de archivo
        file_group = QGroupBox("📁 Archivo a Importar")
        file_layout = QVBoxLayout(file_group)

        file_row = QHBoxLayout()

        self.file_display = QLabel("(No seleccionado)")
        self.file_display.setStyleSheet("color: #888888;")
        file_row.addWidget(self.file_display, 1)

        browse_btn = QPushButton("📂 Examinar...")
        browse_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        browse_btn.clicked.connect(self.on_browse)
        file_row.addWidget(browse_btn)

        file_layout.addLayout(file_row)

        layout.addWidget(file_group)

        # Vista previa
        preview_group = QGroupBox("👁️ Vista Previa del Archivo")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setPlaceholderText("Selecciona un archivo para ver su contenido...")
        preview_layout.addWidget(self.preview_text)

        layout.addWidget(preview_group)

        # Opciones de importación
        options_group = QGroupBox("⚙️ Opciones de Importación")
        options_layout = QVBoxLayout(options_group)

        self.mode_group = QButtonGroup(self)

        self.new_project_radio = QRadioButton("Crear como nuevo proyecto")
        self.new_project_radio.setChecked(True)
        self.new_project_radio.setToolTip("Crea un nuevo proyecto con los datos importados")
        self.mode_group.addButton(self.new_project_radio, 0)
        options_layout.addWidget(self.new_project_radio)

        info_label = QLabel("ℹ️ Nota: Solo se importarán relaciones de elementos que existan en la base de datos")
        info_label.setStyleSheet("color: #888888; font-size: 9pt; font-style: italic;")
        info_label.setWordWrap(True)
        options_layout.addWidget(info_label)

        layout.addWidget(options_group)

        layout.addStretch()

        # Botones
        buttons_layout = QHBoxLayout()

        import_btn = QPushButton("📥 Importar Proyecto")
        import_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        import_btn.setStyleSheet(self._get_button_style("#00ccff"))
        import_btn.clicked.connect(self.on_import)
        buttons_layout.addWidget(import_btn)

        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.setStyleSheet(self._get_button_style("#888888"))
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

        # Styling
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #ffffff;
            }
            QGroupBox {
                color: #00ccff;
                font-weight: bold;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QTextEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
            }
            QRadioButton {
                color: #ffffff;
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

    def on_browse(self):
        """Al hacer clic en examinar"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Archivo de Proyecto",
            "",
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            self.selected_file = file_path
            self.file_display.setText(file_path)
            self.file_display.setStyleSheet("color: #00ccff;")

            # Cargar preview
            self.load_preview()

    def load_preview(self):
        """Carga la vista previa del archivo"""
        if not self.selected_file:
            return

        try:
            with open(self.selected_file, 'r', encoding='utf-8') as f:
                self.file_data = json.load(f)

            # Construir preview
            text = ""

            if 'project' in self.file_data:
                proj = self.file_data['project']
                text += f"Proyecto: {proj.get('icon', '📁')} {proj.get('name', 'Sin nombre')}\n"
                text += f"Descripción: {proj.get('description', 'Sin descripción')}\n"
                text += f"Color: {proj.get('color', '#3498db')}\n\n"

            if 'relations' in self.file_data:
                relations = self.file_data['relations']
                text += f"Relaciones: {len(relations)}\n"

                # Contar por tipo
                by_type = {}
                for rel in relations:
                    entity_type = rel.get('entity_type', 'unknown')
                    by_type[entity_type] = by_type.get(entity_type, 0) + 1

                for entity_type, count in by_type.items():
                    text += f"  • {entity_type}: {count}\n"

                text += "\n"

            if 'components' in self.file_data:
                components = self.file_data['components']
                text += f"Componentes: {len(components)}\n"

                # Contar por tipo
                by_type = {}
                for comp in components:
                    comp_type = comp.get('component_type', 'unknown')
                    by_type[comp_type] = by_type.get(comp_type, 0) + 1

                for comp_type, count in by_type.items():
                    text += f"  • {comp_type}: {count}\n"

            if 'export_date' in self.file_data:
                text += f"\nFecha de exportación: {self.file_data['export_date']}"

            self.preview_text.setPlainText(text)

        except Exception as e:
            logger.error(f"Error cargando preview: {e}")
            self.preview_text.setPlainText(f"Error leyendo archivo:\n{str(e)}")

    def on_import(self):
        """Al hacer clic en importar"""
        if not self.selected_file:
            QMessageBox.warning(
                self,
                "Error",
                "Selecciona un archivo JSON para importar"
            )
            return

        try:
            # Importar
            mode = 'new' if self.new_project_radio.isChecked() else 'merge'

            project_id = self.export_manager.import_project(
                self.selected_file,
                import_mode=mode
            )

            if project_id:
                logger.info(f"Proyecto importado exitosamente: ID {project_id}")
                self.import_completed.emit(project_id)

                project_name = self.file_data.get('project', {}).get('name', 'Proyecto')

                QMessageBox.information(
                    self,
                    "Importación Exitosa",
                    f"Proyecto '{project_name}' importado exitosamente.\n\nID: {project_id}"
                )
                self.accept()
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "No se pudo importar el proyecto. Revisa el log para más detalles."
                )

        except Exception as e:
            logger.error(f"Error en importación: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Error al importar:\n{str(e)}"
            )
