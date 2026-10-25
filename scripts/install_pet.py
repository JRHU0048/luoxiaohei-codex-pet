"""Install only after the desktop client exits; preserve unrelated JSON/TOML data."""
import argparse, copy, ctypes, datetime, hashlib, json, os, pathlib, re, sys, tomllib, uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOCAL = 'custom:luoxiaohei'
MAPPED = 'migrated-cloud-pet-ids-v1'
PENDING = 'pending-cloud-pet-migrations-v1'
OBSERVED = 'last-observed-cloud-pet-selection-v1'

def client_running():
    if os.name != 'nt':
        raise RuntimeError('This installer is tested only on Windows.')
    from ctypes import wintypes
    class Entry(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('usage', wintypes.DWORD), ('pid', wintypes.DWORD),
                    ('heap', ctypes.c_size_t), ('module', wintypes.DWORD), ('threads', wintypes.DWORD),
                    ('parent', wintypes.DWORD), ('priority', wintypes.LONG), ('flags', wintypes.DWORD),
                    ('exe', wintypes.WCHAR * 260)]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.Process32FirstW.argtypes = kernel.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.CreateToolhelp32Snapshot(2, 0)
    if handle == ctypes.c_void_p(-1).value:
        raise RuntimeError('Could not check desktop processes.')
    entry = Entry(); entry.size = ctypes.sizeof(entry)
    try:
        more = kernel.Process32FirstW(handle, ctypes.byref(entry))
        while more:
            if entry.exe.lower() in ('chatgpt.exe', 'codex.exe'):
                return True
            more = kernel.Process32NextW(handle, ctypes.byref(entry))
        return False
    finally:
        kernel.CloseHandle(handle)

def update_state(state):
    state = copy.deepcopy(state)
    atoms = state.get('electron-persisted-atom-state')
    if not isinstance(atoms, dict):
        raise ValueError('Unknown desktop state schema; no files changed.')
    keys = set()
    for name in (MAPPED, PENDING, OBSERVED):
        value = atoms.get(name, {})
        if not isinstance(value, dict):
            raise ValueError('Unknown migration state schema: ' + name)
        keys.update(value)
    cache = atoms.get('cloud-pet-artwork-cache')
    if isinstance(cache, dict) and cache.get('accountId') and cache.get('userId'):
        keys.add(json.dumps([cache['accountId'], cache['userId']], ensure_ascii=False, separators=(',', ':')))
    if not keys:
        raise ValueError('No known desktop account records. Open and sign in to the desktop app once, fully quit it, then retry.')
    mapped = atoms.setdefault(MAPPED, {})
    pending = atoms.setdefault(PENDING, {})
    for key in keys:
        if not isinstance(mapped.get(key, {}), dict) or not isinstance(pending.get(key, {}), dict):
            raise ValueError('Unknown account migration schema; no files changed.')
        if key in mapped:
            mapped[key].pop(LOCAL, None)
        pending.setdefault(key, {})[LOCAL] = {'failedPermanently': True}
    return state, len(keys)

def update_config(text):
    old = tomllib.loads(text)
    newline = '\r\n' if '\r\n' in text else '\n'
    line = 'selected-avatar-id = "' + LOCAL + '"' + newline
    section = re.search(r'(?ms)^\[desktop\][^\r\n]*\r?\n(?P<body>.*?)(?=^\[|\Z)', text)
    if section:
        body = section['body']
        pattern = r'(?m)^[ \t]*selected-avatar-id\s*=[^\r\n]*(?:\r?\n|$)'
        count = len(re.findall(pattern, body))
        if count > 1:
            raise ValueError('Duplicate pet selection entries; no files changed.')
        body = re.sub(pattern, lambda _: line, body) if count else line + body
        result = text[:section.start('body')] + body + text[section.end('body'):]
    else:
        if 'desktop' in old:
            raise ValueError('Unsupported inline desktop table; no files changed.')
        result = text.rstrip() + newline + newline + '[desktop]' + newline + line
    parsed = tomllib.loads(result)
    expected = copy.deepcopy(old); expected.setdefault('desktop', {})['selected-avatar-id'] = LOCAL
    if parsed != expected:
        raise ValueError('Configuration transform changed unrelated values.')
    return result

def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.luoxiaohei-' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('xb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)

def install(home, source_root=ROOT, dry_run=False, process_check=None):
    home = pathlib.Path(home).resolve()
    source_root = pathlib.Path(source_root).resolve()
    source = source_root / 'pet/luoxiaohei'
    manifest = json.loads((source / 'pet.json').read_text(encoding='utf-8-sig'))
    if manifest.get('id') != 'luoxiaohei' or manifest.get('spriteVersionNumber') != 2 or manifest.get('spritesheetPath') != 'spritesheet.webp':
        raise ValueError('Unexpected source pet manifest.')
    checksums = json.loads((source_root / 'checksums.json').read_text(encoding='utf-8'))
    image = (source / 'spritesheet.webp').read_bytes()
    digest = hashlib.sha256(image).hexdigest()
    if digest != checksums['pet/luoxiaohei/spritesheet.webp']:
        raise ValueError('Pet artwork failed its SHA256 check.')
    state_path = home / '.codex-global-state.json'; config_path = home / 'config.toml'
    state_before = state_path.read_bytes()
    config_before = config_path.read_bytes() if config_path.exists() else None
    state, accounts = update_state(json.loads(state_before))
    config_text = (config_before or b'').decode('utf-8-sig')
    config = update_config(config_text).encode('utf-8-sig' if (config_before or b'').startswith(b'\xef\xbb\xbf') else 'utf-8')
    plan = dict(dryRun=dry_run, localPetId=LOCAL, secondsPerForm=10, accountRecordsPinned=accounts,
                target=str(home / 'pets/luoxiaohei'), sha256=digest)
    if dry_run:
        return plan
    if (process_check or client_running)():
        raise RuntimeError('Fully quit the desktop app, including the system tray, then retry. No files changed.')
    if state_path.read_bytes() != state_before or (config_path.read_bytes() if config_path.exists() else None) != config_before:
        raise RuntimeError('Desktop settings changed while planning; no files changed.')
    target = home / 'pets/luoxiaohei'
    values = {state_path: json.dumps(state, ensure_ascii=False, separators=(',', ':')).encode('utf-8'),
              config_path: config, target / 'pet.json': (source / 'pet.json').read_bytes(),
              target / 'spritesheet.webp': image}
    before = {path: path.read_bytes() if path.exists() else None for path in values}
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:8]
    backup = home / 'pet-backups/luoxiaohei' / stamp
    for path, data in before.items():
        if data is not None:
            atomic_write(backup / path.relative_to(home), data)
    try:
        for path, data in values.items():
            atomic_write(path, data)
        if any(path.read_bytes() != data for path, data in values.items()):
            raise RuntimeError('Installed data did not pass readback verification.')
    except BaseException:
        for path, data in before.items():
            if data is None:
                path.unlink(missing_ok=True)
            else:
                atomic_write(path, data)
        raise
    plan.update(installed=True, backup=str(backup), nextStep='Reopen the desktop app and observe a full 30-second cycle.')
    return plan

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--codex-home', type=pathlib.Path, default=pathlib.Path(os.environ.get('CODEX_HOME') or pathlib.Path.home() / '.codex'))
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(install(args.codex_home, dry_run=args.dry_run), indent=2))
    except Exception as error:
        print(str(error), file=sys.stderr); sys.exit(1)
