# -*- coding: utf-8 -*-
u"""把主标注做成一个静态预览站，能直接挂 GitHub Pages。

图片缩到 1000 像素单独存文件，框存成归一化坐标的小 JSON，页面用 div 叠在图片上，
所以浏览器能缓存图片、按需加载，整站几十兆也能秒开。
"""
import os, re, json, argparse, sys, collections, shutil, io
from multiprocessing import Pool
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from classes import CLASSES, CONTENT
from site_pages import INDEX, VIEW

PALETTE = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#42d4f4',
           '#f032e6', '#bfef45', '#fabed4', '#469990', '#dcbeff', '#9a6324', '#fffac8',
           '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075']

FOLDER_NOTE = {'CA': u'日用品大类内部混装', 'CB': u'副食品大类内部混装',
               'CC': u'饮料大类内部混装', 'CD': u'水果大类内部混装'}


def key(name):
    b = os.path.splitext(name)[0]
    m = re.match(r'^(.*?)(\d+)$', b)
    return (m.group(1), int(m.group(2))) if m else (b, 0)


def group_of(folder, name):
    return folder + '/' + key(name)[0].rstrip('_')


def one_image(job):
    src, big, small, maxw, thw = job
    with Image.open(src) as im:
        W, H = im.size
        im = im.convert('RGB')
        for out, w in ((big, maxw), (small, thw)):
            s = min(1.0, float(w) / max(W, H))
            r = im.resize((int(W * s), int(H * s)), Image.LANCZOS) if s < 1.0 else im
            r.save(out, 'JPEG', quality=72 if w > 400 else 68, optimize=True)
    return src, W, H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--images', default=r'D:\tmp\0817b\0817')
    ap.add_argument('--master', default=r'D:\tmp\0817\master.json')
    ap.add_argument('--out', default=os.path.dirname(HERE))
    ap.add_argument('--maxw', type=int, default=1280)
    ap.add_argument('--thumb', type=int, default=160)
    ap.add_argument('--title', default=u'0817 数据集标注预览')
    ap.add_argument('--jobs', type=int, default=6)
    ap.add_argument('--no-images', action='store_true', help=u'只重写页面和数据，不动图片')
    a = ap.parse_args()

    master = json.load(open(a.master, encoding='utf-8'))

    groups = collections.OrderedDict()
    for folder in sorted(os.listdir(a.images)):
        sub = os.path.join(a.images, folder)
        if not os.path.isdir(sub):
            continue
        for name in sorted(os.listdir(sub), key=key):
            if name.lower().endswith(('.jpg', '.jpeg', '.png')):
                groups.setdefault(group_of(folder, name), []).append((folder, name))

    for d in ['data', 'img', 'th']:
        os.makedirs(os.path.join(a.out, d), exist_ok=True)

    jobs = []
    for g, items in groups.items():
        for folder, name in items:
            for d in ['img', 'th']:
                os.makedirs(os.path.join(a.out, d, folder), exist_ok=True)
            stem = os.path.splitext(name)[0] + '.jpg'
            jobs.append((os.path.join(a.images, folder, name),
                         os.path.join(a.out, 'img', folder, stem),
                         os.path.join(a.out, 'th', folder, stem),
                         a.maxw, a.thumb))

    size = {}
    if a.no_images:
        for src, big, small, _, _ in jobs:
            with Image.open(src) as im:
                size[src] = im.size
    else:
        done = 0
        pool = Pool(a.jobs)
        for src, W, H in pool.imap_unordered(one_image, jobs, chunksize=8):
            size[src] = (W, H)
            done += 1
            if done % 100 == 0:
                print('%d / %d 张图已缩' % (done, len(jobs)))
        pool.close()
        pool.join()

    cnt = collections.Counter()
    imgs_per_cls = collections.defaultdict(set)
    per_folder = collections.defaultdict(lambda: [0, 0])
    cards, index = [], []

    for g, items in groups.items():
        frames, nb = [], 0
        for folder, name in items:
            W, H = size[os.path.join(a.images, folder, name)]
            boxes = []
            for b in master['%s/%s' % (folder, name)]['boxes']:
                x1, x2 = sorted((b['x1'], b['x2']))
                y1, y2 = sorted((b['y1'], b['y2']))
                x1, y1 = max(0.0, x1), max(0.0, y1)
                x2, y2 = min(float(W), x2), min(float(H), y2)
                if x2 - x1 < 2 or y2 - y1 < 2:
                    continue
                boxes.append([b['c'], round(x1 / W, 4), round(y1 / H, 4),
                              round(x2 / W, 4), round(y2 / H, 4)])
                cnt[b['c']] += 1
                imgs_per_cls[b['c']].add('%s/%s' % (folder, name))
            frames.append({'f': folder, 'n': os.path.splitext(name)[0] + '.jpg',
                           'r': round(float(W) / H, 4), 'b': boxes})
            nb += len(boxes)
            per_folder[folder][0] += 1
            per_folder[folder][1] += len(boxes)
        gid = g.replace('/', '_')
        json.dump({'group': g, 'frames': frames},
                  open(os.path.join(a.out, 'data', gid + '.json'), 'w', encoding='utf-8'),
                  ensure_ascii=False, separators=(',', ':'))
        index.append((gid, g, len(frames), nb))
        cards.append(u'<div class="card"><a href="view.html?g=%s">%s</a>'
                     u'<div class="m">%d 张图，%d 个框</div></div>' % (gid, g, len(frames), nb))
        print('%-20s %3d 张  %4d 框' % (g, len(frames), nb))

    n_img = sum(x[2] for x in index)
    n_box = sum(x[3] for x in index)
    sub = u'%d 张图，%d 个框，%d 个类别，%d 个拍摄序列。' % (
        n_img, n_box, len([1 for i in range(len(CLASSES)) if cnt[i]]), len(index))

    clsrows = u''.join(
        u'<tr><td class="n">%d</td><td><span class="sw" style="background:%s"></span>%s</td>'
        u'<td>%s</td><td class="n">%d</td><td class="n">%d</td></tr>'
        % (i, PALETTE[i], code, name, len(imgs_per_cls[i]), cnt[i])
        for i, (code, name) in enumerate(CLASSES))

    foldrows = u''.join(
        u'<tr><td>%s</td><td>%s</td><td class="n">%d</td><td class="n">%d</td></tr>'
        % (f, FOLDER_NOTE.get(f, ''), v[0], v[1]) for f, v in sorted(per_folder.items()))

    open(os.path.join(a.out, 'index.html'), 'w', encoding='utf-8').write(
        INDEX.replace('__TITLE__', a.title).replace('__SUB__', sub)
             .replace('__CARDS__', u''.join(cards))
             .replace('__CLSROWS__', clsrows).replace('__FOLDROWS__', foldrows))

    open(os.path.join(a.out, 'view.html'), 'w', encoding='utf-8').write(
        VIEW.replace('__TITLE__', a.title)
            .replace('__CLS__', json.dumps([[c, n] for c, n in CLASSES], ensure_ascii=False))
            .replace('__COLORS__', json.dumps(PALETTE))
            .replace('__GROUPS__', json.dumps([[gid, g, n] for gid, g, n, _ in index],
                                              ensure_ascii=False)))

    open(os.path.join(a.out, '.nojekyll'), 'w').write('')
    open(os.path.join(a.out, 'robots.txt'), 'w').write('User-agent: *\nDisallow: /\n')

    total = sum(os.path.getsize(os.path.join(r, f))
                for r, _, fs in os.walk(a.out) for f in fs)
    print('\n%d 张图，%d 个框，整站 %.0f MB，输出在 %s' % (n_img, n_box, total / 1e6, a.out))


if __name__ == '__main__':
    main()
