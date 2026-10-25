"""Archive the exact reviewed Git commit, excluding local and ignored files."""
import argparse, hashlib, json, pathlib, subprocess, sys, zipfile

root = pathlib.Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=pathlib.Path, default=root / 'dist/luoxiaohei-codex-pet-v1.0.0.zip')
args = parser.parse_args()
subprocess.run([sys.executable, str(root / 'scripts/validate_pet.py')], check=True)
if subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=root):
    raise SystemExit('Commit reviewed changes before building a release.')
output = args.output.resolve(); output.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(['git', 'archive', '--format=zip', '--prefix=luoxiaohei-codex-pet/', '--output=' + str(output), 'HEAD'], cwd=root, check=True)
with zipfile.ZipFile(output) as archive:
    if archive.testzip() is not None:
        raise SystemExit('ZIP verification failed')
print(json.dumps({'ok': True, 'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
                  'sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'bytes': output.stat().st_size}))
