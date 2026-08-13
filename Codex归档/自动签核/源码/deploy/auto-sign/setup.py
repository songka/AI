# -*- coding: utf-8 -*-
"""一键设置脚本：获取并填充 bot_open_id 到 feishu.json。"""
import json, sys
sys.path.insert(0, '/www/wwwroot/lfaf.eu.org/qh/auto-sign')
from feishu import _get_tenant_token
import requests

FEISHU_JSON = '/www/wwwroot/lfaf.eu.org/qh/feishu.json'

with open(FEISHU_JSON) as f:
    cfg = json.load(f)
t = _get_tenant_token(cfg['app_id'], cfg['app_secret'])
r = requests.get('https://open.feishu.cn/open-apis/bot/v3/info',
                 headers={'Authorization': 'Bearer ' + t}, timeout=10)
data = r.json()
if data.get('code') == 0:
    bot_id = data['bot']['open_id']
    cfg['bot_open_id'] = bot_id
    with open(FEISHU_JSON, 'w') as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print(f'bot_open_id 已更新: {bot_id}')
else:
    print(f'失败: {data}')
