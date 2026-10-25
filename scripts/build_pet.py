"""Losslessly mux three complete v2 atlases; no image generation is performed."""
import argparse, hashlib, json, pathlib, struct
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
FORMS = ['cat.webp', 'black-haired.webp', 'white-haired.webp']

def chunk(tag, data):
    return tag + struct.pack('<I', len(data)) + data + (b'\0' if len(data) % 2 else b'')

def build(output, seconds=10):
    if not 1 <= seconds <= 3600:
        raise ValueError('seconds must be between 1 and 3600')
    sources = []
    body = chunk(b'VP8X', bytes([0x12, 0, 0, 0]) + (1535).to_bytes(3, 'little') + (2287).to_bytes(3, 'little'))
    body += chunk(b'ANIM', b'\0' * 6)
    for name in FORMS:
        source = ROOT / 'source-atlases' / name
        data = source.read_bytes()
        with Image.open(source) as image:
            if image.size != (1536, 2288) or getattr(image, 'n_frames', 1) != 1:
                raise ValueError('Each source must be a static 1536x2288 atlas')
            sources.append(image.convert('RGBA').tobytes())
        if data[:4] != b'RIFF' or data[8:12] != b'WEBP':
            raise ValueError('Invalid source WebP')
        position = 12; encoded = b''; lossless = False
        while position + 8 <= len(data):
            tag = data[position:position + 4]
            length = int.from_bytes(data[position + 4:position + 8], 'little')
            end = position + 8 + length + length % 2
            if end > len(data):
                raise ValueError('Truncated source chunk')
            if tag in (b'ALPH', b'VP8 ', b'VP8L'):
                encoded += data[position:end]
                lossless |= tag == b'VP8L'
            position = end
        if not lossless:
            raise ValueError('Sources must be lossless WebP')
        header = b'\0' * 6 + (1535).to_bytes(3, 'little') + (2287).to_bytes(3, 'little')
        header += (seconds * 1000).to_bytes(3, 'little') + bytes([2])
        body += chunk(b'ANMF', header + encoded)
    output.mkdir(parents=True, exist_ok=True)
    target = output / 'spritesheet.webp'
    target.write_bytes(b'RIFF' + struct.pack('<I', len(body) + 4) + b'WEBP' + body)
    with Image.open(target) as image:
        if image.n_frames != 3 or image.info.get('loop') != 0:
            raise ValueError('Invalid animation header')
        for i, expected in enumerate(sources):
            image.seek(i); image.load()
            if image.info.get('duration') != seconds * 1000 or image.convert('RGBA').tobytes() != expected:
                raise ValueError('A form or its timing changed during muxing')
    manifest = dict(id='luoxiaohei', displayName='luoxiaohei', description='3D luoxiaohei pet',
                    spriteVersionNumber=2, spritesheetPath='spritesheet.webp')
    (output / 'pet.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')
    return hashlib.sha256(target.read_bytes()).hexdigest()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=pathlib.Path, default=ROOT / 'pet' / 'luoxiaohei')
    parser.add_argument('--seconds', type=int, default=10)
    args = parser.parse_args()
    print(json.dumps({'ok': True, 'sha256': build(args.output, args.seconds)}))
