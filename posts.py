import pymysql.cursors
import os
import pandas as pd
from datetime import datetime
from pypinyin import lazy_pinyin
import re

OUTPUT_DIR = '_posts'


def main():
    non_alpha_pattern = re.compile(r'[^a-zA-Z0-9]')
    continuous_under_line = re.compile(r'_+')

    # 连接到数据库
    connection = pymysql.connect(host=os.environ['HOST'],
                                 user=os.environ['USER'],
                                 port=int(os.getenv('PORT', 3306)),
                                 password=os.environ['PASS'],
                                 database=os.environ['DB'],
                                 cursorclass=pymysql.cursors.DictCursor)

    with connection:
        with connection.cursor() as cursor:
            # 执行SQL查询
            with open('posts.sql') as f:
                sql = f.read()

            cursor.execute(sql)

            # 获取查询结果
            result = cursor.fetchall()
            df = pd.DataFrame(result)

        # 必要时此处可以提交事务
        # connection.commit()
    for col in ['created', 'modified']:
        df.loc[:, col] = df[col].map(lambda x: datetime.fromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'))

    df.loc[:, 'filename'] = df.apply(
        lambda row: row['created'][:10] + '-' + continuous_under_line.sub('_', non_alpha_pattern.sub(
            '_', '_'.join(lazy_pinyin(row['title'].replace(' ', ''))).lower())) + '.md',
        axis=1
    )

    for filename, title, date, categories, tags, content in df[
        ['filename', 'title', 'created', 'category_list', 'tag_list', 'text']
    ].iloc:
        y, m, d = date[:4], date[5:7], date[8:10]
        dirname = os.path.join(OUTPUT_DIR, y, m, d)
        os.system(f'mkdir -p {dirname}')
        with open(os.path.join(dirname, filename), 'w') as f:
            content = (f"""---
title: "{title}"
date: {date} +0800
categories: [{', '.join(categories.split(','))}]
tags: [{', '.join(tags.split(',')) if tags else ''}]
math: {str('$' in content).lower()}
render_with_liquid: false
---
""" + content).replace('\r\n', '\n').replace('\n#', '\n##')
            f.write(content)


if __name__ == '__main__':
    main()
