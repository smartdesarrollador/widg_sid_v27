"""
Widget de selección de contexto para el Creador Masivo

Componentes:
- Selector de Proyecto con botón +
- Selector de Área con botón +
- Selector de Categoría con botón + (OBLIGATORIO)
- Checkbox "Crear como lista" con campo de nombre
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QCheckBox, QLineEdit, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
import logging

logger = logging.getLogger(__name__)


class SelectorWithCreate(QWidget):
    """
    Widget helper que combina un QComboBox con un botón +

    Señales:
        selection_changed: Emitida cuando cambia la selección (int or None)
        create_clicked: Emitida cuando se hace clic en el botón +
    """

    # Señales
    selection_changed = pyqtSignal(object)  # int ID o None
    create_clicked = pyqtSignal()

    def __init__(self, label_text: str, is_required: bool = False,
                 placeholder: str = "Seleccionar...", parent=None):
        """
        Inicializa el selector con botón de creación

        Args:
            label_text: Texto de la etiqueta
            is_required: Si es campo obligatorio (muestra *)
            placeholder: Texto del placeholder
            parent: Widget padre
        """
        super().__init__(parent)
        self.is_required = is_required
        self._setup_ui(label_text, placeholder)
        self._apply_styles()
        self._connect_signals()

    def _setup_ui(self, label_text: str, placeholder: str):
        """Configura la interfaz del widget"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Etiqueta
        self.label = QLabel(label_text)
        if self.is_required:
            self.label.setText(f"{label_text} *")
            self.label.setStyleSheet("color: #FF5252;")  # Rojo para requerido
        self.label.setFixedWidth(80)

        # ComboBox
        self.combo = QComboBox()
        self.combo.setPlaceholderText(placeholder)
        self.combo.setMinimumHeight(35)

        # Botón crear
        self.create_btn = QPushButton("+")
        self.create_btn.setFixedSize(35, 35)
        self.create_btn.setToolTip(f"Crear nuevo {label_text.lower()}")

        # Agregar a layout
        layout.addWidget(self.label)
        layout.addWidget(self.combo, 1)  # Stretch factor 1
        layout.addWidget(self.create_btn)

    def _apply_styles(self):
        """Aplica estilos CSS al widget"""
        self.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 6px 12px;
                font-size: 13px;
            }
            QComboBox:hover {
                background-color: #353535;
            }
            QComboBox:focus {
                border: 1px solid #2196F3;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #888;
                width: 0;
                height: 0;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: #ffffff;
                selection-background-color: #2196F3;
                border: 1px solid #444;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QLabel {
                color: #ffffff;
                font-size: 13px;
            }
        """)

    def _connect_signals(self):
        """Conecta señales internas"""
        self.combo.currentIndexChanged.connect(self._on_selection_changed)
        self.create_btn.clicked.connect(self.create_clicked.emit)

    def _on_selection_changed(self, index: int):
        """Callback cuando cambia la selección"""
        item_id = self.get_selected_id()
        self.selection_changed.emit(item_id)

    def load_items(self, items: list[tuple[int, str]], include_empty: bool = True):
        """
        Carga items en el combo

        Args:
            items: Lista de tuplas (id, name)
            include_empty: Si incluir opción vacía al inicio
        """
        self.combo.clear()

        if include_empty:
            self.combo.addItem("Ninguno", None)

        for item_id, item_name in items:
            self.combo.addItem(item_name, item_id)

        logger.debug(f"{self.label.text()}: {len(items)} items cargados")

    def get_selected_id(self) -> int | None:
        """
        Obtiene el ID del item seleccionado

        Returns:
            ID del item o None
        """
        return self.combo.currentData()

    def set_selected_id(self, item_id: int | None):
        """
        Establece la selección por ID

        Args:
            item_id: ID a seleccionar
        """
        index = self.combo.findData(item_id)
        if index >= 0:
            self.combo.setCurrentIndex(index)
        else:
            self.combo.setCurrentIndex(0)  # Ninguno

    def clear(self):
        """Limpia la selección"""
        self.combo.setCurrentIndex(0)

    def set_error_state(self, error: bool, message: str = ""):
        """
        Establece estado de error visual

        Args:
            error: True para mostrar error
            message: Mensaje de error (tooltip)
        """
        if error:
            self.combo.setStyleSheet("""
                QComboBox {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 2px solid #d32f2f;
                    border-radius: 5px;
                    padding: 6px 12px;
                    font-size: 13px;
                }
            """)
            if message:
                self.combo.setToolTip(f"❌ {message}")
        else:
            self._apply_styles()
            self.combo.setToolTip("")


class ContextSelectorSection(QWidget):
    """
    Sección de selección de contexto para el Creador Masivo

    Incluye selectores de proyecto, área, categoría y checkbox de lista.

    Señales:
        project_changed: Emitida cuando cambia el proyecto (int or None)
        area_changed: Emitida cuando cambia el área (int or None)
        category_changed: Emitida cuando cambia la categoría (int or None)
        create_as_list_changed: Emitida cuando cambia el checkbox (bool)
        list_name_changed: Emitida cuando cambia el nombre de lista (str)
        create_project_clicked: Emitida cuando se hace clic en crear proyecto
        create_area_clicked: Emitida cuando se hace clic en crear área
        create_category_clicked: Emitida cuando se hace clic en crear categoría
    """

    # Señales
    project_changed = pyqtSignal(object)  # int or None
    area_changed = pyqtSignal(object)  # int or None
    category_changed = pyqtSignal(object)  # int or None
    create_as_list_changed = pyqtSignal(bool)
    list_name_changed = pyqtSignal(str)
    create_project_clicked = pyqtSignal()
    create_area_clicked = pyqtSignal()
    create_category_clicked = pyqtSignal()

    def __init__(self, parent=None):
        """Inicializa la sección de contexto"""
        super().__init__(parent)
        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

    def _setup_ui(self):
        """Configura la interfaz del widget"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Título de sección
        title = QLabel("📋 Contexto")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #444;")
        layout.addWidget(separator)

        # Selector de Proyecto
        self.project_selector = SelectorWithCreate(
            label_text="Proyecto",
            placeholder="Seleccionar proyecto..."
        )
        layout.addWidget(self.project_selector)

        # Selector de Área
        self.area_selector = SelectorWithCreate(
            label_text="Área",
            placeholder="Seleccionar área..."
        )
        layout.addWidget(self.area_selector)

        # Selector de Categoría (OBLIGATORIO)
        self.category_selector = SelectorWithCreate(
            label_text="Categoría",
            is_required=True,
            placeholder="Seleccionar categoría..."
        )
        layout.addWidget(self.category_selector)

        # Checkbox "Crear como lista"
        self.list_checkbox = QCheckBox("Crear como lista")
        self.list_checkbox.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #444;
                border-radius: 3px;
                background-color: #2d2d2d;
            }
            QCheckBox::indicator:checked {
                background-color: #2196F3;
                border-color: #2196F3;
                image: none;
            }
            QCheckBox::indicator:checked:after {
                content: "✓";
                color: white;
            }
        """)
        layout.addWidget(self.list_checkbox)

        # Campo de nombre de lista (inicialmente oculto)
        list_name_layout = QHBoxLayout()
        list_name_layout.setContentsMargins(0, 0, 0, 0)
        list_name_layout.setSpacing(10)

        list_name_label = QLabel("Nombre:")
        list_name_label.setFixedWidth(80)
        list_name_layout.addWidget(list_name_label)

        self.list_name_input = QLineEdit()
        self.list_name_input.setPlaceholderText("Nombre de la lista...")
        self.list_name_input.setMinimumHeight(35)
        self.list_name_input.setVisible(False)
        list_name_label.setVisible(False)
        list_name_layout.addWidget(self.list_name_input)

        self.list_name_label = list_name_label  # Guardar referencia

        layout.addLayout(list_name_layout)

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
            QLabel {
                color: #ffffff;
                font-size: 13px;
            }
        """)

    def _connect_signals(self):
        """Conecta señales internas"""
        # Selectores
        self.project_selector.selection_changed.connect(self.project_changed.emit)
        self.area_selector.selection_changed.connect(self.area_changed.emit)
        self.category_selector.selection_changed.connect(self.category_changed.emit)

        # Botones crear
        self.project_selector.create_clicked.connect(self.create_project_clicked.emit)
        self.area_selector.create_clicked.connect(self.create_area_clicked.emit)
        self.category_selector.create_clicked.connect(self.create_category_clicked.emit)

        # Lista
        self.list_checkbox.stateChanged.connect(self._on_list_checkbox_changed)
        self.list_name_input.textChanged.connect(self.list_name_changed.emit)

    def _on_list_checkbox_changed(self, state: int):
        """Callback cuando cambia el checkbox de lista"""
        is_checked = state == Qt.CheckState.Checked.value

        # Mostrar/ocultar campo de nombre
        self.list_name_input.setVisible(is_checked)
        self.list_name_label.setVisible(is_checked)

        # Emitir señal
        self.create_as_list_changed.emit(is_checked)

        logger.debug(f"Crear como lista: {is_checked}")

    def load_projects(self, projects: list[tuple[int, str]]):
        """
        Carga proyectos en el selector

        Args:
            projects: Lista de tuplas (id, name)
        """
        self.project_selector.load_items(projects)

    def load_areas(self, areas: list[tuple[int, str]]):
        """
        Carga áreas en el selector

        Args:
            areas: Lista de tuplas (id, name)
        """
        self.area_selector.load_items(areas)

    def load_categories(self, categories: list[tuple[int, str]]):
        """
        Carga categorías en el selector

        Args:
            categories: Lista de tuplas (id, name)
        """
        self.category_selector.load_items(categories, include_empty=False)

    def get_project_id(self) -> int | None:
        """Obtiene el ID del proyecto seleccionado"""
        return self.project_selector.get_selected_id()

    def get_area_id(self) -> int | None:
        """Obtiene el ID del área seleccionada"""
        return self.area_selector.get_selected_id()

    def get_category_id(self) -> int | None:
        """Obtiene el ID de la categoría seleccionada"""
        return self.category_selector.get_selected_id()

    def get_create_as_list(self) -> bool:
        """Obtiene el estado del checkbox de lista"""
        return self.list_checkbox.isChecked()

    def get_list_name(self) -> str:
        """Obtiene el nombre de la lista"""
        return self.list_name_input.text().strip()

    def set_project_id(self, project_id: int | None):
        """Establece el proyecto seleccionado"""
        self.project_selector.set_selected_id(project_id)

    def set_area_id(self, area_id: int | None):
        """Establece el área seleccionada"""
        self.area_selector.set_selected_id(area_id)

    def set_category_id(self, category_id: int | None):
        """Establece la categoría seleccionada"""
        self.category_selector.set_selected_id(category_id)

    def set_create_as_list(self, checked: bool):
        """Establece el estado del checkbox de lista"""
        self.list_checkbox.setChecked(checked)
        # Actualizar visibilidad directamente (por si no se procesa la señal)
        self.list_name_input.setVisible(checked)
        self.list_name_label.setVisible(checked)

    def set_list_name(self, name: str):
        """Establece el nombre de la lista"""
        self.list_name_input.setText(name)

    def to_dict(self) -> dict:
        """
        Exporta a diccionario

        Returns:
            Dict con todos los valores
        """
        return {
            'project_id': self.get_project_id(),
            'area_id': self.get_area_id(),
            'category_id': self.get_category_id(),
            'create_as_list': self.get_create_as_list(),
            'list_name': self.get_list_name()
        }

    def from_dict(self, data: dict):
        """
        Importa desde diccionario

        Args:
            data: Dict con valores
        """
        self.set_project_id(data.get('project_id'))
        self.set_area_id(data.get('area_id'))
        self.set_category_id(data.get('category_id'))
        self.set_create_as_list(data.get('create_as_list', False))
        self.set_list_name(data.get('list_name', ''))

    def validate(self) -> tuple[bool, str]:
        """
        Valida el contexto

        Returns:
            Tupla (is_valid, error_message)
        """
        # Categoría es obligatoria
        if self.get_category_id() is None:
            return False, "Debe seleccionar una categoría"

        # Si está marcado crear como lista, necesita nombre
        if self.get_create_as_list():
            if not self.get_list_name():
                return False, "Debe ingresar un nombre para la lista"

        return True, ""

    def clear(self):
        """Limpia todos los campos"""
        self.project_selector.clear()
        self.area_selector.clear()
        self.category_selector.clear()
        self.list_checkbox.setChecked(False)
        self.list_name_input.clear()

    def __repr__(self) -> str:
        """Representación del widget"""
        return (f"ContextSelectorSection(project={self.get_project_id()}, "
                f"area={self.get_area_id()}, category={self.get_category_id()}, "
                f"list={self.get_create_as_list()})")
