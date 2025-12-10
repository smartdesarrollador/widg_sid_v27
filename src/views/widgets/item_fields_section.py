"""
Widget de sección de campos de items para el Creador Masivo

Componentes:
- Contenedor scrollable de ItemFieldWidget
- Botón + para agregar nuevos items
- Gestión dinámica de items (mínimo 1)
- Validación de todos los items
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
from src.views.widgets.item_field_widget import ItemFieldWidget
import logging

logger = logging.getLogger(__name__)


class ItemFieldsSection(QWidget):
    """
    Sección de campos de items para el Creador Masivo

    Permite agregar/eliminar múltiples items dinámicamente.
    Cada item tiene contenido y tipo individual.

    Señales:
        items_changed: Emitida cuando cambia la cantidad de items (int)
        item_content_changed: Emitida cuando cambia el contenido de un item (int, str)
        item_type_changed: Emitida cuando cambia el tipo de un item (int, str)
    """

    # Señales
    items_changed = pyqtSignal(int)  # Cantidad de items
    item_content_changed = pyqtSignal(int, str)  # index, content
    item_type_changed = pyqtSignal(int, str)  # index, type

    def __init__(self, parent=None):
        """Inicializa la sección de campos de items"""
        super().__init__(parent)
        self.item_widgets: list[ItemFieldWidget] = []
        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

        # Agregar primer item por defecto
        self.add_item_field()

    def _setup_ui(self):
        """Configura la interfaz del widget"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Título con contador y botón agregar
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        title = QLabel("📝 Items")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)

        self.count_label = QLabel("(0)")
        self.count_label.setStyleSheet("color: #888; font-size: 11px;")
        header_layout.addWidget(self.count_label)

        header_layout.addStretch()

        self.add_btn = QPushButton("+ Agregar Item")
        self.add_btn.setFixedHeight(35)
        self.add_btn.setToolTip("Agregar nuevo campo de item")
        header_layout.addWidget(self.add_btn)

        layout.addLayout(header_layout)

        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #444;")
        layout.addWidget(separator)

        # Área scrollable para items
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #555;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666;
            }
        """)

        # Widget contenedor de items
        self.items_container = QWidget()
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(0, 0, 10, 0)  # Margen derecho para scrollbar
        self.items_layout.setSpacing(10)
        self.items_layout.addStretch()  # Push items to top

        scroll_area.setWidget(self.items_container)
        layout.addWidget(scroll_area)

    def _apply_styles(self):
        """Aplica estilos CSS al widget"""
        self.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QLabel {
                color: #ffffff;
            }
        """)

    def _connect_signals(self):
        """Conecta señales internas"""
        self.add_btn.clicked.connect(lambda: self.add_item_field())

    def add_item_field(self, content: str = '', item_type: str = 'TEXT'):
        """
        Agrega un nuevo campo de item

        Args:
            content: Contenido inicial
            item_type: Tipo inicial (TEXT, CODE, URL, PATH)
        """
        # Crear widget de item
        item_widget = ItemFieldWidget(content, item_type, auto_detect=True)

        # Conectar señales
        index = len(self.item_widgets)
        item_widget.content_changed.connect(
            lambda text, idx=index: self.item_content_changed.emit(idx, text)
        )
        item_widget.type_changed.connect(
            lambda typ, idx=index: self.item_type_changed.emit(idx, typ)
        )
        item_widget.remove_requested.connect(
            lambda widget=item_widget: self.remove_item_field(widget)
        )

        # Agregar a lista y layout (antes del stretch)
        self.item_widgets.append(item_widget)
        self.items_layout.insertWidget(self.items_layout.count() - 1, item_widget)

        # Actualizar contador
        self._update_count()

        # Focus en el nuevo campo
        item_widget.focus_content()

        logger.debug(f"Campo de item agregado (total: {len(self.item_widgets)})")

    def remove_item_field(self, widget: ItemFieldWidget):
        """
        Elimina un campo de item

        Args:
            widget: Widget a eliminar
        """
        # No permitir eliminar si solo hay 1 item
        if len(self.item_widgets) <= 1:
            logger.warning("No se puede eliminar el último item")
            return

        # Eliminar de lista y layout
        if widget in self.item_widgets:
            self.item_widgets.remove(widget)
            self.items_layout.removeWidget(widget)
            widget.deleteLater()

            # Actualizar contador
            self._update_count()

            logger.debug(f"Campo de item eliminado (total: {len(self.item_widgets)})")

    def _update_count(self):
        """Actualiza el contador de items"""
        count = self.get_items_count()
        self.count_label.setText(f"({count})")
        self.items_changed.emit(count)

    def get_items_count(self) -> int:
        """
        Obtiene la cantidad de items con contenido

        Returns:
            Cantidad de items no vacíos
        """
        return sum(1 for widget in self.item_widgets if not widget.is_empty())

    def get_total_fields(self) -> int:
        """
        Obtiene la cantidad total de campos (vacíos o no)

        Returns:
            Total de campos
        """
        return len(self.item_widgets)

    def get_items_data(self) -> list[dict]:
        """
        Obtiene los datos de todos los items

        Returns:
            Lista de dicts con content y type
        """
        return [widget.to_dict() for widget in self.item_widgets]

    def get_non_empty_items(self) -> list[dict]:
        """
        Obtiene solo los items con contenido

        Returns:
            Lista de dicts con content y type (solo no vacíos)
        """
        return [
            widget.to_dict()
            for widget in self.item_widgets
            if not widget.is_empty()
        ]

    def set_items_data(self, items_data: list[dict]):
        """
        Establece los items desde datos

        Args:
            items_data: Lista de dicts con content y type
        """
        # Limpiar items existentes manualmente
        for widget in self.item_widgets[:]:
            self.items_layout.removeWidget(widget)
            widget.deleteLater()

        self.item_widgets.clear()

        # Agregar items desde datos
        if not items_data:
            # Agregar al menos 1 item vacío
            self.add_item_field()
        else:
            for item_data in items_data:
                self.add_item_field(
                    content=item_data.get('content', ''),
                    item_type=item_data.get('type', 'TEXT')
                )

    def clear_all_items(self):
        """Limpia todos los items (deja solo 1 vacío)"""
        # Eliminar todos los widgets
        for widget in self.item_widgets[:]:
            self.items_layout.removeWidget(widget)
            widget.deleteLater()

        self.item_widgets.clear()

        # Agregar 1 item vacío
        self.add_item_field()

        logger.debug("Todos los items limpiados")

    def validate_all(self) -> tuple[bool, list[tuple[int, str]]]:
        """
        Valida todos los items

        Returns:
            Tupla (all_valid, list of (index, error_message))
        """
        errors = []

        for index, widget in enumerate(self.item_widgets):
            if widget.is_empty():
                continue  # Items vacíos se ignoran

            is_valid, error_msg = widget.validate()
            if not is_valid:
                errors.append((index, error_msg))
                widget.set_error_state(True, error_msg)
            else:
                widget.set_error_state(False)

        all_valid = len(errors) == 0

        if all_valid:
            logger.debug(f"Validación exitosa: {self.get_items_count()} items válidos")
        else:
            logger.warning(f"Validación fallida: {len(errors)} errores")

        return all_valid, errors

    def clear_validation_errors(self):
        """Limpia los estados de error de validación"""
        for widget in self.item_widgets:
            widget.set_error_state(False)

    def focus_first_item(self):
        """Pone foco en el primer campo de item"""
        if self.item_widgets:
            self.item_widgets[0].focus_content()

    def focus_item(self, index: int):
        """
        Pone foco en un item específico

        Args:
            index: Índice del item
        """
        if 0 <= index < len(self.item_widgets):
            self.item_widgets[index].focus_content()

    def set_auto_detect(self, enabled: bool):
        """
        Habilita/deshabilita auto-detección de tipo en todos los items

        Args:
            enabled: True para habilitar
        """
        for widget in self.item_widgets:
            widget.set_auto_detect(enabled)

        logger.debug(f"Auto-detección {'habilitada' if enabled else 'deshabilitada'} en todos los items")

    def to_list(self) -> list[dict]:
        """
        Exporta a lista de diccionarios

        Returns:
            Lista de items con content y type
        """
        return self.get_non_empty_items()

    def from_list(self, items_data: list[dict]):
        """
        Importa desde lista de diccionarios

        Args:
            items_data: Lista de items con content y type
        """
        self.set_items_data(items_data)

    def __repr__(self) -> str:
        """Representación del widget"""
        non_empty = self.get_items_count()
        total = self.get_total_fields()
        return f"ItemFieldsSection(items={non_empty}/{total})"
