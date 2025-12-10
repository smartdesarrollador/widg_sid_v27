"""
Widget de tags de elementos de proyecto para el Creador Masivo

Componentes:
- Se muestra solo cuando hay proyecto o área seleccionada
- Muestra tags asociados al proyecto/área
- Botón + para crear nuevos tags
- Tags seleccionables tipo chips/pills
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
import logging

logger = logging.getLogger(__name__)


class TagChip(QWidget):
    """
    Widget de chip/pill para un tag individual

    Señales:
        toggled: Emitida cuando se selecciona/deselecciona (bool)
    """

    toggled = pyqtSignal(bool)

    def __init__(self, tag_name: str, is_selected: bool = False, parent=None):
        """
        Inicializa el chip de tag

        Args:
            tag_name: Nombre del tag
            is_selected: Si está seleccionado inicialmente
            parent: Widget padre
        """
        super().__init__(parent)
        self.tag_name = tag_name
        self.is_selected = is_selected
        self._setup_ui()
        self._update_style()

    def _setup_ui(self):
        """Configura la interfaz del chip"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(0)

        # Etiqueta del tag
        self.label = QLabel(self.tag_name)
        self.label.setFont(QFont("Segoe UI", 11))
        layout.addWidget(self.label)

        # Hacer clickeable
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _update_style(self):
        """Actualiza el estilo según el estado de selección"""
        if self.is_selected:
            self.setStyleSheet("""
                TagChip {
                    background-color: #2196F3;
                    border: 1px solid #1976D2;
                    border-radius: 12px;
                }
                QLabel {
                    color: #ffffff;
                }
            """)
        else:
            self.setStyleSheet("""
                TagChip {
                    background-color: #3d3d3d;
                    border: 1px solid #555;
                    border-radius: 12px;
                }
                QLabel {
                    color: #aaaaaa;
                }
            """)

    def mousePressEvent(self, event):
        """Maneja el clic en el chip"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()

    def toggle(self):
        """Alterna el estado de selección"""
        self.is_selected = not self.is_selected
        self._update_style()
        self.toggled.emit(self.is_selected)
        logger.debug(f"Tag '{self.tag_name}' {'seleccionado' if self.is_selected else 'deseleccionado'}")

    def set_selected(self, selected: bool):
        """
        Establece el estado de selección

        Args:
            selected: True para seleccionar
        """
        if self.is_selected != selected:
            self.is_selected = selected
            self._update_style()

    def get_tag_name(self) -> str:
        """Obtiene el nombre del tag"""
        return self.tag_name


class FlowLayout(QHBoxLayout):
    """
    Layout que acomoda widgets en flujo horizontal con wrap

    Nota: Implementación simplificada para tags
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSpacing(8)
        self.setContentsMargins(0, 0, 0, 0)


class ProjectElementTagsSection(QWidget):
    """
    Sección de tags de elementos de proyecto

    Solo se muestra cuando hay un proyecto o área seleccionada.
    Permite seleccionar tags existentes y crear nuevos.

    Señales:
        tags_changed: Emitida cuando cambian los tags seleccionados (list[str])
        create_tag_clicked: Emitida cuando se hace clic en crear tag
    """

    # Señales
    tags_changed = pyqtSignal(list)  # list[str]
    create_tag_clicked = pyqtSignal()

    def __init__(self, parent=None):
        """Inicializa la sección de tags de proyecto"""
        super().__init__(parent)
        self.tag_chips: list[TagChip] = []
        self._setup_ui()
        self._apply_styles()
        self._connect_signals()
        self.setVisible(False)  # Oculto por defecto

    def _setup_ui(self):
        """Configura la interfaz del widget"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Título con botón crear
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        title = QLabel("🏷️ Tags de Proyecto/Área")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        self.create_btn = QPushButton("+")
        self.create_btn.setFixedSize(30, 30)
        self.create_btn.setToolTip("Crear nuevo tag para este proyecto/área")
        header_layout.addWidget(self.create_btn)

        layout.addLayout(header_layout)

        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #444;")
        layout.addWidget(separator)

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
        self.empty_label = QLabel("No hay tags disponibles. Haz clic en + para crear.")
        self.empty_label.setStyleSheet("color: #888; font-style: italic;")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty_label)

    def _apply_styles(self):
        """Aplica estilos CSS al widget"""
        self.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 16px;
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
        self.create_btn.clicked.connect(self.create_tag_clicked.emit)

    def load_tags(self, tags: list[str]):
        """
        Carga los tags disponibles para el proyecto/área

        Args:
            tags: Lista de nombres de tags
        """
        # Limpiar chips existentes
        self._clear_chips()

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

        logger.info(f"Cargados {len(tags)} tags de proyecto/área")

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
        logger.debug(f"Tags seleccionados: {selected_tags}")

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

    def show_for_project_or_area(self, has_selection: bool):
        """
        Muestra/oculta la sección según si hay proyecto/área seleccionada

        Args:
            has_selection: True si hay proyecto o área seleccionada
        """
        self.setVisible(has_selection)

        if not has_selection:
            self._clear_chips()

        logger.debug(f"ProjectElementTagsSection {'visible' if has_selection else 'oculta'}")

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

        logger.info(f"Tag '{tag_name}' agregado")

        # Emitir cambio si está seleccionado
        if select:
            self._on_tag_toggled(True)

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
        return f"ProjectElementTagsSection(selected={selected})"
