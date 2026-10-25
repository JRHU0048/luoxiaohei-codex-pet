"""Check metadata, full-atlas timing, transparency, and all approved form pixels."""
import argparse, hashlib, json, pathlib
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
COUNTS = [6, 8, 8, 4, 5, 8, 6, 6, 6, 8, 8]
FORMS = ['cat.webp', 'black-haired.webp', 'white-haired.webp']

def validate(directory, seconds=10):
    metadata = json.loads((directory / 'pet.json').read_text(encoding='utf-8-sig'))
    for key, value in dict(id='luoxiaohei', displayName='luoxiaohei', description='3D luoxiaohei pet', spriteVersionNumber=2, spritesheetPath='spritesheet.webp').items():
        if metadata.get(key) != value:
            raise ValueError('Unexpected metadata: ' + key)
    sheet = directory / 'spritesheet.webp'
    checks = []
    with Image.open(sheet) as image:
        if image.format != 'WEBP' or image.size != (1536, 2288) or image.n_frames != 3 or image.info.get('loop') != 0:
            raise ValueError('Expected a looping three-frame v2 WebP')
        for i, form in enumerate(FORMS):
            image.seek(i); image.load(); rgba = image.convert('RGBA')
            if image.info.get('duration') != seconds * 1000:
                raise ValueError('Unexpected form duration')
            with Image.open(ROOT / 'source-atlases' / form) as reference:
                if rgba.tobytes() != reference.convert('RGBA').tobytes():
                    raise ValueError('Pixels differ from approved form: ' + form)
            alpha = rgba.getchannel('A')
            for row, required in enumerate(COUNTS):
                for col in range(8):
                    maximum = alpha.crop((col * 192, row * 208, (col + 1) * 192, (row + 1) * 208)).getextrema()[1]
                    if col < required and maximum == 0:
                        raise ValueError(f'Missing artwork at form {i}, row {row}, cell {col}')
                    if col >= required and (row, col) != (0, 6) and maximum != 0:
                        raise ValueError(f'Artwork in unused cell at form {i}, row {row}, cell {col}')
            checks.append(dict(form=form, durationMs=image.info['duration'], pixelsMatchSource=True))
    return dict(ok=True, spriteVersionNumber=2, width=1536, height=2288, loop=0, forms=checks,
                sha256=hashlib.sha256(sheet.read_bytes()).hexdigest())

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=pathlib.Path, default=ROOT / 'pet' / 'luoxiaohei')
    parser.add_argument('--seconds', type=int, default=10)
    args = parser.parse_args()
    print(json.dumps(validate(args.directory, args.seconds), indent=2))
