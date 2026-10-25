import hashlib, importlib.util, pathlib, tempfile, unittest
ROOT = pathlib.Path(__file__).resolve().parent.parent
def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

class BuildTests(unittest.TestCase):
    def test_rebuild_preserves_released_bytes_and_all_form_pixels(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = pathlib.Path(temporary)
            actual = load('build_pet').build(output)
            released = hashlib.sha256((ROOT / 'pet/luoxiaohei/spritesheet.webp').read_bytes()).hexdigest()
            self.assertEqual(actual, released)
            self.assertTrue(load('validate_pet').validate(output)['ok'])

if __name__ == '__main__': unittest.main()
