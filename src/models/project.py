"""
Modelos de datos para el sistema de proyectos

Modelos:
- Project: Proyecto principal
- ProjectRelation: Relación entre proyecto y entidad (tag, lista, item, etc)
- ProjectComponent: Componente estructural (divisor, comentario, alerta, nota)
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List


@dataclass
class Project:
    """
    Modelo de proyecto

    Un proyecto agrupa tags, procesos, listas, tablas, categorías e items relacionados
    para facilitar el acceso rápido a todos los elementos de un proyecto específico.
    """
    id: int
    name: str
    description: str = ""
    color: str = "#3498db"
    icon: str = "📁"
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el proyecto a diccionario"""
        data = asdict(self)
        # Convertir datetime a string ISO
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            data['updated_at'] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Crea un proyecto desde un diccionario"""
        # Convertir strings ISO a datetime
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)

    def __str__(self) -> str:
        return f"{self.icon} {self.name}"


@dataclass
class ProjectRelation:
    """
    Modelo de relación proyecto-entidad

    Representa la asociación entre un proyecto y una entidad
    (tag, proceso, lista, tabla, categoría o item).
    """
    id: int
    project_id: int
    entity_type: str  # 'tag', 'process', 'list', 'table', 'category', 'item'
    entity_id: int
    description: str = ""  # Descripción contextual del elemento en el proyecto
    order_index: int = 0
    created_at: Optional[datetime] = None

    # Tipos de entidad válidos
    VALID_ENTITY_TYPES = {'tag', 'process', 'list', 'table', 'category', 'item'}

    def __post_init__(self):
        """Validación post-inicialización"""
        if self.entity_type not in self.VALID_ENTITY_TYPES:
            raise ValueError(
                f"entity_type inválido: '{self.entity_type}'. "
                f"Debe ser uno de: {', '.join(self.VALID_ENTITY_TYPES)}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la relación a diccionario"""
        data = asdict(self)
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectRelation':
        """Crea una relación desde un diccionario"""
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)

    def __str__(self) -> str:
        return f"ProjectRelation({self.entity_type}#{self.entity_id} -> Project#{self.project_id})"


@dataclass
class ProjectComponent:
    """
    Modelo de componente estructural del proyecto

    Componentes que ayudan a organizar visualmente el proyecto:
    - divider: Línea divisoria horizontal
    - comment: Comentario/documentación
    - alert: Alerta importante
    - note: Nota/recordatorio
    """
    id: int
    project_id: int
    component_type: str  # 'divider', 'comment', 'alert', 'note'
    content: str = ""  # Texto del componente (vacío para divisores)
    order_index: int = 0
    created_at: Optional[datetime] = None

    # Tipos de componente válidos
    VALID_COMPONENT_TYPES = {'divider', 'comment', 'alert', 'note'}

    # Íconos por tipo de componente
    COMPONENT_ICONS = {
        'divider': '─',
        'comment': '💬',
        'alert': '⚠️',
        'note': '📌'
    }

    def __post_init__(self):
        """Validación post-inicialización"""
        if self.component_type not in self.VALID_COMPONENT_TYPES:
            raise ValueError(
                f"component_type inválido: '{self.component_type}'. "
                f"Debe ser uno de: {', '.join(self.VALID_COMPONENT_TYPES)}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el componente a diccionario"""
        data = asdict(self)
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectComponent':
        """Crea un componente desde un diccionario"""
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)

    def get_icon(self) -> str:
        """Retorna el ícono del componente"""
        return self.COMPONENT_ICONS.get(self.component_type, '')

    def get_display_text(self) -> str:
        """Retorna el texto a mostrar del componente"""
        if self.component_type == 'divider':
            return '─' * 50  # Línea divisoria
        else:
            icon = self.get_icon()
            return f"{icon} {self.content}"

    def __str__(self) -> str:
        return f"{self.get_icon()} {self.component_type}: {self.content[:30]}..."


# Función auxiliar para validar tipos de entidad
def validate_entity_type(entity_type: str) -> bool:
    """Valida si el tipo de entidad es válido"""
    return entity_type in ProjectRelation.VALID_ENTITY_TYPES


# Función auxiliar para validar tipos de componente
def validate_component_type(component_type: str) -> bool:
    """Valida si el tipo de componente es válido"""
    return component_type in ProjectComponent.VALID_COMPONENT_TYPES


# Funciones auxiliares para obtener metadata de entidades
def get_entity_type_icon(entity_type: str) -> str:
    """Retorna el ícono correspondiente al tipo de entidad"""
    icons = {
        'tag': '🏷️',
        'process': '🔄',
        'list': '📋',
        'table': '📊',
        'category': '📁',
        'item': '📝'
    }
    return icons.get(entity_type, '📄')


def get_entity_type_label(entity_type: str) -> str:
    """Retorna la etiqueta legible del tipo de entidad"""
    labels = {
        'tag': 'Tag',
        'process': 'Proceso',
        'list': 'Lista',
        'table': 'Tabla',
        'category': 'Categoría',
        'item': 'Item'
    }
    return labels.get(entity_type, entity_type.title())
