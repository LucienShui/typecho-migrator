BASE_DIR="/root/blog"
IMG_PATH="${BASE_DIR}/assets/img/posts"

ssh blog "rm -rf ${BASE_DIR}/_posts/*"
scp -r _posts/* blog:${BASE_DIR}/_posts/
ssh blog "rm -rf ${IMG_PATH} && mkdir -p ${IMG_PATH}"
scp -r assets/img/posts/* "blog:${IMG_PATH}/"
