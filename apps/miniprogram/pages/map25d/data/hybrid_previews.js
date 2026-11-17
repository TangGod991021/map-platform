// 自动生成：tools/tiles/build_core_hybrid.py，请勿手工修改
module.exports = {
  list: [
    { key: "jiaxiu", name: "甲秀楼", lat: 26.5686, lon: 106.7167 },
    { key: "penshuichi", name: "喷水池", lat: 26.647, lon: 106.6302 },
    { key: "dashizi", name: "大十字", lat: 26.643, lon: 106.634 },
    { key: "huaguoyuan", name: "花果园", lat: 26.573, lon: 106.686 },
    { key: "hebin", name: "河滨公园", lat: 26.565, lon: 106.712 },
    { key: "guiyangzhan", name: "贵阳站", lat: 26.568, lon: 106.705 }
  ],
  loaders: {
    jiaxiu: () => require("./hybrid/tile_9_-9.js"),
    penshuichi: () => require("./hybrid/tile_-8_8.js"),
    dashizi: () => require("./hybrid/tile_-7_7.js"),
    huaguoyuan: () => require("./hybrid/tile_3_-8.js"),
    hebin: () => require("./hybrid/tile_8_-10.js"),
    guiyangzhan: () => require("./hybrid/tile_7_-9.js")
  }
};
