"""
Migration script for Widget Sidebar
Migrates data from JSON files to SQLite database
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from .db_manager import DBManager


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_json_to_sqlite(
    json_config_path: str = "config.json",
    json_defaults_path: str = "default_categories.json",
    db_path: str = "widget_sidebar.db"
) -> None:
    """
    Migrate data from JSON files to SQLite database

    Args:
        json_config_path: Path to config.json file
        json_defaults_path: Path to default_categories.json file
        db_path: Path to SQLite database file

    Raises:
        FileNotFoundError: If required JSON files don't exist
        json.JSONDecodeError: If JSON files are invalid
        Exception: If migration fails
    """

    print("="*60)
    print("🔄 Iniciando migración de JSON a SQLite...")
    print("="*60)

    # Counters for statistics
    stats = {
        'settings': 0,
        'categories': 0,
        'items': 0,
        'history': 0
    }

    try:
        # Step 1: Create DBManager instance
        print("\n[1/6] Creando base de datos...")
        db = DBManager(db_path)
        print(f"✅ Base de datos inicializada: {db_path}")

        # Step 2: Load and migrate config.json
        config_path = Path(json_config_path)
        config_data = {}

        if config_path.exists():
            print(f"\n[2/6] Leyendo {json_config_path}...")
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            print(f"✅ Archivo cargado: {json_config_path}")
        else:
            print(f"\n[2/6] ⚠️  {json_config_path} no encontrado, usando valores por defecto")
            config_data = {'settings': {}, 'categories': [], 'history': []}

        # Step 3: Migrate settings
        print("\n[3/6] Migrando configuraciones...")
        settings = config_data.get('settings', {})

        # Flatten nested settings (like window_position)
        flat_settings = {}
        for key, value in settings.items():
            if isinstance(value, dict):
                # For nested objects, store as JSON
                flat_settings[key] = value
            else:
                flat_settings[key] = value

        for key, value in flat_settings.items():
            db.set_setting(key, value)
            stats['settings'] += 1

        print(f"✅ Configuraciones migradas: {stats['settings']} settings")

        # Step 4: Load and migrate default_categories.json
        defaults_path = Path(json_defaults_path)

        if defaults_path.exists():
            print(f"\n[4/6] Leyendo {json_defaults_path}...")
            with open(defaults_path, 'r', encoding='utf-8') as f:
                defaults_data = json.load(f)
            print(f"✅ Archivo cargado: {json_defaults_path}")

            # Migrate predefined categories
            print("   Migrando categorías predefinidas...")
            predefined_categories = defaults_data.get('categories', [])

            for cat_data in predefined_categories:
                # Add category
                cat_id = db.add_category(
                    name=cat_data['name'],
                    icon=cat_data.get('icon'),
                    is_predefined=True
                )
                stats['categories'] += 1

                # Add items for this category
                items = cat_data.get('items', [])
                for item_data in items:
                    # Determine item type
                    content = item_data['content']
                    item_type = _determine_item_type(content)

                    db.add_item(
                        category_id=cat_id,
                        label=item_data['label'],
                        content=content,
                        item_type=item_type,
                        icon=item_data.get('icon'),
                        is_sensitive=item_data.get('is_sensitive', False),
                        tags=item_data.get('tags', [])
                    )
                    stats['items'] += 1

                print(f"   ✓ {cat_data['name']}: {len(items)} items")

            print(f"✅ Categorías predefinidas: {len(predefined_categories)} categorías, {stats['items']} items")
        else:
            print(f"\n[4/6] ⚠️  {json_defaults_path} no encontrado")

        # Step 5: Migrate custom categories from config.json
        print("\n[5/6] Migrando categorías personalizadas...")
        custom_categories = config_data.get('categories', [])
        custom_items_count = 0

        if custom_categories:
            for cat_data in custom_categories:
                # Add custom category
                cat_id = db.add_category(
                    name=cat_data['name'],
                    icon=cat_data.get('icon'),
                    is_predefined=False
                )
                stats['categories'] += 1

                # Add items
                items = cat_data.get('items', [])
                for item_data in items:
                    content = item_data['content']
                    item_type = _determine_item_type(content)

                    db.add_item(
                        category_id=cat_id,
                        label=item_data['label'],
                        content=content,
                        item_type=item_type,
                        icon=item_data.get('icon'),
                        is_sensitive=item_data.get('is_sensitive', False),
                        tags=item_data.get('tags', [])
                    )
                    custom_items_count += 1

                print(f"   ✓ {cat_data['name']}: {len(items)} items")

            print(f"✅ Categorías personalizadas: {len(custom_categories)} categorías, {custom_items_count} items")
        else:
            print("✅ Sin categorías personalizadas")

        # Step 6: Migrate clipboard history
        print("\n[6/6] Migrando historial de portapapeles...")
        history = config_data.get('history', [])

        if history:
            for hist_entry in history:
                # History entries from JSON might not have item_id
                content = hist_entry.get('content', '') if isinstance(hist_entry, dict) else str(hist_entry)
                db.add_to_history(item_id=None, content=content)
                stats['history'] += 1

            print(f"✅ Historial migrado: {stats['history']} entradas")
        else:
            print("✅ Sin historial previo")

        # Close database connection
        db.close()

        # Print final statistics
        print("\n" + "="*60)
        print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE!")
        print("="*60)
        print(f"\n📊 Estadísticas:")
        print(f"   • Settings:   {stats['settings']} configuraciones")
        print(f"   • Categorías: {stats['categories']} categorías")
        print(f"   • Items:      {stats['items'] + custom_items_count} items totales")
        print(f"   • Historial:  {stats['history']} entradas")
        print(f"\n📁 Base de datos creada en: {Path(db_path).absolute()}")
        print("="*60)

    except FileNotFoundError as e:
        logger.error(f"Archivo no encontrado: {e}")
        print(f"\n❌ Error: Archivo no encontrado - {e}")
        raise

    except json.JSONDecodeError as e:
        logger.error(f"Error al parsear JSON: {e}")
        print(f"\n❌ Error: JSON inválido - {e}")
        raise

    except Exception as e:
        logger.error(f"Error durante la migración: {e}")
        print(f"\n❌ Error durante la migración: {e}")
        import traceback
        traceback.print_exc()
        raise


def _determine_item_type(content: str) -> str:
    """
    Determine item type based on content

    Args:
        content: Item content string

    Returns:
        str: Item type (TEXT, URL, CODE, PATH)
    """
    content_lower = content.lower().strip()

    # Check if it's a URL
    if content_lower.startswith(('http://', 'https://', 'www.')):
        return 'URL'

    # Check if it's a file path
    if '\\' in content or content.startswith('/') or content.startswith('./'):
        return 'PATH'

    # Check if it's code (contains common code patterns)
    code_indicators = [
        'git ', 'docker ', 'npm ', 'pip ', 'python ',
        'cd ', 'mkdir ', 'chmod ', 'chown ',
        '#!/', 'def ', 'class ', 'import ', 'from ',
        'function', 'const ', 'let ', 'var ',
        '<?php', '<?=', 'SELECT', 'INSERT', 'UPDATE'
    ]

    for indicator in code_indicators:
        if indicator in content_lower or content_lower.startswith(indicator):
            return 'CODE'

    # Default to TEXT
    return 'TEXT'


def backup_json_files(
    config_path: str = "config.json",
    defaults_path: str = "default_categories.json",
    backup_suffix: str = ".backup"
) -> None:
    """
    Create backup copies of JSON files before migration

    Args:
        config_path: Path to config.json
        defaults_path: Path to default_categories.json
        backup_suffix: Suffix to add to backup files
    """
    import shutil

    print("🔄 Creando backup de archivos JSON...")

    config = Path(config_path)
    if config.exists():
        backup_path = config.with_suffix(config.suffix + backup_suffix)
        shutil.copy2(config, backup_path)
        print(f"✅ Backup creado: {backup_path}")

    defaults = Path(defaults_path)
    if defaults.exists():
        backup_path = defaults.with_suffix(defaults.suffix + backup_suffix)
        shutil.copy2(defaults, backup_path)
        print(f"✅ Backup creado: {backup_path}")


def migrate_pinned_panels_for_global_search(db: DBManager) -> None:
    """
    Add missing columns to pinned_panels table for global search support

    Adds:
    - panel_type: 'category' or 'global_search'
    - search_query: Search text for global_search panels
    - advanced_filters: JSON serialized advanced filters
    - state_filter: 'normal', 'archived', 'inactive', 'all'
    - filter_config: General filter configuration JSON
    - keyboard_shortcut: Keyboard shortcut like 'Ctrl+Shift+1'

    Args:
        db: DBManager instance
    """
    try:
        print("\n🔄 Verificando esquema de pinned_panels...")

        # Check which columns exist
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(pinned_panels)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        # Define columns to add
        columns_to_add = {
            'panel_type': "TEXT DEFAULT 'category'",
            'search_query': "TEXT DEFAULT NULL",
            'advanced_filters': "TEXT DEFAULT NULL",
            'state_filter': "TEXT DEFAULT 'normal'",
            'filter_config': "TEXT DEFAULT NULL",
            'keyboard_shortcut': "TEXT DEFAULT NULL"
        }

        added_count = 0

        # Add missing columns
        for column_name, column_def in columns_to_add.items():
            if column_name not in existing_columns:
                alter_query = f"ALTER TABLE pinned_panels ADD COLUMN {column_name} {column_def}"
                cursor.execute(alter_query)
                conn.commit()
                print(f"   ✓ Columna agregada: {column_name}")
                added_count += 1
            else:
                print(f"   ⚠ Columna ya existe: {column_name}")

        if added_count > 0:
            print(f"✅ Migración completada: {added_count} columnas agregadas")
        else:
            print("✅ Esquema ya actualizado, no se requieren cambios")

    except Exception as e:
        logger.error(f"Error en migración de pinned_panels: {e}")
        print(f"❌ Error: {e}")
        raise


def migration_003_create_tags_tables(db: DBManager) -> None:
    """
    Migración 003: Crear tablas tags e item_tags para relación many-to-many

    Esta migración:
    1. Crea tabla 'tags' con nombres únicos (UNIQUE constraint)
    2. Crea tabla pivot 'item_tags' para relación many-to-many
    3. Crea índices para optimización de búsquedas

    Args:
        db: DBManager instance
    """
    try:
        print("\n" + "=" * 80)
        print("🔄 MIGRACIÓN 003: Creación de Tablas tags e item_tags")
        print("=" * 80)

        conn = db.conn
        cursor = conn.cursor()

        # Verificar si las tablas ya existen
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tags'")
        tags_exists = cursor.fetchone() is not None

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='item_tags'")
        item_tags_exists = cursor.fetchone() is not None

        if tags_exists and item_tags_exists:
            print("⚠️  Las tablas 'tags' e 'item_tags' ya existen.")
            print("   Saltando creación de tablas...")
            return

        # Paso 1: Crear tabla tags
        print("\n[1/3] Creando tabla 'tags'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usage_count INTEGER DEFAULT 0,
                last_used TIMESTAMP,
                color TEXT,
                description TEXT
            )
        """)
        conn.commit()
        print("   ✓ Tabla 'tags' creada")

        # Paso 2: Crear índices para tabla tags
        print("   Creando índices para 'tags'...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_usage_count ON tags(usage_count DESC)")
        conn.commit()
        print("   ✓ Índices creados: idx_tags_name, idx_tags_usage_count")

        # Paso 3: Crear tabla pivot item_tags
        print("\n[2/3] Creando tabla pivot 'item_tags'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS item_tags (
                item_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (item_id, tag_id),
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
        print("   ✓ Tabla 'item_tags' creada")

        # Paso 4: Crear índices para tabla item_tags
        print("   Creando índices para 'item_tags'...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_tags_item_id ON item_tags(item_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_tags_tag_id ON item_tags(tag_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_tags_composite ON item_tags(tag_id, item_id)")
        conn.commit()
        print("   ✓ Índices creados: idx_item_tags_item_id, idx_item_tags_tag_id, idx_item_tags_composite")

        # Paso 5: Verificar creación
        print("\n[3/3] Verificando tablas creadas...")

        # Verificar tabla tags
        cursor.execute("PRAGMA table_info(tags)")
        tags_columns = cursor.fetchall()
        print(f"   ✓ Tabla 'tags': {len(tags_columns)} columnas")

        # Verificar tabla item_tags
        cursor.execute("PRAGMA table_info(item_tags)")
        item_tags_columns = cursor.fetchall()
        print(f"   ✓ Tabla 'item_tags': {len(item_tags_columns)} columnas")

        # Verificar índices
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='tags'")
        tags_indices = cursor.fetchall()
        print(f"   ✓ Índices en 'tags': {len(tags_indices)}")

        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='item_tags'")
        item_tags_indices = cursor.fetchall()
        print(f"   ✓ Índices en 'item_tags': {len(item_tags_indices)}")

        print("\n" + "=" * 80)
        print("✅ MIGRACIÓN 003 COMPLETADA EXITOSAMENTE")
        print("=" * 80)
        print("\nTablas creadas:")
        print("  • tags (id, name UNIQUE, created_at, updated_at, usage_count, last_used, color, description)")
        print("  • item_tags (item_id, tag_id, created_at) - PRIMARY KEY (item_id, tag_id)")
        print("\nÍndices creados:")
        print("  • idx_tags_name - Búsqueda rápida por nombre")
        print("  • idx_tags_usage_count - Ordenamiento por uso")
        print("  • idx_item_tags_item_id - Búsqueda por item")
        print("  • idx_item_tags_tag_id - Búsqueda por tag")
        print("  • idx_item_tags_composite - Búsqueda compuesta")
        print("\n✅ Siguiente paso: Ejecutar script de migración de datos")
        print("   Comando: python util/migrate_tags_to_relational.py")

    except Exception as e:
        logger.error(f"❌ Error en migración 003: {e}")
        print(f"\n❌ Error durante migración 003: {e}")
        import traceback
        traceback.print_exc()
        raise


def migration_004_create_project_element_tags(db: DBManager) -> None:
    """
    Migración 004: Crear tablas project_element_tags y project_element_tag_associations

    Esta migración:
    1. Crea tabla 'project_element_tags' para tags específicos de elementos de proyecto
    2. Crea tabla pivot 'project_element_tag_associations' para relación many-to-many
    3. Crea índices para optimización de búsquedas

    Args:
        db: DBManager instance
    """
    try:
        print("\n" + "=" * 80)
        print("🔄 MIGRACIÓN 004: Creación de Tablas de Tags para Elementos de Proyecto")
        print("=" * 80)

        conn = db.connect()
        cursor = conn.cursor()

        # Verificar si las tablas ya existen
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='project_element_tags'
        """)
        tags_exists = cursor.fetchone() is not None

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='project_element_tag_associations'
        """)
        associations_exists = cursor.fetchone() is not None

        if tags_exists and associations_exists:
            print("⚠️  Las tablas ya existen.")
            print("   Saltando creación de tablas...")
            return

        # Paso 1: Crear tabla project_element_tags
        print("\n[1/3] Creando tabla 'project_element_tags'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_element_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                color TEXT DEFAULT '#3498db',
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("   ✓ Tabla 'project_element_tags' creada")

        # Paso 2: Crear índices para tabla project_element_tags
        print("   Creando índices para 'project_element_tags'...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_project_element_tags_name
            ON project_element_tags(name)
        """)
        conn.commit()
        print("   ✓ Índice creado: idx_project_element_tags_name")

        # Paso 3: Crear tabla pivot project_element_tag_associations
        print("\n[2/3] Creando tabla pivot 'project_element_tag_associations'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_element_tag_associations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_relation_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_relation_id) REFERENCES project_relations(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES project_element_tags(id) ON DELETE CASCADE,
                UNIQUE(project_relation_id, tag_id)
            )
        """)
        conn.commit()
        print("   ✓ Tabla 'project_element_tag_associations' creada")

        # Paso 4: Crear índices para tabla project_element_tag_associations
        print("   Creando índices para 'project_element_tag_associations'...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_project_element_tag_assoc_relation
            ON project_element_tag_associations(project_relation_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_project_element_tag_assoc_tag
            ON project_element_tag_associations(tag_id)
        """)
        conn.commit()
        print("   ✓ Índices creados: idx_project_element_tag_assoc_relation, idx_project_element_tag_assoc_tag")

        # Paso 5: Verificar creación
        print("\n[3/3] Verificando tablas creadas...")

        # Verificar tabla project_element_tags
        cursor.execute("PRAGMA table_info(project_element_tags)")
        tags_columns = cursor.fetchall()
        print(f"   ✓ Tabla 'project_element_tags': {len(tags_columns)} columnas")

        # Verificar tabla project_element_tag_associations
        cursor.execute("PRAGMA table_info(project_element_tag_associations)")
        associations_columns = cursor.fetchall()
        print(f"   ✓ Tabla 'project_element_tag_associations': {len(associations_columns)} columnas")

        # Verificar índices
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='project_element_tags'
        """)
        tags_indices = cursor.fetchall()
        print(f"   ✓ Índices en 'project_element_tags': {len(tags_indices)}")

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='project_element_tag_associations'
        """)
        associations_indices = cursor.fetchall()
        print(f"   ✓ Índices en 'project_element_tag_associations': {len(associations_indices)}")

        print("\n" + "=" * 80)
        print("✅ MIGRACIÓN 004 COMPLETADA EXITOSAMENTE")
        print("=" * 80)
        print("\nTablas creadas:")
        print("  • project_element_tags (id, name UNIQUE, color, description, created_at, updated_at)")
        print("  • project_element_tag_associations (id, project_relation_id, tag_id, created_at)")
        print("    - UNIQUE constraint en (project_relation_id, tag_id)")
        print("\nÍndices creados:")
        print("  • idx_project_element_tags_name - Búsqueda rápida por nombre")
        print("  • idx_project_element_tag_assoc_relation - Búsqueda por relación de proyecto")
        print("  • idx_project_element_tag_assoc_tag - Búsqueda por tag")
        print("\n✅ Sistema de tags para elementos de proyecto listo para usar")

    except Exception as e:
        logger.error(f"❌ Error en migración 004: {e}")
        print(f"\n❌ Error durante migración 004: {e}")
        import traceback
        traceback.print_exc()
        raise


def migration_005_add_item_drafts_table(db: DBManager) -> None:
    """
    Migración 005: Crear tabla item_drafts para persistencia de borradores
    del Creador Masivo de Items

    Esta migración:
    1. Crea tabla 'item_drafts' con campos para persistir borradores
    2. Crea índices para optimización de búsquedas
    3. Soporte para JSON en campos de items y tags

    Args:
        db: DBManager instance
    """
    try:
        print("\n" + "=" * 80)
        print("🔄 MIGRACIÓN 005: Creación de Tabla item_drafts")
        print("=" * 80)

        conn = db.connect()
        cursor = conn.cursor()

        # Verificar si la tabla ya existe
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='item_drafts'
        """)
        table_exists = cursor.fetchone() is not None

        if table_exists:
            print("⚠️  La tabla 'item_drafts' ya existe.")
            print("   Saltando creación de tabla...")
            return

        # Paso 1: Crear tabla item_drafts
        print("\n[1/3] Creando tabla 'item_drafts'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS item_drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tab_id TEXT NOT NULL UNIQUE,
                tab_name TEXT DEFAULT 'Sin título',
                project_id INTEGER DEFAULT NULL,
                area_id INTEGER DEFAULT NULL,
                category_id INTEGER DEFAULT NULL,
                create_as_list BOOLEAN DEFAULT 0,
                list_name TEXT DEFAULT NULL,
                item_tags_json TEXT DEFAULT NULL,
                project_element_tags_json TEXT DEFAULT NULL,
                items_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
            )
        """)
        conn.commit()
        print("   ✓ Tabla 'item_drafts' creada")

        # Paso 2: Crear índices
        print("\n[2/3] Creando índices para 'item_drafts'...")

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_drafts_tab_id
            ON item_drafts(tab_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_drafts_updated
            ON item_drafts(updated_at DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_drafts_category
            ON item_drafts(category_id)
        """)

        conn.commit()
        print("   ✓ Índices creados: idx_drafts_tab_id, idx_drafts_updated, idx_drafts_category")

        # Paso 3: Verificar creación
        print("\n[3/3] Verificando tabla creada...")

        cursor.execute("PRAGMA table_info(item_drafts)")
        columns = cursor.fetchall()
        print(f"   ✓ Tabla 'item_drafts': {len(columns)} columnas")

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='item_drafts'
        """)
        indices = cursor.fetchall()
        print(f"   ✓ Índices en 'item_drafts': {len(indices)}")

        print("\n" + "=" * 80)
        print("✅ MIGRACIÓN 005 COMPLETADA EXITOSAMENTE")
        print("=" * 80)
        print("\nTabla creada:")
        print("  • item_drafts")
        print("    - tab_id (UNIQUE) - UUID de la pestaña")
        print("    - tab_name - Nombre de la pestaña")
        print("    - project_id, area_id, category_id - FKs opcionales")
        print("    - create_as_list, list_name - Configuración de lista")
        print("    - item_tags_json - Tags de items (JSON array)")
        print("    - project_element_tags_json - Tags de proyecto/área (JSON array)")
        print("    - items_json - Items del borrador (JSON array)")
        print("    - created_at, updated_at - Timestamps")
        print("\nÍndices creados:")
        print("  • idx_drafts_tab_id - Búsqueda rápida por tab_id")
        print("  • idx_drafts_updated - Ordenamiento por fecha de actualización")
        print("  • idx_drafts_category - Búsqueda por categoría")
        print("\n✅ Sistema de persistencia de borradores listo para usar")

    except Exception as e:
        logger.error(f"❌ Error en migración 005: {e}")
        print(f"\n❌ Error durante migración 005: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    """
    Run migration when script is executed directly
    """
    import sys

    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print("Uso: python -m src.database.migrations [opciones]")
            print("\nOpciones:")
            print("  -h, --help     Mostrar esta ayuda")
            print("  --backup       Crear backup antes de migrar")
            print("\nEjemplo:")
            print("  python -m src.database.migrations")
            print("  python -m src.database.migrations --backup")
            sys.exit(0)

        if sys.argv[1] == '--backup':
            backup_json_files()

    # Run migration
    try:
        migrate_json_to_sqlite()
    except Exception as e:
        print(f"\n❌ La migración falló: {e}")
        sys.exit(1)
