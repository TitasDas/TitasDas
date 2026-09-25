"""Profile teasers: 656x492 looping GIFs built to be read at 328 px.

Solid headline band on top (one short idea per beat), a clean crop of the
product below, a closing card that asks for the click.
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

FONTS = os.path.expanduser('~/.claude/skills/canvas-design/canvas-fonts/')
TW, TH, BAND = 656, 492, 112
FPS = 10; BEAT = 17; XF = 3


def font(n, s): return ImageFont.truetype(FONTS + n, s)


def ease(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def crop_to(img, box, zoom=1.0, focus=(0.5, 0.5)):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    if zoom > 1:
        nw, nh = w / zoom, h / zoom
        cx, cy = x0 + w * focus[0], y0 + h * focus[1]
        x0 = min(max(cx - nw / 2, box[0]), box[2] - nw); y0 = min(max(cy - nh / 2, box[1]), box[3] - nh)
        w, h = nw, nh
    return img.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((TW, TH - BAND), Image.LANCZOS)


def band(text, cfg):
    b = Image.new('RGB', (TW, BAND), cfg['band']); d = ImageDraw.Draw(b)
    f = cfg['font']; tw = d.textlength(text, font=f)
    while tw > TW - 60:
        f = ImageFont.truetype(f.path, f.size - 2); tw = d.textlength(text, font=f)
    d.rectangle((0, BAND - 6, TW, BAND), fill=cfg['accent'])
    d.text((30, (BAND - 6 - f.size) // 2 - 4), text, font=f, fill=(255, 255, 255))
    return b


def frame(content, text, cfg):
    img = Image.new('RGB', (TW, TH)); img.paste(band(text, cfg), (0, 0)); img.paste(content, (0, BAND)); return img


def card(cfg):
    img = Image.new('RGB', (TW, TH), cfg['band']); d = ImageDraw.Draw(img)
    if cfg.get('logo'):
        lg = Image.open(cfg['logo']).convert('RGBA'); lg.thumbnail((96, 96)); img.paste(lg, ((TW - lg.width) // 2, 70), lg)
    y = 190
    for text, f, col in ((cfg['name'], cfg['name_font'], (255, 255, 255)), (cfg['value'], cfg['value_font'], (225, 232, 244))):
        tw = d.textlength(text, font=f); d.text(((TW - tw) / 2, y), text, font=f, fill=col); y += f.size + 26
    cta = cfg['cta']; f = cfg['cta_font']; tw = d.textlength(cta, font=f)
    d.rounded_rectangle(((TW - tw) / 2 - 26, y + 18, (TW + tw) / 2 + 26, y + 18 + f.size + 28), radius=(f.size + 28) // 2, fill=cfg['accent'])
    d.text(((TW - tw) / 2, y + 30), cta, font=f, fill=(255, 255, 255))
    return img


def build(cfg, beats, out):
    """beats: list of (headline, [PIL images for the content area, one per GIF frame])."""
    frames = []
    texts = []
    for text, contents in beats:
        frames.append([frame(c, text, cfg) for c in contents]); texts.append(text)
    frames.append([card(cfg)] * int(BEAT * 1.6)); texts.append(None)
    seq = []
    for i, fr in enumerate(frames):
        if i and seq:
            for j in range(XF):
                blended = Image.blend(seq[-XF + j], fr[j], ease((j + 1) / (XF + 1)))
                if texts[i] is not None:
                    blended.paste(band(texts[i], cfg), (0, 0))  # headline switches cleanly, only the picture fades
                seq[-XF + j] = blended
            seq.extend(fr[XF:])
        else:
            seq.extend(fr)
    tmp = out + '.d'; os.makedirs(tmp, exist_ok=True)
    for k, im in enumerate(seq): im.save(f'{tmp}/{k:04d}.png')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', f'{tmp}/%04d.png', '-vf',
                    'split[s0][s1];[s0]palettegen=max_colors=160:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle',
                    '-loop', '0', out], check=True)
    print(out, len(seq), 'frames', os.path.getsize(out) // 1024, 'KB')


def still(path, box, zoom=(1.0, 1.06), focus=(0.5, 0.5), n=BEAT):
    im = Image.open(path).convert('RGB')
    return [crop_to(im, box, zoom[0] + (zoom[1] - zoom[0]) * ease(i / (n - 1)), focus) for i in range(n)]


def seqs(paths, box, n=BEAT):
    out = []
    for i in range(n):
        p = paths[min(len(paths) - 1, int(i * len(paths) / n))]
        out.append(crop_to(Image.open(p).convert('RGB'), box))
    return out


HERE = os.path.dirname(os.path.abspath(__file__))
which = sys.argv[1]

if which == 'wd':
    C = f'{HERE}/caps/'; box = (0, 0, 1080, 626)
    cfg = dict(band=(15, 30, 51), accent=(31, 95, 191), font=font('Outfit-Bold.ttf', 44), name='WD My Passport', value='Unlocker for Linux',
               name_font=font('Outfit-Bold.ttf', 50), value_font=font('Outfit-Regular.ttf', 34), cta='Watch the walkthrough', cta_font=font('Outfit-Bold.ttf', 28),
               logo='/home/td/work/wd-hdd-unlocker/assets/brand/icon-128.png')
    typing = [f'{C}02-unlock-empty.png'] + [f'{C}03-typing-{i:02d}.png' for i in range(1, 10)]
    beats = [('Locked WD drive?', still(C + '01-drive-locked.png', (230, 80, 1080, 572), zoom=(1.0, 1.05))),
             ('Unlock it on Linux', seqs(typing, (110, 90, 710, 438))),
             ('Copy files as yourself', still(C + '05-volumes.png', (230, 288, 1080, 780), zoom=(1.0, 1.05))),
             ('Change the password', still(C + '07-change-dialog.png', (240, 160, 860, 519), zoom=(1.0, 1.05))),
             ('Format or erase', still(C + '09-format-dialog.png', (230, 190, 850, 549), zoom=(1.0, 1.05))),
             ('Eject, and it locks', still(C + '12-drive-dark.png', (230, 60, 1080, 552), zoom=(1.0, 1.05)))]
    build(cfg, beats, f'{HERE}/wd-teaser.gif')

elif which == 'fm':
    C = f'{HERE}/fm/caps/'
    cfg = dict(band=(26, 40, 34), accent=(176, 74, 40), font=font('InstrumentSerif-Regular.ttf', 54), name='Forced Move', value='Your move limits theirs',
               name_font=font('InstrumentSerif-Regular.ttf', 72), value_font=font('InstrumentSans-Regular.ttf', 32), cta='Watch it played', cta_font=font('InstrumentSans-Bold.ttf', 28))
    board = (240, 110, 1040, 574)
    beats = [('Tic-tac-toe, with a catch', still(C + '01-home.png', (0, 20, 1280, 761), focus=(0.5, 0.35))),
             ('Place your mark', still(C + '04-origin.png', (200, 100, 1080, 610), zoom=(1.0, 1.05))),
             ('Then lock their squares', seqs([C + '05-first-allowed.png'] * 2 + [C + '06-committed-ai-replied.png'] * 3, (200, 100, 1080, 610))),
             ('The computer fights back', still(C + '07-turn2-origin.png', (200, 100, 1080, 610))),
             ('Nine boards in one', seqs([C + '14-ultimate-move.png', C + '15-ultimate-move2.png', C + '16-ultimate-move3.png'], (160, 110, 1120, 666))),
             ('Play a friend by link', still(C + '17-lobby.png', (0, 0, 1280, 741), zoom=(1.4, 1.5), focus=(0.5, 0.45)))]
    build(cfg, beats, f'{HERE}/fm-teaser.gif')

elif which == 'dd':
    R = f'{HERE}/dd/'
    WALL = Image.open(R + 'wallpaper.png').convert('RGB')
    EV = {e['name']: e['t'] for e in json.load(open(R + 'rec/events.json'))}
    def keyed(t):
        i = max(1, int(t * 25) + 1)
        im = Image.open(f'{R}rec/frames/{i:05d}.png').convert('RGB'); r, g, b = im.split()
        mx = ImageChops.lighter(ImageChops.lighter(r, g), b)
        mask = mx.point(lambda v: 255 if v <= 6 else 0).filter(ImageFilter.MinFilter(3))
        return Image.composite(WALL, im, mask)
    box = (0, 330, 830, 960)
    def clip(t0, t1, b=box):
        return [crop_to(keyed(t0 + (t1 - t0) * i / (BEAT - 1)), b) for i in range(BEAT)]
    cfg = dict(band=(38, 26, 20), accent=(232, 140, 92), font=font('BricolageGrotesque-Bold.ttf', 46), name='Desktop Drawer', value='Enjoy your wallpaper',
               name_font=font('BricolageGrotesque-Bold.ttf', 58), value_font=font('WorkSans-Regular.ttf', 32), cta='Watch it in action', cta_font=font('BricolageGrotesque-Bold.ttf', 28),
               logo='/home/td/work/desktop-drawer-public/desktop/applet/desktop-drawer@linux-automations/icon.png')
    intro = [crop_to(Image.open(f'{R}frames/{k:05d}.png').convert('RGB'), (0, 0, 1280, 960)) for k in range(46, 46 + BEAT * 2, 2)]
    beats = [('Desktop full of files?', [crop_to(Image.open(f'{R}frames/00002.png').convert('RGB'), (0, 0, 1280, 960))] * 6 + intro[:BEAT - 6]),
             ('Tidy them into the panel', intro),
             ('Hover to open', clip(EV['hover-icon'] - 0.3, EV['menu-open'] + 0.4)),
             ('Browse folders in place', clip(EV['menu-open'] + 0.4, EV['reading'])),
             ('Pick any folder', clip(EV['settings'] + 0.6, EV['settings'] + 2.6, (400, 0, 1280, 660))),
             ('Light or dark', clip(EV['light'] + 1.6, EV['light-menu']))]
    build(cfg, beats, f'{HERE}/dd-teaser.gif')

elif which == 'rs':
    R = f'{HERE}/rs/'
    def clip(t0, t1, b=(0, 40, 1280, 781)):
        return [crop_to(Image.open(f'{R}f{int((t0 + (t1 - t0) * i / (BEAT - 1)) * 10) + 1:05d}.png').convert('RGB'), b) for i in range(BEAT)]
    cfg = dict(band=(122, 44, 16), accent=(232, 128, 72), font=font('InstrumentSans-Bold.ttf', 44), name='Readstand', value='Read on purpose. Keep what you learn.',
               name_font=font('InstrumentSerif-Regular.ttf', 72), value_font=font('InstrumentSans-Regular.ttf', 30), cta='Watch the walkthrough', cta_font=font('InstrumentSans-Bold.ttf', 28),
               logo='/home/td/work/software-shop-wd-unlocker/public/media/readstand/icon.png')
    beats = [('Follow the sites you choose', clip(7.0, 10.8)),
             ('Read without clutter', clip(14.5, 19.8)),
             ('Pick up where you left off', clip(23.0, 28.8)),
             ('Save the lines that matter', clip(38.0, 44.0)),
             ('Export notes to Markdown', clip(47.5, 52.5)),
             ('Map what you learn', clip(81.5, 88.0))]
    build(cfg, beats, f'{HERE}/rs-teaser.gif')
