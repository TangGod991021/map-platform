/**
 * 2.5D 几何构建工具（W1 从页面抽出，便于 Node 侧基准测试与 W3 TileBuilder 复用）。
 * 注意：threejs-miniprogram 基于 r108，必须使用 *BufferGeometry。
 */

function setAttribute(THREE, geo, name, attr) {
  if (geo.setAttribute) geo.setAttribute(name, attr);
  else geo.addAttribute(name, attr);
}

/**
 * 把多个带变换的索引几何体合并为一个非索引 BufferGeometry。
 * 用于合并 POI 光柱/核心球等静态部件，减少 draw call。
 */
function mergeTransformedGeometries(THREE, entries) {
  const positions = [];
  const normals = [];

  entries.forEach((entry) => {
    const g = entry.geometry.clone();
    if (entry.matrix && g.applyMatrix4) g.applyMatrix4(entry.matrix);

    const posAttr = g.attributes && g.attributes.position;
    const norAttr = g.attributes && g.attributes.normal;
    if (!posAttr) {
      g.dispose();
      return;
    }

    const pos = posAttr.array;
    const nor = norAttr ? norAttr.array : null;
    const index = g.index && g.index.array;

    if (index) {
      for (let i = 0; i < index.length; i++) {
        const j = index[i] * 3;
        positions.push(pos[j], pos[j + 1], pos[j + 2]);
        if (nor) normals.push(nor[j], nor[j + 1], nor[j + 2]);
      }
    } else {
      for (let i = 0; i < pos.length; i++) positions.push(pos[i]);
      if (nor) {
        for (let i = 0; i < nor.length; i++) normals.push(nor[i]);
      }
    }
    g.dispose();
  });

  const geo = new THREE.BufferGeometry();
  setAttribute(THREE, geo, 'position', new THREE.Float32BufferAttribute(positions, 3));
  if (normals.length) {
    setAttribute(THREE, geo, 'normal', new THREE.Float32BufferAttribute(normals, 3));
  }
  return geo;
}

/**
 * 把建筑盒体列表合并为一个 Mesh + 一套边线。
 * @param {object} THREE scoped three
 * @param {Array} list [{x,z,w,d,h,y?,k?}]
 */
function buildBoxes(THREE, list, color, emissive, edgeColor, edgeOpacity) {
  const positions = [];
  const normals = [];
  const edgePositions = [];

  list.forEach((b) => {
    const y = b.y || 0;
    // three r108 中 BoxGeometry 是旧版 Geometry（没有 attributes），必须用 BoxBufferGeometry
    const geo = new THREE.BoxBufferGeometry(b.w, b.h, b.d);
    geo.translate(b.x, y + b.h / 2, b.z);

    const posAttr = geo.attributes && geo.attributes.position;
    const norAttr = geo.attributes && geo.attributes.normal;
    if (!posAttr || !norAttr) {
      console.warn('[2.5D] skip invalid building', b);
      geo.dispose();
      return;
    }
    const pos = posAttr.array;
    const nor = norAttr.array;
    const index = geo.index && geo.index.array;
    if (index) {
      // BoxBufferGeometry 是索引几何体：必须按索引展开，否则会漏掉部分三角面
      for (let i = 0; i < index.length; i++) {
        const j = index[i] * 3;
        positions.push(pos[j], pos[j + 1], pos[j + 2]);
        normals.push(nor[j], nor[j + 1], nor[j + 2]);
      }
    } else {
      for (let i = 0; i < pos.length; i++) positions.push(pos[i]);
      for (let i = 0; i < nor.length; i++) normals.push(nor[i]);
    }
    geo.dispose();

    const x1 = b.x - b.w / 2;
    const x2 = b.x + b.w / 2;
    const y1 = y;
    const y2 = y + b.h;
    const z1 = b.z - b.d / 2;
    const z2 = b.z + b.d / 2;
    const c = [
      [x1, y1, z1], [x2, y1, z1], [x2, y1, z2], [x1, y1, z2],
      [x1, y2, z1], [x2, y2, z1], [x2, y2, z2], [x1, y2, z2]
    ];
    const edges = [
      [0, 1], [1, 2], [2, 3], [3, 0],
      [4, 5], [5, 6], [6, 7], [7, 4],
      [0, 4], [1, 5], [2, 6], [3, 7]
    ];
    edges.forEach(([a, b2]) => {
      edgePositions.push(
        c[a][0], c[a][1], c[a][2],
        c[b2][0], c[b2][1], c[b2][2]
      );
    });
  });

  const geo = new THREE.BufferGeometry();
  setAttribute(THREE, geo, 'position', new THREE.Float32BufferAttribute(positions, 3));
  setAttribute(THREE, geo, 'normal', new THREE.Float32BufferAttribute(normals, 3));
  const mesh = new THREE.Mesh(
    geo,
    new THREE.MeshStandardMaterial({
      color,
      emissive,
      emissiveIntensity: 0.7,
      metalness: 0.35,
      roughness: 0.5,
      transparent: true,
      opacity: 0.96
    })
  );

  const edgeGeo = new THREE.BufferGeometry();
  setAttribute(THREE, edgeGeo, 'position', new THREE.Float32BufferAttribute(edgePositions, 3));
  const line = new THREE.LineSegments(
    edgeGeo,
    new THREE.LineBasicMaterial({
      color: edgeColor,
      transparent: true,
      opacity: edgeOpacity
    })
  );

  return { mesh, line };
}

module.exports = {
  setAttribute,
  mergeTransformedGeometries,
  buildBoxes
};
