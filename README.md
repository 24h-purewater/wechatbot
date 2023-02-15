# wechatbot

werobot doc: https://werobot.readthedocs.io/zh_CN/latest/

wechat offiaccount doc: https://developers.weixin.qq.com/doc/offiaccount/Getting_Started/Overview.html


config file:


```
wx_token: 
port: 
log_level: info
log_file: server.log
openai_endpoint: 
validation_sign: 
app_id: 
app_secret: 
multithreading: on
wx_send_msg_buffer_period: 2

slack_webhook: 
wx_welcome_msg: 

maintenance_status: 
maintenance_msg: 
developer_open_id: 
open_ai_max_tokens: 1000
open_ai_fallback: true


```

test env
```
docker-compose  --env-file .env.test  -f docker-compose-test.yml up -d
```


prod env
```
docker-compose  up -d
```
