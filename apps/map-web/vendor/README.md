# 第三方浏览器构建

## supercluster.min.js

- 版本：9.1.0
- 来源：<https://unpkg.com/supercluster@9.1.0/dist/supercluster.min.js>
- 许可证：ISC
- 全局变量：`window.Supercluster`（UMD）

地图 H5 为纯静态站点，不引入打包器，因此直接使用官方 UMD 构建。
升级时替换本文件并同步 `index.html` 顶部注释中的版本号。

## 为什么不用 vue-tianditu

`vue-tianditu` 最后发布于 2022-05，已明显过旧；后台地图组件改用
Leaflet 1.9.4 + @geoman-io/leaflet-geoman-free 2.20.6（见 admin-web 依赖）。
