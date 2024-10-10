# AutoWeb3

## 安装
1. 自行下载metamask插件压缩包,放置到./extension路径下, 命名为 metamask
2. 安装依赖
```shell
pip install -r requirements.txt
playwright install
```

## 使用
### play_metamask
使用playwright控制浏览器, 并安装metamask插件, 导入助记词
- 只适用于全新的用户(首次安装meta_mask插件), 否则打开浏览器时不会弹出meta_mask的欢迎页(除非已知插件的id)
