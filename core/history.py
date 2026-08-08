"""
Historique Undo/Redo (PATCH 27).

Pile de snapshots (chaînes JSON) du document, agnostique de Qt et du
contenu réel des blocs — donc facilement testable seule. Un
"snapshot" est la sérialisation complète du document
(``Document.to_dict()``, cf. PATCH 8/9), ce qui garantit un état
totalement indépendant de l'état courant, quel que soit le type de
bloc modifié (texte, checklist, tableau, image, ...).
"""
from __future__ import annotations

_DEFAULT_MAX_HISTORY = 200


class UndoHistory:
    """Pile undo/redo générique basée sur des snapshots texte.

    Utilisation typique :
        history = UndoHistory(snapshot())
        ... l'utilisateur modifie le document ...
        history.check(snapshot())   # crée un point d'annulation si besoin
        ...
        previous = history.undo(snapshot())  # None si rien à annuler
        next_ = history.redo()               # None si rien à rétablir
    """

    def __init__(self, initial_snapshot: str, max_history: int = _DEFAULT_MAX_HISTORY) -> None:
        self._baseline = initial_snapshot
        self._undo_stack: list[str] = []
        self._redo_stack: list[str] = []
        self._max_history = max_history

    @property
    def baseline(self) -> str:
        """Dernier snapshot connu comme étant l'état courant "propre"."""
        return self._baseline

    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    def check(self, current_snapshot: str) -> bool:
        """Crée un point d'annulation si `current_snapshot` diffère de
        la référence courante. Retourne True si un point a été créé.

        Vide la pile de rétablissement (toute nouvelle action rend les
        anciens "redo" obsolètes — comportement standard).
        """
        if current_snapshot == self._baseline:
            return False
        self._undo_stack.append(self._baseline)
        if len(self._undo_stack) > self._max_history:
            self._undo_stack.pop(0)
        self._redo_stack.clear()
        self._baseline = current_snapshot
        return True

    def undo(self, current_snapshot: str) -> str | None:
        """Confirme d'abord tout changement en attente (`current_snapshot`),
        puis dépile un état antérieur. None si rien à annuler."""
        self.check(current_snapshot)
        if not self._undo_stack:
            return None
        self._redo_stack.append(self._baseline)
        self._baseline = self._undo_stack.pop()
        return self._baseline

    def redo(self) -> str | None:
        """Rétablit le dernier état annulé. None si rien à rétablir."""
        if not self._redo_stack:
            return None
        self._undo_stack.append(self._baseline)
        if len(self._undo_stack) > self._max_history:
            self._undo_stack.pop(0)
        self._baseline = self._redo_stack.pop()
        return self._baseline
