const { mapBaseUrl } = require('../../config.js');
const MAP_BASE_URL = mapBaseUrl;

Page({
  data: {
    mapUrl: ''
  },

  onLoad(options) {
    const opts = options || {};
    const lng = opts.lng || '106.6302';
    const lat = opts.lat || '26.6470';
    const zoom = opts.zoom || '13';

    this.setData({
      mapUrl:
        MAP_BASE_URL +
        '?lng=' + encodeURIComponent(lng) +
        '&lat=' + encodeURIComponent(lat) +
        '&zoom=' + encodeURIComponent(zoom)
    });
  },

  onMapMessage(e) {
    const data = e && e.detail && e.detail.data;
    console.log('[tianditu] web-view message', data);
  },

  onMapError(e) {
    console.error('[tianditu] web-view error', e && e.detail);
    wx.showToast({
      title: '地图加载失败，请检查网络或域名配置',
      icon: 'none'
    });
  },

  onShareAppMessage() {
    return {
      title: '黔山漫游 · 天地图',
      path: '/pages/map/index'
    };
  }
});
