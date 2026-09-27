from __future__ import annotations
from collections.abc import Iterable
from .doranet import DORAnetBackend
from .retrobiocat import RetroBioCatBackend
from .retropath import RetroPathBackend
from .biopks import BioPKSBackend

class BackendRegistry:
    def __init__(self,backends:Iterable[object]=()):
        self._backends={}
        for backend in backends:self.register(backend)
    def register(self,backend:object)->None:
        backend_id=getattr(backend,"backend_id")
        if backend_id in self._backends: raise ValueError(f"duplicate backend_id: {backend_id}")
        self._backends[backend_id]=backend
    def get(self,backend_id:str): return self._backends[backend_id]
    def ids(self)->tuple[str,...]: return tuple(sorted(self._backends))

def default_registry()->BackendRegistry:
    return BackendRegistry([DORAnetBackend(),RetroBioCatBackend(),RetroPathBackend(),BioPKSBackend()])
