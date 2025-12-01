"""
Quick Create Dialog
Dialog for quick creation of items or categories
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QInputDialog, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from views.item_editor_dialog import ItemEditorDialog

logger = logging.getLogger(__name__)


class QuickCreateDialog(QDialog):
    """
    Dialog for quick creation of items or categories
    Shows two main options: Create Item and Create Category
    """

    # Signal emitted when data changes (item or category created)
    data_changed = pyqtSignal()
    item_created_signal = pyqtSignal(int, int)  # item_id, category_id

    def __init__(self, controller=None, parent=None):
        """
        Initialize quick create dialog

        Args:
            controller: MainController instance OR DBManager instance
            parent: Parent widget
        """
        super().__init__(parent)

        # Soportar tanto controller como db_manager directo
        from database.db_manager import DBManager

        if isinstance(controller, DBManager):
            # Se pasó un DBManager directo - crear mock controller
            self.db = controller

            # Crear objeto mock para que ItemEditorDialog funcione
            class MockConfigManager:
                def __init__(self, db):
                    self.db = db

            class MockController:
                def __init__(self, db):
                    self.config_manager = MockConfigManager(db)

                def invalidate_filter_cache(self):
                    pass  # No-op en contexto de proyecto

            self.controller = MockController(controller)
        else:
            # Se pasó un controller (comportamiento original)
            self.controller = controller
            self.db = controller.config_manager.db if controller else None

        # Rastrear último item/categoría creado
        self.last_created_item_id = None
        self.last_created_category_id = None

        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("Creación Rápida")
        self.setFixedSize(400, 250)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title_label = QLabel("¿Qué deseas crear?")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        # Buttons layout
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(15)

        # Create Item button
        self.create_item_button = QPushButton("📝 Crear Item")
        self.create_item_button.setFixedHeight(60)
        self.create_item_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.create_item_button.clicked.connect(self.create_item)
        buttons_layout.addWidget(self.create_item_button)

        # Create Category button
        self.create_category_button = QPushButton("📁 Crear Categoría")
        self.create_category_button.setFixedHeight(60)
        self.create_category_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.create_category_button.clicked.connect(self.create_category)
        buttons_layout.addWidget(self.create_category_button)

        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)
        self.apply_styles()

    def apply_styles(self):
        """Apply styles to the dialog"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #252525;
                color: #ffffff;
                border: 2px solid #00d4ff;
                border-radius: 8px;
                font-size: 14pt;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00d4ff,
                    stop:1 #00ff88
                );
                color: #000000;
                border: 2px solid #00ff88;
            }
            QPushButton:pressed {
                background-color: #00d4ff;
                color: #000000;
            }
        """)

    def create_item(self):
        """Create a new item - first select category"""
        if not self.db:
            QMessageBox.warning(
                self,
                "Error",
                "No se pudo acceder a la base de datos."
            )
            return

        try:
            # Get all categories
            categories = self.db.get_categories()

            if not categories:
                QMessageBox.information(
                    self,
                    "Sin Categorías",
                    "No hay categorías disponibles. Crea una categoría primero."
                )
                return

            # Create category selection dialog
            category_dialog = QDialog(self)
            category_dialog.setWindowTitle("Seleccionar Categoría")
            category_dialog.setFixedSize(350, 150)

            dialog_layout = QVBoxLayout()
            dialog_layout.setSpacing(15)
            dialog_layout.setContentsMargins(20, 20, 20, 20)

            # Label
            label = QLabel("Selecciona la categoría para el nuevo item:")
            dialog_layout.addWidget(label)

            # Category combo box
            category_combo = QComboBox()
            for category in categories:
                # Handle both dict and object types
                if isinstance(category, dict):
                    cat_id = category['id']
                    cat_name = category['name']
                    cat_icon = category.get('icon', '📁')
                else:
                    cat_id = category.id
                    cat_name = category.name
                    cat_icon = getattr(category, 'icon', '📁')

                category_combo.addItem(f"{cat_icon} {cat_name}", cat_id)

            dialog_layout.addWidget(category_combo)

            # Buttons
            buttons_layout = QHBoxLayout()
            ok_button = QPushButton("Aceptar")
            cancel_button = QPushButton("Cancelar")

            ok_button.clicked.connect(category_dialog.accept)
            cancel_button.clicked.connect(category_dialog.reject)

            buttons_layout.addWidget(ok_button)
            buttons_layout.addWidget(cancel_button)
            dialog_layout.addLayout(buttons_layout)

            category_dialog.setLayout(dialog_layout)
            category_dialog.setStyleSheet("""
                QDialog {
                    background-color: #1e1e1e;
                }
                QLabel {
                    color: #ffffff;
                    font-size: 10pt;
                }
                QComboBox {
                    background-color: #252525;
                    color: #ffffff;
                    border: 1px solid #00d4ff;
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 10pt;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox::down-arrow {
                    image: none;
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-top: 6px solid #00d4ff;
                    margin-right: 8px;
                }
                QComboBox QAbstractItemView {
                    background-color: #252525;
                    color: #ffffff;
                    selection-background-color: #00d4ff;
                    selection-color: #000000;
                    border: 1px solid #00d4ff;
                }
                QPushButton {
                    background-color: #252525;
                    color: #ffffff;
                    border: 1px solid #00d4ff;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-size: 10pt;
                }
                QPushButton:hover {
                    background-color: #00d4ff;
                    color: #000000;
                }
            """)

            # Show category selection dialog
            if category_dialog.exec() == QDialog.DialogCode.Accepted:
                selected_category_id = category_combo.currentData()

                # Open ItemEditorDialog
                item_editor = ItemEditorDialog(
                    item=None,  # New item
                    category_id=selected_category_id,
                    controller=self.controller,
                    parent=self
                )

                # Connect signals
                item_editor.item_created.connect(self.on_item_created)

                # Show dialog
                item_editor.exec()

        except Exception as e:
            logger.error(f"Error creating item: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al crear el item: {str(e)}"
            )

    def create_category(self):
        """Create a new category with optional tags"""
        if not self.controller:
            QMessageBox.warning(
                self,
                "Error",
                "No se pudo acceder al controlador."
            )
            return

        # Create custom dialog for category with tags
        category_dialog = QDialog(self)
        category_dialog.setWindowTitle("Nueva Categoría")
        category_dialog.setFixedSize(450, 280)

        dialog_layout = QVBoxLayout()
        dialog_layout.setSpacing(10)
        dialog_layout.setContentsMargins(25, 25, 25, 25)

        # Name label and input
        name_label = QLabel("Nombre de la categoría:")
        dialog_layout.addWidget(name_label)

        from PyQt6.QtWidgets import QLineEdit
        name_input = QLineEdit()
        name_input.setPlaceholderText("Ej: Python, Docker, JavaScript...")
        name_input.setMinimumHeight(35)
        dialog_layout.addWidget(name_input)

        # Add spacing
        dialog_layout.addSpacing(10)

        # Tags label and input (optional)
        tags_label = QLabel("Tags (opcional):")
        dialog_layout.addWidget(tags_label)

        tags_input = QLineEdit()
        tags_input.setPlaceholderText("backend, programacion, desarrollo...")
        tags_input.setMinimumHeight(35)
        dialog_layout.addWidget(tags_input)

        # Add spacing before buttons
        dialog_layout.addSpacing(15)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        ok_button = QPushButton("OK")
        ok_button.setMinimumHeight(40)
        cancel_button = QPushButton("Cancel")
        cancel_button.setMinimumHeight(40)

        ok_button.clicked.connect(category_dialog.accept)
        cancel_button.clicked.connect(category_dialog.reject)

        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        dialog_layout.addLayout(buttons_layout)

        category_dialog.setLayout(dialog_layout)
        category_dialog.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #ffffff;
                font-size: 10pt;
            }
            QLineEdit {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #00d4ff;
                border-radius: 4px;
                padding: 8px;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border: 2px solid #00d4ff;
            }
            QPushButton {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #00d4ff;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 10pt;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #00d4ff;
                color: #000000;
            }
        """)

        # Show dialog
        if category_dialog.exec() != QDialog.DialogCode.Accepted:
            logger.info("Category creation cancelled")
            return

        name = name_input.text().strip()
        tags_text = tags_input.text().strip()

        if not name:
            logger.info("Category creation cancelled - empty name")
            return

        # Parse tags
        tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()] if tags_text else []

        try:
            logger.info(f"Creating new category: {name} with tags: {tags}")

            # Save directly to database to get real ID
            category_id = self.db.add_category(
                name=name,
                icon="📁",  # Default icon
                is_predefined=False,
                tags=tags
            )

            if not category_id:
                logger.error("Failed to create category in database")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"No se pudo crear la categoría '{name}' en la base de datos."
                )
                return

            logger.info(f"Category created in database with ID: {category_id}")

            # Show success message
            tags_msg = f"\nTags: {', '.join(tags)}" if tags else ""
            QMessageBox.information(
                self,
                "Éxito",
                f"La categoría '{name}' se creó correctamente.{tags_msg}"
            )

            # Emit signal to refresh UI
            self.data_changed.emit()

        except Exception as e:
            logger.error(f"Error creating category: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al crear la categoría: {str(e)}"
            )


    def on_item_created(self, category_id: str):
        """Handle item created signal"""
        logger.info(f"Item created in category {category_id}")

        # Obtener el último item creado en esta categoría
        try:
            cat_id = int(category_id)
            items = self.db.get_items_by_category(cat_id)
            if items:
                # El último item en la lista es el recién creado
                last_item = items[-1]
                self.last_created_item_id = last_item['id']
                self.last_created_category_id = cat_id
                logger.info(f"Last created item ID: {self.last_created_item_id}")

                # Emitir señal con el item_id y category_id
                self.item_created_signal.emit(self.last_created_item_id, cat_id)
        except Exception as e:
            logger.error(f"Error getting last created item: {e}")

        self.data_changed.emit()
