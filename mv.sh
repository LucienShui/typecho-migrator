ssh blog 'yes | rm -rf /root/lucienshui.github.io/_posts/*'
scp -r _posts/* blog:/root/lucienshui.github.io/_posts/
ssh blog 'cd /root/lucienshui.github.io && bash build.sh'
echo 'http://10.0.1.205:3000'
