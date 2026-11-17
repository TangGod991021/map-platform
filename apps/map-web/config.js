// 天地图「浏览器端」Key（应用类型选择：浏览器端）
// 在服务器上编辑 /var/www/tianmap/config.js，替换下面的值后刷新页面。
window.TIANDITU_TK = 'YOUR_TIANDITU_TK';

window.MAP_CONFIG = {
  center: { lng: 106.6302, lat: 26.6470 },
  zoom: 13,
  // false：只显示卫星影像，移除天地图官方注记（含地铁线、道路、地名等）
  // true：叠加 cia_w 影像注记
  showTiandituLabels: false,
  // 点位/路线/区域默认关闭；后续由后端/后台动态下发时再打开
  showPois: true,
  showRoutes: true,
  showAreas: true,
  // 静态快照由后台发布生成；开发也可指向 http://127.0.0.1:8000/map-api/v1/bootstrap
  poisApi: './data/map.json',
  // 修改 pois.json 后递增该版本号，避免浏览器缓存
  dataVersion: '1'
};
