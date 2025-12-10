"""
Widget para campo individual de item en el Creador Masivo

Componentes:
- Campo de texto para contenido
- ComboBox para tipo (TEXT, CODE, URL, PATH)
- Botón de eliminar
- Auto-detección de tipo opcional
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QComboBox, QPushButton, QLabel
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
from src.core.item_validation_service import ItemValidationService
import logging

logger = logging.getLogger(__name__)


class ItemFieldWidget(QWidget):
    """
    Widget para un campo individual de item

    Señales:
        content_changed: Emitida cuando cambia el contenido (str)
        type_changed: Emitida cuando cambia el tipo (str)
        remove_requested: Emitida cuando se solicita eliminar
    """

    # Señales
    content_changed = pyqtSignal(str)  # nuevo contenido
    type_changed = pyqtSignal(str)  # nuevo tipo
    remove_requested = pyqtSignal()  # solicitud de eliminación

    # Tipos de items disponibles
    ITEM_TYPES = ['TEXT', 'CODE', 'URL', 'PATH']

    def __init__(self, content: str = '', item_type: str = 'TEXT',
                 auto_detect: bool = True, parent=None):
        """
        Inicializa el widget de campo de item

        Args:
            content: Contenido inicial
            item_type: Tipo inicial (TEXT, CODE, URL, PATH)
            auto_detect: Habilitar auto-detección de tipo
            parent: Widget padre
        """
        super().__init__(parent)
        self.auto_detect_enabled = auto_detect
        self._setup_ui()
        self._apply_styles()
        self.set_content(content)
        self.set_type(item_type)
        self._connect_signals()

    def _setup_ui(self):
        """Configura la interfaz del widget"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(10)

        # Campo de texto para contenido
        self.content_input = QLineEdit()
        self.content_input.setPlaceholderText("Ingrese el contenido del item...")
        self.content_input.setMinimumHeight(40)

        # Indicador de tipo (emoji)
        self.type_indicator = QLabel()
        self.type_indicator.setFixedWidth(30)
        self.type_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(16)
        self.type_indicator.setFont(font)

        # ComboBox de tipo
        self.type_combo = QComboBox()
        self.type_combo.addItems(self.ITEM_TYPES)
        self.type_combo.setFixedWidth(100)
        self.type_combo.setMinimumHeight(40)

        # Botón eliminar
        self.remove_btn = QPushButton("✖")
        self.remove_btn.setFixedSize(35, 35)
        self.remove_btn.setToolTip("Eliminar item")

        # Agregar a layout
        layout.addWidget(self.type_indicator)
        layout.addWidget(self.content_input, 1)  # Stretch factor 1
        layout.addWidget(self.type_combo)
        layout.addWidget(self.remove_btn)

    def _apply_styles(self):
        """Aplica estilos CSS al widget"""
        self.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #2196F3;
                background-color: #353535;
            }
            QLineEdit::placeholder {
                color: #888;
            }
            QComboBox {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 8px;
                font-size: 12px;
            }
            QComboBox:hover {
                background-color: #4d4d4d;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #888;
                width: 0;
                height: 0;
            }
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
            QPushButton:pressed {
                background-color: #8b0000;
            }
        """)

    def _connect_signals(self):
        """Conecta señales internas"""
        self.content_input.textChanged.connect(self._on_content_changed)
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        self.remove_btn.clicked.connect(self.remove_requested.emit)

    def _on_content_changed(self, text: str):
        """Callback cuando cambia el contenido"""
        # Auto-detectar tipo si está habilitado y el campo no está vacío
        if self.auto_detect_enabled and text.strip():
            detected_type = ItemValidationService.auto_detect_type(text)
            if detected_type != self.get_type():
                # Actualizar tipo sin emitir señal para evitar loops
                self.type_combo.blockSignals(True)
                self.set_type(detected_type)
                self.type_combo.blockSignals(False)
                logger.debug(f"Auto-detectado tipo {detected_type} para: {text[:30]}...")

        # Emitir señal de cambio
        self.content_changed.emit(text)

    def _on_type_changed(self, item_type: str):
        """Callback cuando cambia el tipo"""
        # Actualizar indicador visual
        self._update_type_indicator(item_type)

        # Emitir señal
        self.type_changed.emit(item_type)

    def _update_type_indicator(self, item_type: str):
        """Actualiza el emoji indicador de tipo"""
        icon = ItemValidationService.get_type_icon(item_type)
        self.type_indicator.setText(icon)
        tooltip = ItemValidationService.get_type_description(item_type)
        self.type_indicator.setToolTip(tooltip)

    def get_content(self) -> str:
        """
        Obtiene el contenido actual

        Returns:
            Contenido del campo
        """
        return self.content_input.text().strip()

    def set_content(self, content: str):
        """
        Establece el contenido

        Args:
            content: Nuevo contenido
        """
        self.content_input.setText(content)

    def get_type(self) -> str:
        """
        Obtiene el tipo actual

        Returns:
            Tipo de item (TEXT, CODE, URL, PATH)
        """
        return self.type_combo.currentText()

    def set_type(self, item_type: str):
        """
        Establece el tipo

        Args:
            item_type: Nuevo tipo
        """
        if item_type in self.ITEM_TYPES:
            self.type_combo.setCurrentText(item_type)
            self._update_type_indicator(item_type)
        else:
            logger.warning(f"Tipo inválido: {item_type}, usando TEXT")
            self.type_combo.setCurrentText('TEXT')

    def to_dict(self) -> dict:
        """
        Exporta a diccionario

        Returns:
            Dict con content y type
        """
        return {
            'content': self.get_content(),
            'type': self.get_type()
        }

    def from_dict(self, data: dict):
        """
        Importa desde diccionario

        Args:
            data: Dict con content y type
        """
        self.set_content(data.get('content', ''))
        self.set_type(data.get('type', 'TEXT'))

    def is_empty(self) -> bool:
        """
        Verifica si el campo está vacío

        Returns:
            True si no tiene contenido
        """
        return not self.get_content()

    def validate(self) -> tuple[bool, str]:
        """
        Valida el contenido según el tipo

        Returns:
            Tupla (is_valid, error_message)
        """
        content = self.get_content()
        item_type = self.get_type()

        if not content:
            return False, "El campo está vacío"

        return ItemValidationService.validate_item(content, item_type)

    def set_auto_detect(self, enabled: bool):
        """
        Habilita/deshabilita auto-detección de tipo

        Args:
            enabled: True para habilitar
        """
        self.auto_detect_enabled = enabled
        logger.debug(f"Auto-detección {'habilitada' if enabled else 'deshabilitada'}")

    def focus_content(self):
        """Pone foco en el campo de contenido"""
        self.content_input.setFocus()

    def clear(self):
        """Limpia el contenido del campo"""
        self.content_input.clear()

    def set_placeholder(self, text: str):
        """
        Establece el texto del placeholder

        Args:
            text: Texto del placeholder
        """
        self.content_input.setPlaceholderText(text)

    def set_error_state(self, error: bool, message: str = ""):
        """
        Establece estado de error visual

        Args:
            error: True para mostrar error
            message: Mensaje de error (tooltip)
        """
        if error:
            self.content_input.setStyleSheet("""
                QLineEdit {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 2px solid #d32f2f;
                    border-radius: 5px;
                    padding: 8px 12px;
                    font-size: 13px;
                }
            """)
            if message:
                self.content_input.setToolTip(f"❌ {message}")
        else:
            # Resetear a estilo normal
            self._apply_styles()
            self.content_input.setToolTip("")

    def __repr__(self) -> str:
        """Representación del widget"""
        content_preview = self.get_content()[:30] + '...' if len(self.get_content()) > 30 else self.get_content()
        return f"ItemFieldWidget({self.get_type()}): {content_preview}"
