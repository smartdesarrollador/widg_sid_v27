"""
Widget de tags de items para el Creador Masivo

Componentes:
- Tags seleccionables tipo chips/pills
- Botón + para crear nuevos tags
- Siempre visible (a diferencia de ProjectElementTagsSection)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QCompleter
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
from src.views.widgets.project_element_tags_section import TagChip, FlowLayout
import logging

logger = logging.getLogger(__name__)


class ItemTagsSection(QWidget):
    """
    Sección de tags generales de items

    Permite seleccionar tags existentes y crear nuevos.
    Siempre visible, a diferencia de ProjectElementTagsSection.

    Señales:
        tags_changed: Emitida cuando cambian los tags seleccionados (list[str])
        create_tag_clicked: Emitida cuando se hace clic en crear tag
    """

    # Señales
    tags_changed = pyqtSignal(list)  # list[str]
    create_tag_clicked = pyqtSignal()

    def __init__(self, parent=None):
        """Inicializa la sección de tags de items"""
        super().__init__(parent)
        self.tag_chips: list[TagChip] = []
        self.all_available_tags: list[str] = []  # Para autocompletado
        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

    def _setup_ui(self):
        """Configura la interfaz del widget"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Título con botón crear
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        title = QLabel("🏷️ Tags de Items")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)

        # Info label
        info_label = QLabel("(Aplica a todos los items)")
        info_label.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
        header_layout.addWidget(info_label)

        header_layout.addStretch()

        self.create_btn = QPushButton("+")
        self.create_btn.setFixedSize(30, 30)
        self.create_btn.setToolTip("Crear nuevo tag")
        header_layout.addWidget(self.create_btn)

        layout.addLayout(header_layout)

        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #444;")
        layout.addWidget(separator)

        # Campo de búsqueda/agregar tag
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar o agregar tag...")
        self.search_input.setMinimumHeight(35)
        search_layout.addWidget(self.search_input)

        self.add_btn = QPushButton("Agregar")
        self.add_btn.setFixedHeight(35)
        self.add_btn.setToolTip("Agregar tag desde búsqueda")
        search_layout.addWidget(self.add_btn)

        layout.addLayout(search_layout)

        # Contenedor scrollable para tags
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setMaximumHeight(150)
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

        # Widget contenedor de tags
        self.tags_container = QWidget()
        self.tags_layout = FlowLayout()
        self.tags_container.setLayout(self.tags_layout)

        scroll_area.setWidget(self.tags_container)
        layout.addWidget(scroll_area)

        # Label de ayuda cuando no hay tags
        self.empty_label = QLabel("No hay tags disponibles. Usa el campo de búsqueda o haz clic en + para crear.")
        self.empty_label.setStyleSheet("color: #888; font-style: italic;")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty_label)

        # Autocompletador (se configurará al cargar tags)
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.search_input.setCompleter(self.completer)

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
            QPushButton#create_btn {
                font-size: 16px;
                padding: 0;
            }
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
            }
        """)

    def _connect_signals(self):
        """Conecta señales internas"""
        self.create_btn.clicked.connect(self.create_tag_clicked.emit)
        self.add_btn.clicked.connect(self._on_add_tag_from_search)
        self.search_input.returnPressed.connect(self._on_add_tag_from_search)
        self.search_input.textChanged.connect(self._on_search_changed)

    def _on_search_changed(self, text: str):
        """Callback cuando cambia el texto de búsqueda"""
        # Filtrar tags visibles según búsqueda
        search_text = text.lower().strip()

        if not search_text:
            # Mostrar todos los tags
            for chip in self.tag_chips:
                chip.setVisible(True)
        else:
            # Filtrar tags que coincidan
            for chip in self.tag_chips:
                matches = search_text in chip.get_tag_name().lower()
                chip.setVisible(matches)

    def _on_add_tag_from_search(self):
        """Callback para agregar tag desde campo de búsqueda"""
        tag_name = self.search_input.text().strip()

        if not tag_name:
            logger.warning("No se puede agregar tag vacío")
            return

        # Verificar si ya existe
        existing_names = [chip.get_tag_name().lower() for chip in self.tag_chips]
        if tag_name.lower() in existing_names:
            logger.info(f"Tag '{tag_name}' ya existe, seleccionándolo")
            # Seleccionar el tag existente
            for chip in self.tag_chips:
                if chip.get_tag_name().lower() == tag_name.lower():
                    chip.set_selected(True)
                    break
            self.search_input.clear()
            self._on_tag_toggled(True)
            return

        # Agregar nuevo tag
        self.add_tag(tag_name, select=True)
        self.search_input.clear()

        logger.info(f"Tag '{tag_name}' agregado desde búsqueda")

    def load_tags(self, tags: list[str]):
        """
        Carga los tags disponibles

        Args:
            tags: Lista de nombres de tags
        """
        # Limpiar chips existentes
        self._clear_chips()

        # Guardar para autocompletado
        self.all_available_tags = tags.copy()
        self.completer.setModel(None)  # Resetear modelo
        from PyQt6.QtCore import QStringListModel
        self.completer.setModel(QStringListModel(tags))

        if not tags:
            self.empty_label.setVisible(True)
            self.tags_container.setVisible(False)
            return

        self.empty_label.setVisible(False)
        self.tags_container.setVisible(True)

        # Crear chips
        for tag_name in tags:
            chip = TagChip(tag_name)
            chip.toggled.connect(self._on_tag_toggled)
            self.tag_chips.append(chip)
            self.tags_layout.addWidget(chip)

        logger.info(f"Cargados {len(tags)} tags de items")

    def _clear_chips(self):
        """Limpia todos los chips de tags"""
        for chip in self.tag_chips:
            self.tags_layout.removeWidget(chip)
            chip.deleteLater()

        self.tag_chips.clear()

    def _on_tag_toggled(self, is_selected: bool):
        """Callback cuando se selecciona/deselecciona un tag"""
        selected_tags = self.get_selected_tags()
        self.tags_changed.emit(selected_tags)
        logger.debug(f"Tags de items seleccionados: {selected_tags}")

    def get_selected_tags(self) -> list[str]:
        """
        Obtiene los tags seleccionados

        Returns:
            Lista de nombres de tags seleccionados
        """
        return [chip.get_tag_name() for chip in self.tag_chips if chip.is_selected]

    def set_selected_tags(self, tag_names: list[str]):
        """
        Establece los tags seleccionados

        Args:
            tag_names: Lista de nombres de tags a seleccionar
        """
        for chip in self.tag_chips:
            should_select = chip.get_tag_name() in tag_names
            chip.set_selected(should_select)

    def clear_selection(self):
        """Limpia la selección de todos los tags"""
        for chip in self.tag_chips:
            chip.set_selected(False)

    def add_tag(self, tag_name: str, select: bool = True):
        """
        Agrega un nuevo tag a la lista

        Args:
            tag_name: Nombre del tag
            select: Si seleccionarlo automáticamente
        """
        # Verificar que no exista ya
        existing_names = [chip.get_tag_name() for chip in self.tag_chips]
        if tag_name in existing_names:
            logger.warning(f"Tag '{tag_name}' ya existe")
            return

        # Mostrar contenedor si estaba vacío
        if not self.tag_chips:
            self.empty_label.setVisible(False)
            self.tags_container.setVisible(True)

        # Crear chip
        chip = TagChip(tag_name, is_selected=select)
        chip.toggled.connect(self._on_tag_toggled)
        self.tag_chips.append(chip)
        self.tags_layout.addWidget(chip)

        # Agregar a lista de autocompletado
        if tag_name not in self.all_available_tags:
            self.all_available_tags.append(tag_name)
            from PyQt6.QtCore import QStringListModel
            self.completer.setModel(QStringListModel(self.all_available_tags))

        logger.info(f"Tag '{tag_name}' agregado")

        # Emitir cambio si está seleccionado
        if select:
            self._on_tag_toggled(True)

    def remove_tag(self, tag_name: str):
        """
        Elimina un tag de la lista

        Args:
            tag_name: Nombre del tag a eliminar
        """
        for chip in self.tag_chips[:]:
            if chip.get_tag_name() == tag_name:
                self.tag_chips.remove(chip)
                self.tags_layout.removeWidget(chip)
                chip.deleteLater()
                logger.info(f"Tag '{tag_name}' eliminado")

                # Verificar si quedó vacío
                if not self.tag_chips:
                    self.empty_label.setVisible(True)
                    self.tags_container.setVisible(False)

                # Emitir cambio
                self._on_tag_toggled(False)
                break

    def clear_search(self):
        """Limpia el campo de búsqueda"""
        self.search_input.clear()

    def to_list(self) -> list[str]:
        """
        Exporta los tags seleccionados a lista

        Returns:
            Lista de tags seleccionados
        """
        return self.get_selected_tags()

    def from_list(self, tag_names: list[str]):
        """
        Importa tags seleccionados desde lista

        Args:
            tag_names: Lista de nombres de tags a seleccionar
        """
        self.set_selected_tags(tag_names)

    def __repr__(self) -> str:
        """Representación del widget"""
        selected = self.get_selected_tags()
        total = len(self.tag_chips)
        return f"ItemTagsSection(selected={len(selected)}/{total})"
