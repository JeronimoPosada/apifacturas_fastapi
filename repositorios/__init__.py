"""Paquete de repositorios — Clase base de PostgreSQL."""

from .base_repositorio_postgresql import BaseRepositorioPostgreSQL
# ↑ El punto (.) significa "desde este mismo paquete".
# Hace que BaseRepositorioPostgreSQL sea importable como:
#   from repositorios import BaseRepositorioPostgreSQL
# En vez de:
#   from repositorios.base_repositorio_postgresql import BaseRepositorioPostgreSQL