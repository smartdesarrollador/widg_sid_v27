"""
Servicio de validación para items del Creador Masivo

Proporciona validaciones específicas por tipo de item y
detección automática de tipo basado en contenido.
"""

import re
from pathlib import Path
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class ItemValidationService:
    """
    Servicio de validación para items

    Proporciona métodos para validar contenido según el tipo
    y detectar automáticamente el tipo basado en el contenido.
    """

    # Patrones de validación
    URL_PATTERN = re.compile(
        r'^https?://'  # http:// o https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # dominio
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # o IP
        r'(?::\d+)?'  # puerto opcional
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )

    # Indicadores de código
    CODE_KEYWORDS = [
        'git ', 'docker ', 'npm ', 'pip ', 'python ', 'node ',
        'cd ', 'mkdir ', 'chmod ', 'chown ', 'ls ', 'cat ',
        '#!/', 'def ', 'class ', 'import ', 'from ', 'export ',
        'function', 'const ', 'let ', 'var ', 'async ', 'await ',
        '<?php', '<?=', 'SELECT', 'INSERT', 'UPDATE', 'DELETE',
        'CREATE', 'DROP', 'ALTER', 'use ', 'require', 'include'
    ]

    @staticmethod
    def validate_url(content: str) -> Tuple[bool, str]:
        """
        Valida que el contenido sea una URL válida

        Args:
            content: Contenido a validar

        Returns:
            Tupla (is_valid, error_message)
        """
        content = content.strip()

        if not content:
            return False, "La URL no puede estar vacía"

        # Verificar protocolo
        if not content.startswith(('http://', 'https://')):
            return False, "La URL debe comenzar con http:// o https://"

        # Validar formato
        if ItemValidationService.URL_PATTERN.match(content):
            return True, ""

        return False, "Formato de URL inválido"

    @staticmethod
    def validate_path(content: str) -> Tuple[bool, str]:
        """
        Valida que el contenido sea un path válido

        Args:
            content: Contenido a validar

        Returns:
            Tupla (is_valid, error_message)
        """
        content = content.strip()

        if not content:
            return False, "El path no puede estar vacío"

        try:
            # Intentar crear Path object
            path = Path(content)

            # Verificar que tenga algún componente
            if not str(path):
                return False, "El path no puede estar vacío"

            # Path válido (puede o no existir físicamente)
            return True, ""

        except Exception as e:
            return False, f"Path inválido: {str(e)}"

    @staticmethod
    def validate_code(content: str) -> Tuple[bool, str]:
        """
        Valida que el contenido sea código válido

        Args:
            content: Contenido a validar

        Returns:
            Tupla (is_valid, error_message)
        """
        content = content.strip()

        if not content:
            return False, "El código no puede estar vacío"

        # Para CODE no hay validación estricta
        # Solo verificar que tenga contenido
        return True, ""

    @staticmethod
    def validate_text(content: str) -> Tuple[bool, str]:
        """
        Valida texto genérico

        Args:
            content: Contenido a validar

        Returns:
            Tupla (is_valid, error_message)
        """
        content = content.strip()

        if not content:
            return False, "El texto no puede estar vacío"

        return True, ""

    @classmethod
    def validate_item(cls, content: str, item_type: str) -> Tuple[bool, str]:
        """
        Valida un item según su tipo

        Args:
            content: Contenido del item
            item_type: Tipo del item (URL, PATH, CODE, TEXT)

        Returns:
            Tupla (is_valid, error_message)
        """
        # Mapeo de tipos a validadores
        validators = {
            'URL': cls.validate_url,
            'PATH': cls.validate_path,
            'CODE': cls.validate_code,
            'TEXT': cls.validate_text
        }

        # Obtener validador (por defecto TEXT)
        validator = validators.get(item_type, cls.validate_text)

        try:
            return validator(content)
        except Exception as e:
            logger.error(f"Error validando item tipo {item_type}: {e}")
            return False, f"Error de validación: {str(e)}"

    @classmethod
    def auto_detect_type(cls, content: str) -> str:
        """
        Detecta automáticamente el tipo de item basado en el contenido

        Orden de detección:
        1. URL (si empieza con http/https)
        2. PATH (si parece una ruta de archivo)
        3. CODE (si contiene palabras clave de código)
        4. TEXT (por defecto)

        Args:
            content: Contenido del item

        Returns:
            Tipo detectado: URL, PATH, CODE o TEXT
        """
        content = content.strip()

        if not content:
            return 'TEXT'

        # 1. Detectar URL
        if content.startswith(('http://', 'https://', 'ftp://', 'www.')):
            return 'URL'

        # 2. Detectar PATH
        # Windows: C:\, D:\, etc.
        if re.match(r'^[A-Z]:\\', content):
            return 'PATH'

        # Unix/Linux: /, ~/, ./
        if content.startswith(('/', '~/', './')):
            return 'PATH'

        # Extensiones de archivo comunes
        if re.search(r'\.(exe|dll|py|js|ts|jsx|tsx|java|cpp|h|cs|go|rs|rb|php|html|css|json|xml|yml|yaml|md|txt|pdf|doc|docx|xls|xlsx|ppt|pptx|zip|rar|tar|gz|7z|png|jpg|jpeg|gif|svg|mp4|mp3|avi|mov)$', content, re.IGNORECASE):
            return 'PATH'

        # 3. Detectar CODE
        content_lower = content.lower()

        # Verificar palabras clave al inicio
        for keyword in cls.CODE_KEYWORDS:
            if content_lower.startswith(keyword):
                return 'CODE'

        # Verificar si contiene sintaxis de código
        code_patterns = [
            r'\s*=\s*',  # Asignaciones
            r'[\{\}\[\]\(\)]',  # Llaves, corchetes, paréntesis
            r';$',  # Punto y coma al final
            r'=>',  # Arrow functions
            r'->',  # Acceso a miembros
            r'::\w+',  # Namespaces
            r'\$\w+',  # Variables PHP/Bash
            r'@\w+',  # Decoradores Python
        ]

        for pattern in code_patterns:
            if re.search(pattern, content):
                return 'CODE'

        # 4. Por defecto TEXT
        return 'TEXT'

    @staticmethod
    def sanitize_content(content: str, item_type: str) -> str:
        """
        Sanitiza el contenido según el tipo

        Args:
            content: Contenido a sanitizar
            item_type: Tipo de item

        Returns:
            Contenido sanitizado
        """
        content = content.strip()

        if item_type == 'URL':
            # Eliminar espacios en URLs
            content = content.replace(' ', '')

        elif item_type == 'PATH':
            # Normalizar separadores de path
            content = content.replace('\\\\', '\\')

        elif item_type == 'CODE':
            # Preservar espacios en código
            pass

        elif item_type == 'TEXT':
            # Normalizar espacios múltiples
            content = ' '.join(content.split())

        return content

    @classmethod
    def validate_and_sanitize(cls, content: str, item_type: str) -> Tuple[bool, str, str]:
        """
        Valida y sanitiza el contenido en una sola operación

        Args:
            content: Contenido del item
            item_type: Tipo del item

        Returns:
            Tupla (is_valid, sanitized_content, error_message)
        """
        # Sanitizar primero
        sanitized = cls.sanitize_content(content, item_type)

        # Luego validar
        is_valid, error_msg = cls.validate_item(sanitized, item_type)

        return is_valid, sanitized, error_msg

    @staticmethod
    def get_type_description(item_type: str) -> str:
        """
        Retorna una descripción del tipo de item

        Args:
            item_type: Tipo de item

        Returns:
            Descripción legible
        """
        descriptions = {
            'URL': 'Enlace web (http:// o https://)',
            'PATH': 'Ruta de archivo o carpeta',
            'CODE': 'Comando o fragmento de código',
            'TEXT': 'Texto genérico'
        }

        return descriptions.get(item_type, 'Tipo desconocido')

    @staticmethod
    def get_type_icon(item_type: str) -> str:
        """
        Retorna un icono emoji para el tipo

        Args:
            item_type: Tipo de item

        Returns:
            Emoji representativo
        """
        icons = {
            'URL': '🌐',
            'PATH': '📁',
            'CODE': '💻',
            'TEXT': '📝'
        }

        return icons.get(item_type, '📄')

    @staticmethod
    def suggest_improvements(content: str, item_type: str) -> list[str]:
        """
        Sugiere mejoras para el contenido basado en el tipo

        Args:
            content: Contenido del item
            item_type: Tipo del item

        Returns:
            Lista de sugerencias
        """
        suggestions = []

        if item_type == 'URL':
            if not content.startswith('https://'):
                suggestions.append("💡 Considera usar HTTPS en lugar de HTTP para mayor seguridad")

            if ' ' in content:
                suggestions.append("⚠️ Las URLs no deben contener espacios")

        elif item_type == 'PATH':
            if '\\\\' in content:
                suggestions.append("💡 Usa separadores simples (\\) en lugar de dobles (\\\\)")

        elif item_type == 'CODE':
            if len(content) > 200:
                suggestions.append("💡 Considera dividir comandos largos en múltiples items")

        return suggestions
