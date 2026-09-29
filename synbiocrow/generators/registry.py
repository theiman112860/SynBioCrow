from __future__ import annotations
import os
from collections.abc import Iterable
from .doranet import DORAnetBackend
from .retrobiocat import RetroBioCatBackend
from .retropath import RetroPathBackend, RetroPathSettings
from .retropath_standalone import RetroPathStandaloneBackend, RetroPathStandaloneSettings
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

def _retropath_from_env()->RetroPathBackend:
    rules=os.getenv("SYNBIOCROW_RETROPATH_RULES")
    sink=os.getenv("SYNBIOCROW_RETROPATH_SINK")
    if not (rules and sink):
        return RetroPathBackend()
    return RetroPathBackend(settings=RetroPathSettings(
        rules_file=rules,
        sink_file=sink,
        knime_install=os.getenv("SYNBIOCROW_RETROPATH_KNIME"),
    ))

def _retropath_standalone_from_env()->RetroPathStandaloneBackend:
    exe=os.getenv("SYNBIOCROW_RETROPATH_STANDALONE_EXE")
    rules=os.getenv("SYNBIOCROW_RETROPATH_RULES")
    sink=os.getenv("SYNBIOCROW_RETROPATH_SINK")
    if not (exe and rules and sink):
        return RetroPathStandaloneBackend()
    return RetroPathStandaloneBackend(settings=RetroPathStandaloneSettings(
        executable=exe,
        rules_file=rules,
        sink_file=sink,
        max_steps=int(os.getenv("SYNBIOCROW_RETROPATH_STANDALONE_MAX_STEPS","3")),
        topx=int(os.getenv("SYNBIOCROW_RETROPATH_STANDALONE_TOPX","25")),
        timeout_minutes=int(os.getenv("SYNBIOCROW_RETROPATH_STANDALONE_TIMEOUT_MINUTES","8")),
    ))

def default_registry()->BackendRegistry:
    return BackendRegistry([
        DORAnetBackend(),
        RetroBioCatBackend(),
        _retropath_from_env(),
        _retropath_standalone_from_env(),
        BioPKSBackend(),
    ])
