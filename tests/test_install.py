import importlib.util, json, pathlib, tempfile, unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('installer', ROOT / 'scripts/install_pet.py')
installer = importlib.util.module_from_spec(spec); spec.loader.exec_module(installer)
KEY = '["example-account","example-user"]'

class InstallTests(unittest.TestCase):
    def fixture(self, home):
        state = {'electron-persisted-atom-state': {
            installer.MAPPED: {KEY: {'custom:luoxiaohei': 'pet_example', 'custom:other': 'pet_other'}},
            installer.OBSERVED: {KEY: 'pet_example'}, installer.PENDING: {},
            'unrelated': {'time': '2026-10-25T01:00:00Z', 'values': [None, False, [], {'name': 'example'}]}}}
        (home / '.codex-global-state.json').write_text(json.dumps(state), encoding='utf-8')
        (home / 'config.toml').write_text('model = "example"\n[desktop]\nselected-avatar-id = "pet_example"\npet-size = 120\n[other]\nvalue = 1\n', encoding='utf-8')
        return state

    def test_install_backup_preservation_and_idempotence(self):
        with tempfile.TemporaryDirectory() as directory:
            home = pathlib.Path(directory); original = self.fixture(home)
            result = installer.install(home, process_check=lambda: False)
            state = json.loads((home / '.codex-global-state.json').read_bytes())
            atoms = state['electron-persisted-atom-state']
            self.assertEqual(atoms['unrelated'], original['electron-persisted-atom-state']['unrelated'])
            self.assertEqual(atoms[installer.MAPPED][KEY], {'custom:other': 'pet_other'})
            self.assertTrue(atoms[installer.PENDING][KEY][installer.LOCAL]['failedPermanently'])
            self.assertEqual(json.loads((pathlib.Path(result['backup']) / '.codex-global-state.json').read_bytes()), original)
            self.assertEqual((home / 'pets/luoxiaohei/spritesheet.webp').read_bytes(), (ROOT / 'pet/luoxiaohei/spritesheet.webp').read_bytes())
            installer.install(home, process_check=lambda: False)
            self.assertEqual(json.loads((home / '.codex-global-state.json').read_bytes()), state)

    def test_running_client_blocks_writes_but_dry_run_is_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            home = pathlib.Path(directory); self.fixture(home)
            before = (home / '.codex-global-state.json').read_bytes()
            with self.assertRaisesRegex(RuntimeError, 'Fully quit'):
                installer.install(home, process_check=lambda: True)
            installer.install(home, dry_run=True, process_check=lambda: True)
            self.assertEqual((home / '.codex-global-state.json').read_bytes(), before)
            self.assertFalse((home / 'pets').exists())

    def test_toml_sections_comments_and_line_endings(self):
        for text in ['', 'model = "example"\n', '[desktop]\r\npet-size = 120\r\n[other]\r\nvalue = 1\r\n', '[desktop]\nselected-avatar-id = "old" # keep other settings\npet-size=120\n']:
            updated = installer.update_config(text)
            self.assertEqual(installer.update_config(updated), updated)
            self.assertIn('selected-avatar-id = "custom:luoxiaohei"', updated)

if __name__ == '__main__': unittest.main()
