WITH
post_table AS (
    SELECT cid,
           title,
           created,
           modified,
           commentsNum AS comments_num,
           REPLACE(text, '<!--markdown-->', '') AS text,
           views
    FROM typecho_contents
    WHERE `type` = 'post'
),
cid_to_attachment AS (
    SELECT parent AS cid, CONCAT_WS('##', CONCAT(text, '@@', `order`)) AS attachment_list
    FROM typecho_contents
    WHERE `type` = 'attachment'
    GROUP BY parent
),
cid_to_summary AS (
    SELECT cid, str_value AS summary
    FROM typecho_fields
    WHERE `name` = 'customSummary'
),
cid_mid_relation_table AS (
    SELECT cid, mid
    FROM typecho_relationships
),
tag_table AS (
    SELECT *, `name` AS display_name
    FROM typecho_metas
    WHERE `type` = 'tag'
),
cid_to_tag_table AS (
    SELECT cid,
           tag_table.display_name
    FROM cid_mid_relation_table
    INNER JOIN tag_table
    ON cid_mid_relation_table.mid = tag_table.mid
),
cid_to_tag_list_table AS (
    SELECT cid, CONCAT_WS(',', display_name) AS tag_list
    FROM cid_to_tag_table
    GROUP BY cid
),
category_table AS (
    SELECT *, `name` AS display_name
    FROM typecho_metas
    WHERE `type` = 'category'
),
category_lv1 AS (
    SELECT mid, display_name, category_table.count, 1 AS lv
    FROM category_table
    WHERE parent = 0
),
category_lv2 AS (
    SELECT category_table.mid,
           CONCAT(category_parent.display_name, ',', category_table.display_name) AS display_name,
           category_table.count,
           2 AS lv
    FROM category_lv1 AS category_parent
    INNER JOIN category_table AS category_table
    ON category_parent.mid = category_table.parent
    WHERE category_table.display_name != 'solution'
),
category_union AS (
    SELECT *
    FROM category_lv1
    UNION
    SELECT *
    FROM category_lv2
),
cid_to_category AS (
    SELECT cid_mid_relation_table.cid,
           category_table.*,
           ROW_NUMBER() OVER (
               PARTITION BY cid
               ORDER BY `lv` DESC, `count` ASC
           ) AS row_id
    FROM cid_mid_relation_table
    LEFT OUTER JOIN category_union AS category_table
    ON cid_mid_relation_table.mid = category_table.mid
    WHERE category_table.mid IS NOT NULL
),
duplicate_cid AS (
    SELECT cid, COUNT(1) AS cnt, COUNT(DISTINCT mid) AS unique_cnt
    FROM cid_to_category
    GROUP BY cid
    HAVING COUNT(1) > 1
),
duplicate_record AS (
    SELECT cid_to_category.*
    FROM cid_to_category
    INNER JOIN duplicate_cid
    ON cid_to_category.cid = duplicate_cid.cid
),
unique_cid_to_category AS (
    SELECT *
    FROM cid_to_category
    WHERE row_id = 1
)
SELECT post_table.*,
       unique_cid_to_category.display_name AS category_list,
       cid_to_tag_list_table.tag_list,
       cid_to_summary.summary,
       cid_to_attachment.attachment_list
FROM post_table
LEFT OUTER JOIN unique_cid_to_category
ON post_table.cid = unique_cid_to_category.cid
LEFT OUTER JOIN cid_to_tag_list_table
ON post_table.cid = cid_to_tag_list_table.cid
LEFT OUTER JOIN cid_to_summary
ON post_table.cid = cid_to_summary.cid
LEFT OUTER JOIN cid_to_attachment
ON post_table.cid = cid_to_attachment.cid
;
