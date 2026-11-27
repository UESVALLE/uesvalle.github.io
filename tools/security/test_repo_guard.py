"""Pruebas aisladas: no se leen bases ni credenciales institucionales."""
import pathlib
import tempfile
import unittest
from repo_guard import inspect_file


class RepoGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def add(self, name, content):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return name

    def test_blocks_operational_dataset(self):
        name = self.add("data/ircas/current/IRCAS.csv", "campo\nvalor\n")
        self.assertIn("DATA_OR_EVIDENCE_IN_GIT", inspect_file(self.root, name))

    def test_blocks_nested_evidence(self):
        name = self.add("assets/evidencias/foto.jpg", "dummy")
        self.assertIn("DATA_OR_EVIDENCE_IN_GIT", inspect_file(self.root, name))

    def test_blocks_client_side_password_literal(self):
        name = self.add("dashboards/test.html", '<script>const PASSWORD_TABLERO = "no-usar-esta-clave";</script>')
        self.assertIn("CLIENT_OR_SOURCE_CREDENTIAL", inspect_file(self.root, name))

    def test_blocks_environment_secrets(self):
        name = self.add(".env", "TEST_API_KEY=example_secret_value\n")
        reasons = inspect_file(self.root, name)
        self.assertIn("SENSITIVE_FILE_EXTENSION", reasons)
        self.assertIn("ENVIRONMENT_SECRET", reasons)

    def test_documentation_is_acceptable(self):
        name = self.add("docs/arquitectura_seguridad/GUIA.md", "No usar contraseñas en HTML.")
        self.assertEqual(inspect_file(self.root, name), [])

    def test_code_without_credentials_is_acceptable(self):
        name = self.add("tools/security/validar.py", "print('datos sintéticos')\n")
        self.assertEqual(inspect_file(self.root, name), [])


if __name__ == "__main__":
    unittest.main()
