"""
Project Export Dialog - Diálogo para exportar proyectos
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFileDialog, QMessageBox, QTextEdit,
                             QGroupBox, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ProjectExportDialog(QDialog):
    """Diálogo para exportar un proyecto a JSON"""

    export_completed = pyqtSignal(str)  # file_path

    def __init__(self, project_data: dict, export_manager, parent=None):
        super().__init__(parent)

        self.project_data = project_data
        self.export_manager = export_manager
        self.selected_path = None

        self.init_ui()
        self.load_summary()

    def init_ui(self):
        """Inicializa la interfaz"""
        self.setWindowTitle("📤 Exportar Proyecto")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Header
        header = QLabel(f"📤 Exportar: {self.project_data['icon']} {self.project_data['name']}")
        header.setStyleSheet("""
            QLabel {
                font-size: 14pt;
                font-weight: bold;
                color: #00ff88;
                padding: 10px;
            }
        """)
        layout.addWidget(header)

        # Resumen
        summary_group = QGroupBox("📊 Resumen del Proyecto")
        summary_layout = QVBoxLayout(summary_group)

        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(150)
        summary_layout.addWidget(self.summary_text)

        layout.addWidget(summary_group)

        # Opciones de exportación
        options_group = QGroupBox("⚙️ Opciones de Exportación")
        options_layout = QVBoxLayout(options_group)

        self.include_metadata_check = QCheckBox("Incluir metadata de elementos")
        self.include_metadata_check.setChecked(True)
        self.include_metadata_check.setToolTip("Incluye información detallada de cada elemento (recomendado)")
        options_layout.addWidget(self.include_metadata_check)

        layout.addWidget(options_group)

        # Ruta de destino
        path_layout = QHBoxLayout()

        path_label = QLabel("📁 Archivo de destino:")
        path_label.setStyleSheet("font-weight: bold; color: #ffffff;")
        path_layout.addWidget(path_label)

        self.path_display = QLabel("(No seleccionado)")
        self.path_display.setStyleSheet("color: #888888;")
        path_layout.addWidget(self.path_display, 1)

        browse_btn = QPushButton("📂 Examinar...")
        browse_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        browse_btn.clicked.connect(self.on_browse)
        path_layout.addWidget(browse_btn)

        layout.addLayout(path_layout)

        layout.addStretch()

        # Botones
        buttons_layout = QHBoxLayout()

        export_btn = QPushButton("📤 Exportar Proyecto")
        export_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        export_btn.setStyleSheet(self._get_button_style("#00ff88"))
        export_btn.clicked.connect(self.on_export)
        buttons_layout.addWidget(export_btn)

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
                color: #00ff88;
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
            QCheckBox {
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

    def load_summary(self):
        """Carga el resumen del proyecto"""
        try:
            summary = self.export_manager.get_export_summary(self.project_data['id'])

            if not summary:
                self.summary_text.setPlainText("Error obteniendo resumen del proyecto")
                return

            # Construir texto de resumen
            text = f"Proyecto: {summary['project_name']}\n\n"
            text += f"Total de elementos: {summary['total_relations']}\n"

            if summary['relations_by_type']:
                text += "\nElementos por tipo:\n"
                for entity_type, count in summary['relations_by_type'].items():
                    text += f"  • {entity_type}: {count}\n"

            text += f"\nComponentes estructurales: {summary['total_components']}\n"

            if summary['components_by_type']:
                text += "\nComponentes por tipo:\n"
                for comp_type, count in summary['components_by_type'].items():
                    text += f"  • {comp_type}: {count}\n"

            self.summary_text.setPlainText(text)

        except Exception as e:
            logger.error(f"Error cargando resumen: {e}")
            self.summary_text.setPlainText(f"Error: {str(e)}")

    def on_browse(self):
        """Al hacer clic en examinar"""
        # Nombre sugerido
        safe_name = "".join(c for c in self.project_data['name'] if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        default_name = f"proyecto_{safe_name}.json"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Proyecto",
            default_name,
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            self.selected_path = file_path
            self.path_display.setText(file_path)
            self.path_display.setStyleSheet("color: #00ff88;")

    def on_export(self):
        """Al hacer clic en exportar"""
        try:
            # Verificar si hay ruta seleccionada
            if not self.selected_path:
                # Usar ruta por defecto
                safe_name = "".join(c for c in self.project_data['name'] if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_name = safe_name.replace(' ', '_')
                self.selected_path = f"proyecto_{safe_name}.json"

            # Exportar
            result = self.export_manager.export_project(
                self.project_data['id'],
                self.selected_path
            )

            if result:
                logger.info(f"Proyecto exportado exitosamente: {result}")
                self.export_completed.emit(result)

                QMessageBox.information(
                    self,
                    "Exportación Exitosa",
                    f"Proyecto exportado a:\n{result}"
                )
                self.accept()
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "No se pudo exportar el proyecto. Revisa el log para más detalles."
                )

        except Exception as e:
            logger.error(f"Error en exportación: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Error al exportar:\n{str(e)}"
            )
