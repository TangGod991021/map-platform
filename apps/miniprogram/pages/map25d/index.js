const { createScopedThreejs } = require('../../utils/threejs-miniprogram.js');
const {
  buildBoxes,
  mergeTransformedGeometries,
  setAttribute
} = require('./engine/geometry.js');
const HYBRID_PREVIEWS = require('./data/hybrid_previews.js');
let area = require('./data/area25d.js');

// 数据集切换：compile mode 通过 ?tile=demo|osm|synthetic|hybrid 选择
// hybrid 额外支持 ?area=jiaxiu|penshuichi|...
const DATASETS = {
  demo: () => require('./data/area25d.js'),
  osm: () => require('./data/tile_osm_jiaxiu.js'),
  synthetic: () => require('./data/tile_synthetic_5k.js'),
  hybrid: () => HYBRID_PREVIEWS.loaders.jiaxiu()
};

const TYPE_LABEL = {
  landmark: '地标',
  river: '水系',
  district: '街区'
};

const TYPE_COLOR = {
  landmark: '#00e5ff',
  river: '#38bdf8',
  district: '#8b5cf6'
};

const DEFAULT_CAMERA = {
  azimuth: 0.78,
  polar: 0.95,
  radius: 2400,
  zoom: 1
};

Page({
  data: {
    loading: true,
    error: '',
    selected: null,
    activeFilter: 'all',
    filters: [
      { key: 'all', label: '全部', color: '#00e5ff' },
      { key: 'landmark', label: '地标', color: '#00e5ff' },
      { key: 'river', label: '水系', color: '#38bdf8' },
      { key: 'district', label: '街区', color: '#8b5cf6' }
    ],
    clock: '',
    poiCount: area.pois.length,
    meta: area.meta,
    areaName: area.meta.name,
    previewAreas: HYBRID_PREVIEWS.list,
    activeAreaKey: '',
    // 自定义导航布局：状态栏高度、右侧胶囊避让宽度
    statusBarHeight: 20,
    capsuleRight: 88,
    compassDeg: 45,
    zoomPct: 100,
    hintVisible: true,
    // W1 性能基线
    debug: false,
    dataKey: 'demo',
    fps: 0,
    drawCalls: 0,
    triangles: 0,
    geometries: 0,
    textures: 0,
    buildMs: 0
  },

  onLoad(options) {
    const opts = options || {};
    const key = opts.tile;
    // 默认进入混合方案核心区；?tile=demo|osm|synthetic 仍可用于调试
    this._dataKey = DATASETS[key] ? key : 'hybrid';

    if (this._dataKey === 'hybrid') {
      const areaKey =
        opts.area && HYBRID_PREVIEWS.loaders[opts.area] ? opts.area : 'jiaxiu';
      this._areaKey = areaKey;
      area = HYBRID_PREVIEWS.loaders[areaKey]();
    } else {
      this._areaKey = null;
      area = DATASETS[this._dataKey]();
    }

    const areaInfo = this._areaKey
      ? HYBRID_PREVIEWS.list.find((item) => item.key === this._areaKey)
      : null;

    this.setData({
      debug: opts.debug === '1',
      dataKey: this._dataKey,
      areaName: areaInfo ? areaInfo.name : area.meta.name,
      activeAreaKey: this._areaKey || '',
      poiCount: area.pois.length,
      meta: area.meta
    });

    this.initMetrics();
  },

  onReady() {
    this.updateClock();
    this._clockTimer = setInterval(() => this.updateClock(), 1000);
    this._hintTimer = setTimeout(() => {
      this.setData({ hintVisible: false });
    }, 4800);
    this.initCanvas();
  },

  onUnload() {
    this.dispose();
  },

  initMetrics() {
    let sys = {};
    try {
      sys = wx.getSystemInfoSync();
    } catch (e) {
      sys = {};
    }

    const statusBarHeight = sys.statusBarHeight || 20;
    let capsuleRight = 88;

    try {
      if (wx.getMenuButtonBoundingClientRect) {
        const menu = wx.getMenuButtonBoundingClientRect();
        if (menu && menu.left) {
          capsuleRight = Math.max(88, (sys.windowWidth || 375) - menu.left + 8);
        }
      }
    } catch (e) {
      capsuleRight = 88;
    }

    this.setData({
      statusBarHeight,
      capsuleRight
    });
  },

  updateClock() {
    const d = new Date();
    const pad = (n) => String(n).padStart(2, '0');
    this.setData({
      clock: `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
    });
  },

  initCanvas() {
    wx.createSelectorQuery()
      .select('#webgl')
      .node()
      .exec((res) => {
        const canvas = res && res[0] && res[0].node;
        if (!canvas) {
          this.setData({
            loading: false,
            error: '当前基础库不支持 WebGL Canvas，请升级微信或基础库后重试。'
          });
          return;
        }
        this._canvas = canvas;

        wx.createSelectorQuery()
          .select('.stage')
          .boundingClientRect()
          .exec((rectRes) => {
            const rect = rectRes && rectRes[0];
            if (!rect || !rect.width || !rect.height) {
              this.setData({ loading: false, error: '无法获取画布尺寸。' });
              return;
            }
            this._rect = rect;
            try {
              this.initScene(canvas, rect);
            } catch (e) {
              console.error('[2.5D] initScene error', e);
              this.setData({
                loading: false,
                error: '3D 场景初始化失败：' + (e && e.message ? e.message : String(e))
              });
            }
          });
      });
  },

  initScene(canvas, rect) {
    const THREE = createScopedThreejs(canvas);
    this.THREE = THREE;

    const dpr = Math.min((wx.getSystemInfoSync().pixelRatio || 1), 2);
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;

    const renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: false
    });
    renderer.setPixelRatio(dpr);
    renderer.setSize(rect.width, rect.height, false);
    renderer.setClearColor(0x050914, 1);
    this.renderer = renderer;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x050914);
    scene.fog = new THREE.Fog(0x050914, 1500, 3800);
    this.scene = scene;

    const aspect = rect.width / rect.height;
    const frustum = 820;
    const camera = new THREE.OrthographicCamera(
      -frustum * aspect,
      frustum * aspect,
      frustum,
      -frustum,
      1,
      6000
    );
    this.camera = camera;
    this.target = new THREE.Vector3(0, 0, 0);
    this.azimuth = DEFAULT_CAMERA.azimuth;
    this.polar = DEFAULT_CAMERA.polar;
    this._baseRadius = DEFAULT_CAMERA.radius;

    // 按数据集范围自动取景：演示 1.4km / 合成 2km / OSM 500m
    const span = Math.max(
      (area.meta && area.meta.area && area.meta.area.width) || 1400,
      (area.meta && area.meta.area && area.meta.area.depth) || 1100
    );
    this._fitZoom = clamp(1400 / span, 0.6, 1.35);

    // 入场时从更远处缓推近，形成“接入城市”的镜头感
    this.radius = DEFAULT_CAMERA.radius * 1.45;
    this.camera.zoom = this._fitZoom * 0.86;
    this.camera.updateProjectionMatrix();
    this.updateCamera();

    const buildStart = Date.now();
    this.addLights();
    this.addGround();
    this.addWater();
    this.addRoads();
    this.addBuildings();
    this.addPoiMarkers();
    this._buildMs = Date.now() - buildStart;

    const raf = canvas.requestAnimationFrame
      ? canvas.requestAnimationFrame.bind(canvas)
      : (fn) => setTimeout(fn, 16);
    this._raf = raf;
    this._disposed = false;
    this._frameCount = 0;
    this._perfLast = Date.now();

    this._intro = {
      start: Date.now(),
      dur: 1100,
      from: this.radius,
      to: DEFAULT_CAMERA.radius,
      toZoom: this._fitZoom
    };

    const loop = () => {
      if (this._disposed) return;
      this.animate();
      this._rafId = raf(loop);
    };
    this._rafId = raf(loop);

    this.setData({ loading: false, error: '', buildMs: this._buildMs });
    this.syncHud();
  },

  addLights() {
    const THREE = this.THREE;
    const scene = this.scene;

    scene.add(new THREE.AmbientLight(0x88aaff, 0.75));

    const key = new THREE.DirectionalLight(0x00e5ff, 1.2);
    key.position.set(600, 1200, 400);
    scene.add(key);

    const fill = new THREE.DirectionalLight(0x8b5cf6, 0.7);
    fill.position.set(-500, 700, -600);
    scene.add(fill);

    scene.add(new THREE.HemisphereLight(0x00e5ff, 0x02040a, 0.4));
  },

  addGround() {
    const THREE = this.THREE;
    const scene = this.scene;

    const ground = new THREE.Mesh(
      new THREE.PlaneBufferGeometry(5000, 5000),
      new THREE.MeshBasicMaterial({ color: 0x050914 })
    );
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -1;
    scene.add(ground);

    const grid = new THREE.GridHelper(5000, 100, 0x00e5ff, 0x0a1a33);
    grid.position.y = 0;
    if (grid.material) {
      grid.material.transparent = true;
      grid.material.opacity = 0.16;
    }
    scene.add(grid);
  },

  addWater() {
    const THREE = this.THREE;
    const scene = this.scene;

    area.water.forEach((w) => {
      const pts = w.p;
      if (!pts || pts.length < 3) return;

      const shape = new THREE.Shape();
      shape.moveTo(pts[0][0], -pts[0][1]);
      for (let i = 1; i < pts.length; i++) {
        shape.lineTo(pts[i][0], -pts[i][1]);
      }
      const geo = new THREE.ShapeBufferGeometry(shape);
      const mesh = new THREE.Mesh(
        geo,
        new THREE.MeshBasicMaterial({
          color: 0x0a2a5e,
          transparent: true,
          opacity: 0.9,
          side: THREE.DoubleSide
        })
      );
      mesh.rotation.x = -Math.PI / 2;
      mesh.position.y = 0.05;
      scene.add(mesh);

      const worldPts = pts.map((p) => new THREE.Vector3(p[0], 0.12, p[1]));
      const lineGeo = new THREE.BufferGeometry().setFromPoints(worldPts);
      scene.add(
        new THREE.LineLoop(
          lineGeo,
          new THREE.LineBasicMaterial({
            color: 0x00e5ff,
            transparent: true,
            opacity: 0.55
          })
        )
      );
    });
  },

  addRoads() {
    const THREE = this.THREE;
    const scene = this.scene;

    const groups = { primary: [], secondary: [], river: [] };
    area.roads.forEach((r) => {
      const pts = r.p || [];
      const key = groups[r.t] ? r.t : 'secondary';
      for (let i = 0; i < pts.length - 1; i++) {
        const a = pts[i];
        const b = pts[i + 1];
        groups[key].push(a[0], 0.14, a[1], b[0], 0.14, b[1]);
      }
    });

    const style = {
      primary: { color: 0x00e5ff, opacity: 0.65 },
      secondary: { color: 0x1e6fb8, opacity: 0.35 },
      river: { color: 0x38bdf8, opacity: 0.45 }
    };

    Object.keys(groups).forEach((key) => {
      const arr = groups[key];
      if (!arr.length) return;
      const geo = new THREE.BufferGeometry();
      setAttribute(THREE, geo, 'position', new THREE.Float32BufferAttribute(arr, 3));
      scene.add(
        new THREE.LineSegments(
          geo,
          new THREE.LineBasicMaterial({
            color: style[key].color,
            transparent: true,
            opacity: style[key].opacity
          })
        )
      );
    });
  },

  addBuildings() {
    const THREE = this.THREE;
    const scene = this.scene;

    const blocks = area.buildings.filter((b) => b.k === 'block');
    const landmarks = area.buildings.filter((b) => b.k !== 'block');

    const block = buildBoxes(THREE, blocks, 0x0b2545, 0x0a1a33, 0x00e5ff, 0.22);
    scene.add(block.mesh);
    scene.add(block.line);

    const landmark = buildBoxes(THREE, landmarks, 0x123a5a, 0x00b8d4, 0x7dd3fc, 0.55);
    scene.add(landmark.mesh);
    scene.add(landmark.line);

    const tower = area.buildings.find((b) => b.k === 'tower');
    if (tower) {
      const beam = new THREE.Mesh(
        new THREE.CylinderBufferGeometry(2, 2, 140, 6),
        new THREE.MeshBasicMaterial({
          color: 0x00e5ff,
          transparent: true,
          opacity: 0.25,
          blending: THREE.AdditiveBlending,
          depthWrite: false
        })
      );
      beam.position.set(tower.x, 70, tower.z);
      scene.add(beam);
    }
  },

  addPoiMarkers() {
    const THREE = this.THREE;
    const scene = this.scene;

    this.poiGroups = {};
    this.poiStaticMeshes = {};
    // 屏幕空间拾取：不创建不可见的 hit mesh，减少 draw call
    this.poiVertices = [];

    const colorByType = {
      landmark: 0x00e5ff,
      river: 0x38bdf8,
      district: 0x8b5cf6
    };

    // 静态部分（光柱、核心球）按类型合并，减少 draw call
    const staticBeams = {};
    const staticCores = {};

    area.pois.forEach((poi) => {
      const color = colorByType[poi.type] || 0x00e5ff;
      const type = poi.type || 'landmark';

      const group = new THREE.Group();
      group.position.set(poi.x, 0, poi.z);
      group.userData = { poi };

      staticBeams[type] = staticBeams[type] || [];
      staticBeams[type].push({
        geometry: new THREE.CylinderBufferGeometry(1.4, 1.4, 96, 6),
        matrix: new THREE.Matrix4().makeTranslation(poi.x, 48, poi.z)
      });

      staticCores[type] = staticCores[type] || [];
      staticCores[type].push({
        geometry: new THREE.SphereBufferGeometry(6, 16, 16),
        matrix: new THREE.Matrix4().makeTranslation(poi.x, 96, poi.z)
      });

      const ring = new THREE.Mesh(
        new THREE.RingBufferGeometry(10, 14, 32),
        new THREE.MeshBasicMaterial({
          color,
          transparent: true,
          opacity: 0.7,
          side: THREE.DoubleSide,
          blending: THREE.AdditiveBlending,
          depthWrite: false
        })
      );
      ring.rotation.x = -Math.PI / 2;
      ring.position.y = 96;
      group.add(ring);

      const groundRing = new THREE.Mesh(
        new THREE.RingBufferGeometry(10, 16, 32),
        new THREE.MeshBasicMaterial({
          color,
          transparent: true,
          opacity: 0.45,
          side: THREE.DoubleSide,
          blending: THREE.AdditiveBlending,
          depthWrite: false
        })
      );
      groundRing.rotation.x = -Math.PI / 2;
      groundRing.position.y = 0.4;
      group.add(groundRing);

      const label = makeLabel(THREE, poi.name);
      if (label) {
        label.position.y = 128;
        group.add(label);
      }

      this.poiVertices.push({
        poi,
        pos: new THREE.Vector3(poi.x, 96, poi.z)
      });

      group.userData.ring = ring;
      group.userData.groundRing = groundRing;

      this.poiGroups[type] = this.poiGroups[type] || [];
      this.poiGroups[type].push(group);
      scene.add(group);
    });

    Object.keys(staticBeams).forEach((type) => {
      const color = colorByType[type] || 0x00e5ff;

      const beamGeo = mergeTransformedGeometries(THREE, staticBeams[type]);
      staticBeams[type].forEach((e) => e.geometry.dispose());
      const beamMesh = new THREE.Mesh(
        beamGeo,
        new THREE.MeshBasicMaterial({
          color,
          transparent: true,
          opacity: 0.38,
          blending: THREE.AdditiveBlending,
          depthWrite: false
        })
      );
      scene.add(beamMesh);

      const coreGeo = mergeTransformedGeometries(THREE, staticCores[type]);
      staticCores[type].forEach((e) => e.geometry.dispose());
      const coreMesh = new THREE.Mesh(
        coreGeo,
        new THREE.MeshBasicMaterial({ color })
      );
      scene.add(coreMesh);

      this.poiStaticMeshes[type] = [beamMesh, coreMesh];
    });
  },

  animate() {
    if (!this.renderer || !this.scene || !this.camera) return;

    const t = Date.now() / 1000;

    if (this._intro) {
      const p = Math.min(1, (Date.now() - this._intro.start) / this._intro.dur);
      const eased = 1 - Math.pow(1 - p, 3);
      const toZoom = this._intro.toZoom || DEFAULT_CAMERA.zoom;
      this.radius = this._intro.from + (this._intro.to - this._intro.from) * eased;
      this.camera.zoom = toZoom * (0.86 + 0.14 * eased);
      this.camera.updateProjectionMatrix();
      this.updateCamera();
      if (p >= 1) {
        this.radius = this._intro.to;
        this.camera.zoom = toZoom;
        this.camera.updateProjectionMatrix();
        this._intro = null;
        this.syncHud();
      }
    }

    if (this.poiGroups) {
      Object.keys(this.poiGroups).forEach((type) => {
        this.poiGroups[type].forEach((g, idx) => {
          const ring = g.userData.ring;
          const groundRing = g.userData.groundRing;
          if (ring) {
            const k = 1 + 0.25 * Math.sin(t * 2 + idx);
            ring.scale.set(k, k, k);
            ring.material.opacity = 0.45 + 0.25 * Math.sin(t * 2 + idx);
          }
          if (groundRing) {
            const phase = (t * 0.6 + idx * 0.3) % 1;
            const gk = 1 + 0.45 * phase;
            groundRing.scale.set(gk, gk, gk);
            groundRing.material.opacity = 0.45 * (1 - phase);
          }
        });
      });
    }
    this.renderer.render(this.scene, this.camera);

    if (this.data.debug) {
      this._frameCount++;
      const now = Date.now();
      const elapsed = now - this._perfLast;
      if (elapsed >= 500) {
        const info = this.renderer.info;
        this.setData({
          fps: Math.round((this._frameCount * 1000) / elapsed),
          drawCalls: info.render.calls,
          triangles: info.render.triangles,
          geometries: info.memory.geometries,
          textures: info.memory.textures
        });
        this._frameCount = 0;
        this._perfLast = now;
      }
    }
  },

  updateCamera() {
    const cam = this.camera;
    if (!cam) return;
    const r = this.radius;
    const sinP = Math.sin(this.polar);
    cam.position.set(
      this.target.x + r * sinP * Math.cos(this.azimuth),
      this.target.y + r * Math.cos(this.polar),
      this.target.z + r * sinP * Math.sin(this.azimuth)
    );
    cam.lookAt(this.target);
    cam.updateMatrixWorld();
  },

  syncHud() {
    if (!this.camera) return;
    const deg = ((this.azimuth * 180) / Math.PI + 360) % 360;
    this.setData({
      compassDeg: Math.round(deg),
      zoomPct: Math.round(this.camera.zoom * 100)
    });
  },

  onTouchStart(e) {
    const touches = e.touches || [];
    if (touches.length === 1) {
      this._touchStart = {
        x: touches[0].clientX,
        y: touches[0].clientY,
        t: Date.now()
      };
      this._lastTouch = {
        x: touches[0].clientX,
        y: touches[0].clientY
      };
      this._pinchDist = 0;
    } else if (touches.length === 2) {
      this._pinchDist = dist(touches[0], touches[1]);
      this._touchStart = null;
    }
  },

  onTouchMove(e) {
    const touches = e.touches || [];
    if (!this.camera) return;

    if (touches.length === 2) {
      const d = dist(touches[0], touches[1]);
      if (this._pinchDist > 0) {
        const ratio = d / this._pinchDist;
        this.camera.zoom = clamp(this.camera.zoom * ratio, 0.55, 3.2);
        this.camera.updateProjectionMatrix();
      }
      this._pinchDist = d;
      return;
    }

    if (touches.length === 1 && this._lastTouch) {
      const t = touches[0];
      const dx = t.clientX - this._lastTouch.x;
      const dy = t.clientY - this._lastTouch.y;
      this.panBy(dx, dy);
      this._lastTouch = { x: t.clientX, y: t.clientY };
    }
  },

  onTouchEnd(e) {
    const start = this._touchStart;
    const touches = e.changedTouches || [];
    if (!start || !touches.length) {
      this._touchStart = null;
      this._lastTouch = null;
      this.syncHud();
      return;
    }
    const t = touches[0];
    const moved = Math.hypot(t.clientX - start.x, t.clientY - start.y);
    const elapsed = Date.now() - start.t;
    this._touchStart = null;
    this._lastTouch = null;
    if (moved < 10 && elapsed < 350) {
      this.pickPoi(t.clientX, t.clientY);
    }
    this.syncHud();
  },

  panBy(dx, dy) {
    if (!this._rect || !this.camera) return;
    const THREE = this.THREE;
    const factor =
      ((this.camera.top - this.camera.bottom) / this._rect.height) /
      this.camera.zoom;

    const right = new THREE.Vector3().setFromMatrixColumn(this.camera.matrix, 0);
    const up = new THREE.Vector3().setFromMatrixColumn(this.camera.matrix, 1);
    right.y = 0;
    up.y = 0;
    if (right.lengthSq() > 0) right.normalize();
    if (up.lengthSq() > 0) up.normalize();

    this.target.addScaledVector(right, -dx * factor * 1.15);
    this.target.addScaledVector(up, dy * factor * 1.15);
    this.updateCamera();
  },

  pickPoi(clientX, clientY) {
    if (!this._rect || !this.poiVertices || !this.poiVertices.length) return;

    const rect = this._rect;
    const cx = clientX - rect.left;
    const cy = clientY - rect.top;
    const filter = this.data.activeFilter;
    const hitRadius = 44; // CSS px

    let best = null;
    let bestDist = hitRadius;

    this.poiVertices.forEach((entry) => {
      const poi = entry.poi;
      if (filter !== 'all' && poi.type !== filter) return;

      const ndc = entry.pos.clone().project(this.camera);
      const sx = (ndc.x * 0.5 + 0.5) * rect.width;
      const sy = (-ndc.y * 0.5 + 0.5) * rect.height;
      const d = Math.hypot(sx - cx, sy - cy);
      if (d < bestDist) {
        bestDist = d;
        best = poi;
      }
    });

    if (best) this.selectPoi(best);
  },

  selectPoi(poi) {
    this.setData({
      selected: Object.assign({}, poi, {
        typeLabel: TYPE_LABEL[poi.type] || '点位',
        typeColor: TYPE_COLOR[poi.type] || '#00e5ff',
        coord: `X ${poi.x} · Z ${poi.z}`
      })
    });
    this.target.set(poi.x, 0, poi.z);
    if (this.camera) {
      this.camera.zoom = Math.max(this.camera.zoom, 1.25);
      this.camera.updateProjectionMatrix();
    }
    this.updateCamera();
    this.syncHud();
  },

  onFilter(e) {
    const key = e.currentTarget.dataset.key;
    this.setData({ activeFilter: key });
    Object.keys(this.poiGroups || {}).forEach((type) => {
      const visible = key === 'all' || key === type;
      this.poiGroups[type].forEach((g) => {
        g.visible = visible;
      });
      (this.poiStaticMeshes[type] || []).forEach((m) => {
        m.visible = visible;
      });
    });
  },

  launchArea(key) {
    if (!key) return;
    const debug = this.data.debug ? '&debug=1' : '';
    wx.reLaunch({
      url: `/pages/map25d/index?tile=hybrid&area=${key}${debug}`
    });
  },

  onSwitchArea() {
    const list = HYBRID_PREVIEWS.list || [];
    if (!list.length) return;

    wx.showActionSheet({
      itemList: list.map((item) => item.name),
      success: (res) => {
        const item = list[res.tapIndex];
        if (item) this.launchArea(item.key);
      }
    });
  },

  onSelectArea(e) {
    const key = e.currentTarget.dataset.key;
    if (key && key !== this._areaKey) this.launchArea(key);
  },

  onZoomIn() {
    if (!this.camera) return;
    this.camera.zoom = clamp(this.camera.zoom * 1.18, 0.55, 3.2);
    this.camera.updateProjectionMatrix();
    this.syncHud();
  },

  onZoomOut() {
    if (!this.camera) return;
    this.camera.zoom = clamp(this.camera.zoom / 1.18, 0.55, 3.2);
    this.camera.updateProjectionMatrix();
    this.syncHud();
  },

  onRotateLeft() {
    if (!this.camera) return;
    this.azimuth -= 0.18;
    this.updateCamera();
    this.syncHud();
  },

  onRotateRight() {
    if (!this.camera) return;
    this.azimuth += 0.18;
    this.updateCamera();
    this.syncHud();
  },

  onCompassTap() {
    if (!this.camera) return;
    this.azimuth = DEFAULT_CAMERA.azimuth;
    this.updateCamera();
    this.syncHud();
    haptic();
  },

  onReset() {
    if (!this.camera) return;
    this.target.set(0, 0, 0);
    this.azimuth = DEFAULT_CAMERA.azimuth;
    this.polar = DEFAULT_CAMERA.polar;
    this.radius = this._baseRadius || DEFAULT_CAMERA.radius;
    this._intro = null;
    this.camera.zoom = this._fitZoom || DEFAULT_CAMERA.zoom;
    this.camera.updateProjectionMatrix();
    this.updateCamera();
    this.syncHud();
    this.setData({ selected: null, activeFilter: 'all' });
    Object.keys(this.poiGroups || {}).forEach((type) => {
      this.poiGroups[type].forEach((g) => {
        g.visible = true;
      });
      (this.poiStaticMeshes[type] || []).forEach((m) => {
        m.visible = true;
      });
    });
    haptic();
  },

  onFocusSelected() {
    const s = this.data.selected;
    if (!s || !this.camera) return;
    this.target.set(s.x, 0, s.z);
    this.camera.zoom = Math.max(this.camera.zoom, 1.8);
    this.camera.updateProjectionMatrix();
    this.updateCamera();
    this.syncHud();
    haptic();
  },

  onCloseCard() {
    this.setData({ selected: null });
  },

  onRetry() {
    if (this.data.loading) return;
    // 整页重建，确保 WebGL 上下文与 Three 资源干净释放
    wx.reLaunch({
      url: '/pages/map25d/index',
      fail: () => this.initCanvas()
    });
  },

  onShareAppMessage() {
    const suffix = this._areaKey
      ? `?tile=hybrid&area=${this._areaKey}`
      : '';
    return {
      title: '黔山漫游 2.5D 城市地图 · 数字孪生',
      path: '/pages/map25d/index' + suffix
    };
  },

  teardownScene() {
    this._disposed = true;
    if (this._rafId && this._canvas && this._canvas.cancelAnimationFrame) {
      this._canvas.cancelAnimationFrame(this._rafId);
    }
    this._rafId = null;

    if (this.scene) {
      this.scene.traverse((obj) => {
        if (obj.geometry) obj.geometry.dispose();
        if (obj.material) {
          if (Array.isArray(obj.material)) {
            obj.material.forEach((m) => m.dispose());
          } else {
            obj.material.dispose();
          }
        }
      });
    }
    if (this.renderer) this.renderer.dispose();

    this.scene = null;
    this.renderer = null;
    this.camera = null;
    this.poiGroups = null;
    this.poiStaticMeshes = null;
    this.poiVertices = null;
  },

  dispose() {
    this.teardownScene();
    if (this._clockTimer) clearInterval(this._clockTimer);
    if (this._hintTimer) clearTimeout(this._hintTimer);
  }
});

function haptic() {
  try {
    if (wx.vibrateShort) wx.vibrateShort({ type: 'light' });
  } catch (e) {
    // 部分设备/开发者工具不支持震动，忽略
  }
}

function makeLabel(THREE, text) {
  try {
    if (!wx.createOffscreenCanvas) return null;
    const canvas = wx.createOffscreenCanvas({ type: '2d', width: 256, height: 72 });
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, 256, 72);

    ctx.fillStyle = 'rgba(5,9,20,0.78)';
    roundRect(ctx, 2, 12, 252, 48, 12);
    ctx.fill();

    ctx.strokeStyle = 'rgba(0,229,255,0.7)';
    ctx.lineWidth = 2;
    roundRect(ctx, 2, 12, 252, 48, 12);
    ctx.stroke();

    ctx.fillStyle = '#E2E8F0';
    ctx.font = 'bold 26px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, 128, 36);

    const tex = new THREE.CanvasTexture(canvas);
    const mat = new THREE.SpriteMaterial({
      map: tex,
      transparent: true,
      depthTest: false,
      depthWrite: false
    });
    const sprite = new THREE.Sprite(mat);
    sprite.scale.set(150, 42, 1);
    return sprite;
  } catch (e) {
    console.warn('[2.5D] label failed', e);
    return null;
  }
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

function dist(a, b) {
  return Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);
}

function clamp(v, min, max) {
  return Math.min(max, Math.max(min, v));
}
