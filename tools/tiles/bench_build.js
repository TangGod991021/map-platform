#!/usr/bin/env node
/**
 * W1 基准：在 Node 侧测量 5K 建筑合并几何体的构建耗时与体积。
 * 用法：node tools/tiles/bench_build.js
 */

const { createScopedThreejs } = require('../../utils/threejs-miniprogram.js');
const { buildBoxes } = require('../../pages/map25d/engine/geometry.js');
const tile = require('../../pages/map25d/data/tile_synthetic_5k.js');

const THREE = createScopedThreejs({});

const t0 = Date.now();
const { mesh, line } = buildBoxes(
  THREE,
  tile.buildings,
  0x0b2545,
  0x0a1a33,
  0x00e5ff,
  0.22
);
const buildMs = Date.now() - t0;

const meshBytes =
  mesh.geometry.attributes.position.array.length * 4 +
  (mesh.geometry.attributes.normal ? mesh.geometry.attributes.normal.array.length * 4 : 0) +
  line.geometry.attributes.position.array.length * 4;

console.log(JSON.stringify({
  dataset: tile.meta.name,
  buildings: tile.buildings.length,
  buildMs,
  meshVertices: mesh.geometry.attributes.position.count,
  triangles: mesh.geometry.attributes.position.count / 3,
  edgeVertices: line.geometry.attributes.position.count,
  edgeSegments: line.geometry.attributes.position.count / 2,
  geometryMB: Number((meshBytes / 1048576).toFixed(2))
}, null, 2));
