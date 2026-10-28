# Control preventivo de seguridad (rama de arquitectura)

El script `repo_guard.py` revisa **únicamente los archivos añadidos/modificados** en un PR para prevenir la incorporación de nuevos datasets crudos, evidencias y credenciales incrustadas. La ejecución automática usa `.github/workflows/security-guard.yml`.

Comandos:
```bash
python -m unittest discover -s tools/security -p 'test_*.py' -v
python tools/security/repo_guard.py --base origin/main
```

- **No es un antivirus ni un escáner exhaustivo del histórico.** Los 704 archivos previos requieren auditoría y clasificación por separado.
- Es deliberadamente conservador: bloquea nuevos cambios a `data/`, `archive/` y carpetas de evidencias hasta implementar almacenamiento privado y aprobar el proceso.
- Si necesita modificar datos previamente rastreados, no desactive el guard en producción; abra un PR específico para cambiar su flujo de publicación y retire los datos del artefacto servido.
- Nunca imprima secretos en logs. El script sólo reporta rutas y códigos de regla.
- Toda promoción a `main` requiere revisión y responsable institucional.
