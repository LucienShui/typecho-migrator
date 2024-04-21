IMG_PATH="/root/lucienshui.github.io/assets/img/posts"

ssh blog 'rm -rf /root/lucienshui.github.io/_posts/*'
scp -r _posts/* blog:/root/lucienshui.github.io/_posts/
ssh blog "rm -rf ${IMG_PATH} && mkdir -p ${IMG_PATH}"
scp -r assets/img/posts/* "blog:${IMG_PATH}/"
ssh blog 'cd /root/lucienshui.github.io && bash build.sh'
echo 'http://10.0.1.205:3000'
