# 数据工具

## check_areacity.py

核对 `apps/map-web/data/guizhou-*.json` 与 AreaCity 免费行政区划数据：

```bash
python tools/data/check_areacity.py
```

- 默认从 jsDelivr 拉取 AreaCity master 的 `ok_data_level3.csv` / `ok_data_level4.csv`；
- 也可用 `--level3` / `--level4` 指定本地 CSV；
- 只读比对，不修改任何数据文件；
- 乡镇级坐标/边界为 AreaCity 付费数据，脚本只统计免费名称数据的覆盖情况。

数据说明见 [docs/数据校验-贵州行政区划.md](../../docs/数据校验-贵州行政区划.md)。
