# simple_proxy
一个简单代理，在本地listen， 可以切换出口代理直连，根据后缀ip正则表达式使用不同的代理设置，类似于switchy omega， 通过简单的html/js进行配置
配置界面类似switchy omega插件，需要使用html和js，通过web方式进行配置，配置包括规则和出口设置，出口设置有直接，代理， 服务器可以切换直接，代理，自动方式。




simple_proxy/
├── requirements.txt
├── setup.py
├── simple_proxy/
│   ├── __init__.py
│   ├── config.py
│   ├── proxy_server.py
│   ├── rule_engine.py
│   ├── web_interface.py
│   └── static/
│       ├── index.html
│       ├── css/
│       │   └── style.css
│       └── js/
│           └── main.js
└── tests/
    ├── __init__.py
    ├── test_proxy_server.py
    ├── test_rule_engine.py
    └── test_config.py

