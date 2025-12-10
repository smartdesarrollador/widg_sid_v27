"""
Manager de persistencia de borradores con auto-guardado

Gestiona el guardado automático de borradores con debounce
para evitar guardados excesivos y optimizar rendimiento.
"""

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from typing import Dict, Optional
from src.models.item_draft import ItemDraft
import logging

logger = logging.getLogger(__name__)


class DraftPersistenceManager(QObject):
    """
    Gestiona el auto-guardado de borradores con debounce

    Características:
    - Auto-guardado con debounce configurable
    - Queue de borradores pendientes
    - Señales de éxito/error
    - Forzado de guardado inmediato
    - Carga de borradores desde BD

    Signals:
        draft_saved: Emitida cuando se guarda un borrador (tab_id)
        save_failed: Emitida cuando falla el guardado (tab_id, error)
        draft_loaded: Emitida cuando se carga un borrador (tab_id)
    """

    # Señales
    draft_saved = pyqtSignal(str)  # tab_id
    save_failed = pyqtSignal(str, str)  # tab_id, error_message
    draft_loaded = pyqtSignal(str)  # tab_id

    def __init__(self, db_manager, debounce_ms: int = 1000, parent=None):
        """
        Inicializa el manager de persistencia

        Args:
            db_manager: Instancia de DBManager
            debounce_ms: Milisegundos de debounce (por defecto 1000ms = 1s)
            parent: Widget padre (opcional)
        """
        super().__init__(parent)
        self.db = db_manager
        self.debounce_ms = debounce_ms

        # Timers por tab_id para debounce
        self.save_timers: Dict[str, QTimer] = {}

        # Borradores pendientes de guardado
        self.pending_drafts: Dict[str, ItemDraft] = {}

        # Estadísticas
        self.stats = {
            'saves': 0,
            'loads': 0,
            'errors': 0
        }

        logger.info(f"DraftPersistenceManager inicializado (debounce={debounce_ms}ms)")

    def schedule_save(self, draft: ItemDraft):
        """
        Programa el guardado de un borrador con debounce

        Si ya hay un guardado programado para este tab_id,
        se cancela y se reprograma, implementando el debounce.

        Args:
            draft: Borrador a guardar
        """
        tab_id = draft.tab_id

        # Actualizar borrador pendiente
        self.pending_drafts[tab_id] = draft

        # Cancelar timer existente si lo hay
        if tab_id in self.save_timers:
            self.save_timers[tab_id].stop()
            logger.debug(f"Timer cancelado para tab {tab_id}")

        # Crear nuevo timer
        timer = QTimer()
        timer.setSingleShot(True)  # Solo se ejecuta una vez
        timer.timeout.connect(lambda: self._save_draft(tab_id))
        timer.start(self.debounce_ms)

        self.save_timers[tab_id] = timer

        logger.debug(f"Guardado programado para tab {tab_id} en {self.debounce_ms}ms")

    def _save_draft(self, tab_id: str):
        """
        Ejecuta el guardado real del borrador en BD

        Args:
            tab_id: ID de la pestaña a guardar
        """
        if tab_id not in self.pending_drafts:
            logger.warning(f"No hay borrador pendiente para tab {tab_id}")
            return

        draft = self.pending_drafts[tab_id]

        try:
            # Guardar en BD
            success = self.db.save_item_draft(tab_id, draft.to_dict())

            if success:
                logger.info(f"✅ Borrador guardado: {tab_id} ({draft.tab_name})")
                self.stats['saves'] += 1
                self.draft_saved.emit(tab_id)

                # Limpiar pendientes
                del self.pending_drafts[tab_id]
                if tab_id in self.save_timers:
                    del self.save_timers[tab_id]
            else:
                raise Exception("DBManager retornó False")

        except Exception as e:
            error_msg = f"Error guardando borrador: {str(e)}"
            logger.error(f"❌ {error_msg} (tab_id={tab_id})")
            self.stats['errors'] += 1
            self.save_failed.emit(tab_id, error_msg)

    def force_save(self, tab_id: str) -> bool:
        """
        Fuerza el guardado inmediato de un borrador específico

        Cancela el timer de debounce y guarda inmediatamente.

        Args:
            tab_id: ID de la pestaña

        Returns:
            True si se guardó exitosamente
        """
        # Cancelar timer si existe
        if tab_id in self.save_timers:
            self.save_timers[tab_id].stop()
            logger.debug(f"Timer forzado para tab {tab_id}")

        # Guardar inmediatamente
        if tab_id in self.pending_drafts:
            self._save_draft(tab_id)
            return tab_id not in self.pending_drafts  # True si se limpió de pendientes
        else:
            logger.warning(f"No hay borrador pendiente para forzar guardado: {tab_id}")
            return False

    def force_save_all(self):
        """
        Fuerza el guardado inmediato de todos los borradores pendientes

        Útil al cerrar la aplicación o ventana para asegurar que
        no se pierdan datos.
        """
        logger.info(f"Forzando guardado de {len(self.pending_drafts)} borradores pendientes...")

        # Obtener lista de tab_ids (copia para evitar modificación durante iteración)
        tab_ids = list(self.pending_drafts.keys())

        for tab_id in tab_ids:
            self.force_save(tab_id)

        logger.info("✅ Todos los borradores guardados")

    def load_all_drafts(self) -> list[ItemDraft]:
        """
        Carga todos los borradores desde BD

        Returns:
            Lista de objetos ItemDraft
        """
        try:
            draft_dicts = self.db.get_all_item_drafts()

            drafts = []
            for draft_dict in draft_dicts:
                try:
                    draft = ItemDraft.from_dict(draft_dict)
                    drafts.append(draft)
                    self.draft_loaded.emit(draft.tab_id)
                except Exception as e:
                    logger.error(f"Error parseando borrador {draft_dict.get('tab_id')}: {e}")
                    continue

            self.stats['loads'] += len(drafts)
            logger.info(f"📂 Cargados {len(drafts)} borradores desde BD")
            return drafts

        except Exception as e:
            logger.error(f"Error cargando borradores: {e}")
            self.stats['errors'] += 1
            return []

    def load_draft(self, tab_id: str) -> Optional[ItemDraft]:
        """
        Carga un borrador específico desde BD

        Args:
            tab_id: ID de la pestaña

        Returns:
            ItemDraft o None si no existe
        """
        try:
            draft_dict = self.db.get_item_draft(tab_id)

            if draft_dict:
                draft = ItemDraft.from_dict(draft_dict)
                self.draft_loaded.emit(tab_id)
                logger.info(f"📂 Borrador cargado: {tab_id}")
                return draft
            else:
                logger.debug(f"No existe borrador con tab_id: {tab_id}")
                return None

        except Exception as e:
            logger.error(f"Error cargando borrador {tab_id}: {e}")
            return None

    def delete_draft(self, tab_id: str) -> bool:
        """
        Elimina un borrador de BD y memoria

        Args:
            tab_id: ID de la pestaña

        Returns:
            True si se eliminó correctamente
        """
        try:
            # Cancelar guardado pendiente
            if tab_id in self.save_timers:
                self.save_timers[tab_id].stop()
                del self.save_timers[tab_id]
                logger.debug(f"Timer cancelado para eliminación: {tab_id}")

            # Eliminar de pendientes
            if tab_id in self.pending_drafts:
                del self.pending_drafts[tab_id]

            # Eliminar de BD
            success = self.db.delete_item_draft(tab_id)

            if success:
                logger.info(f"🗑️ Borrador eliminado: {tab_id}")
                return True
            else:
                logger.warning(f"No se pudo eliminar borrador: {tab_id}")
                return False

        except Exception as e:
            logger.error(f"Error eliminando borrador {tab_id}: {e}")
            self.stats['errors'] += 1
            return False

    def clear_all_drafts(self) -> int:
        """
        Elimina todos los borradores de BD y memoria

        Returns:
            Cantidad de borradores eliminados
        """
        try:
            # Cancelar todos los timers
            for timer in self.save_timers.values():
                timer.stop()

            self.save_timers.clear()
            self.pending_drafts.clear()

            # Eliminar de BD
            count = self.db.clear_all_item_drafts()

            logger.info(f"🗑️ Eliminados {count} borradores")
            return count

        except Exception as e:
            logger.error(f"Error limpiando borradores: {e}")
            self.stats['errors'] += 1
            return 0

    def has_pending_saves(self) -> bool:
        """
        Verifica si hay borradores pendientes de guardar

        Returns:
            True si hay borradores en queue
        """
        return len(self.pending_drafts) > 0

    def get_pending_count(self) -> int:
        """
        Retorna cantidad de borradores pendientes de guardar

        Returns:
            Número de borradores en queue
        """
        return len(self.pending_drafts)

    def get_stats(self) -> dict:
        """
        Retorna estadísticas de operaciones

        Returns:
            Dict con stats
        """
        return {
            'saves': self.stats['saves'],
            'loads': self.stats['loads'],
            'errors': self.stats['errors'],
            'pending': self.get_pending_count()
        }

    def reset_stats(self):
        """Resetea las estadísticas"""
        self.stats = {
            'saves': 0,
            'loads': 0,
            'errors': 0
        }
        logger.debug("Estadísticas reseteadas")

    def set_debounce(self, debounce_ms: int):
        """
        Cambia el tiempo de debounce

        Args:
            debounce_ms: Nuevo tiempo de debounce en milisegundos
        """
        if debounce_ms < 0:
            logger.warning("Debounce no puede ser negativo, usando 0")
            debounce_ms = 0

        self.debounce_ms = debounce_ms
        logger.info(f"Debounce actualizado a {debounce_ms}ms")

    def __del__(self):
        """Destructor: fuerza guardado de pendientes"""
        if hasattr(self, 'pending_drafts') and self.pending_drafts:
            logger.warning(f"Destruyendo manager con {len(self.pending_drafts)} borradores pendientes")
            self.force_save_all()
