import pymysql.cursors
import shutil
import os
import pandas as pd
import json
from datetime import datetime
from pypinyin import lazy_pinyin
from requests.api import get
import re
import phpserialize

POSTS_DIR = '_posts'
IMG_DIR = 'assets/img/posts'

non_alpha_pattern = re.compile(r'[^a-zA-Z0-9.]')
continuous_under_line = re.compile(r'_+')
header_pattern = re.compile(r'(\n#+)([^\s#])')


def zh_to_en(name: str) -> str:
    return continuous_under_line.sub('_', non_alpha_pattern.sub(
        '_', '_'.join(lazy_pinyin(name.replace(' ', ''))).lower()))


def main():
    connection = pymysql.connect(host=os.environ['HOST'],
                                 user=os.environ['USER'],
                                 port=int(os.getenv('PORT', 3306)),
                                 password=os.environ['PASS'],
                                 database=os.environ['DB'],
                                 cursorclass=pymysql.cursors.DictCursor)

    with connection:
        with connection.cursor() as cursor:
            with open('posts.sql') as f:
                sql = f.read()

            cursor.execute(sql)

            result = cursor.fetchall()
            df = pd.DataFrame(result)

    for col in ['created', 'modified']:
        df.loc[:, col] = df[col].map(lambda x: datetime.fromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'))

    for col in ['tag_list', 'category_list']:
        df.loc[:, col] = df[col].map(lambda x: (x or '').split(','))

    df.loc[:, 'attachment_list'] = df['attachment_list'].map(
        lambda x: [each.split('@@') for each in x.split('##')] if x else []
    )

    df.loc[:, 'filename'] = df.apply(lambda row: row['created'][:10] + '-' + zh_to_en(row['title']), axis=1)

    for filename, title, created, modified, categories, tags, content, summary, attachment_list in df[
        ['filename', 'title', 'created', 'modified', 'category_list', 'tag_list', 'text', 'summary', 'attachment_list']
    ].iloc:
        y, m, d = created[:4], created[5:7], created[8:10]
        post_dir = os.path.join(POSTS_DIR, y, m, d)
        os.system(f'mkdir -p {post_dir}')

        body = [
            "---",
            f"title: {json.dumps(title, ensure_ascii=False)}",
            f"date: {created} +0800",
            f"last_modified_at: {modified} +0800",
            f"math: {str('$' in content).lower()}",
            f"render_with_liquid: false",
            f"categories: {json.dumps(categories, ensure_ascii=False)}",
        ]
        if ''.join(tags):
            body.append(f"tags: {json.dumps(tags, ensure_ascii=False).lower()}")
        if summary:
            body.append(f"description: {json.dumps(summary, ensure_ascii=False)}")
        body.extend(['---', content])

        content = '\n'.join(body).replace('\r\n', '\n')
        if header_pattern.findall(content):
            content = header_pattern.sub(r'\1 \2', content)
        if '\n# ' in content:
            content = content.replace('\n#', '\n##')

        if attachment_list:
            img_dir = os.path.join(IMG_DIR, y, m, d, filename)
            os.system(f'mkdir -p {img_dir}')

            for serialized_data, order in attachment_list:
                data = phpserialize.loads(serialized_data.encode('utf-8'), decode_strings=True)
                img_name = zh_to_en(data['name'])
                img_src_path = data['path']
                img_dst_path = os.path.join(img_dir, img_name)
                if os.path.exists(img_local_src_path := img_src_path.strip('/')):
                    shutil.copy(img_local_src_path, img_dst_path)
                else:
                    with open(img_dst_path, 'wb') as f:
                        f.write(get(f'https://blog.lucien.ink/{img_src_path}').content)
                for prefix in ['www.', 'blog.', '']:
                    content = content.replace(f'https://{prefix}lucien.ink{img_src_path}', img_dst_path)

        with open(os.path.join(post_dir, filename + '.md'), 'w') as f:
            f.write(content)


if __name__ == '__main__':
    main()
