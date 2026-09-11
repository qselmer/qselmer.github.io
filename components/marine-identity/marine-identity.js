(() => {
  'use strict';

  const container = document.getElementById('jsi-flying-fish-container');
  if (!container) return;

  const RENDERER = {
    POINT_INTERVAL: 4,
    FISH_COUNT: 10,
    INIT_HEIGHT_RATE: 0.60,
    THRESHOLD: 36,

    MODEL_NODE_COUNT: 9,
    MODEL_BASE_OFFSET: 0.052,
    MODEL_LIFT_PER_FISH: 0.045,
    MODEL_MAX_LIFT: 0.225,
    MODEL_SMOOTHING: 0.075,
    MODEL_INFLUENCE_RADIUS: 0.20,
    COUNT_AXIS_MAX: 5,
    SHOW_COUNT_AXIS: true,

    SHOW_ISOBATHS: true,
    ISOBATH_COLOR: 'rgba(185,217,232,0.10)',
    ISOBATH_LINE_WIDTH: 1,

    SEA_COLOR_TOP: '#1B6983',
    SEA_COLOR_BOTTOM: '#0E5A73',
    SEA_EDGE: '#8BC7DA',
    SKY_COLOR: '#0b1320',
    MODEL_ANCHOVY_COLOR: '#B9D9E8',
    MODEL_TUNA_COLOR: '#F2C879',
    AXIS_COLOR: 'rgba(255,255,255,0.48)',
    AXIS_TEXT_COLOR: 'rgba(255,255,255,0.72)',

    init() {
      this.container = container;
      this.canvas = document.createElement('canvas');
      this.canvas.setAttribute('aria-hidden', 'true');
      this.container.replaceChildren(this.canvas);
      this.context = this.canvas.getContext('2d');

      this.points = [];
      this.fishes = [];
      this.modelNodeY = { anchovy: [], tuna: [] };
      this.motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
      this.reducedMotion = this.motionQuery.matches;
      this.animationFrameId = null;
      this.resizeTimer = null;
      this.pointerAxis = null;

      this.render = this.render.bind(this);
      this.handleResize = this.handleResize.bind(this);
      this.handlePointerEnter = this.handlePointerEnter.bind(this);
      this.handlePointerMove = this.handlePointerMove.bind(this);
      this.handleMotionPreferenceChange = this.handleMotionPreferenceChange.bind(this);

      this.setup();
      this.bindEvents();
      this.render();
    },

    bindEvents() {
      window.addEventListener('resize', this.handleResize, { passive: true });
      this.container.addEventListener('pointerenter', this.handlePointerEnter, { passive: true });
      this.container.addEventListener('pointermove', this.handlePointerMove, { passive: true });

      if (this.motionQuery.addEventListener) {
        this.motionQuery.addEventListener('change', this.handleMotionPreferenceChange);
      } else if (this.motionQuery.addListener) {
        this.motionQuery.addListener(this.handleMotionPreferenceChange);
      }
    },

    handleResize() {
      window.clearTimeout(this.resizeTimer);
      this.resizeTimer = window.setTimeout(() => {
        this.stopAnimation();
        this.setup();
        this.render();
      }, 160);
    },

    handleMotionPreferenceChange(event) {
      this.reducedMotion = event.matches;
      this.stopAnimation();
      this.setup();
      this.render();
    },

    stopAnimation() {
      if (this.animationFrameId !== null) {
        cancelAnimationFrame(this.animationFrameId);
        this.animationFrameId = null;
      }
    },

    setup() {
      const rect = this.container.getBoundingClientRect();
      this.width = Math.max(1, rect.width);
      this.height = Math.max(1, rect.height);
      this.points.length = 0;
      this.fishes.length = 0;
      this.modelNodeY.anchovy.length = 0;
      this.modelNodeY.tuna.length = 0;
      this.pointerAxis = null;

      const dpr = Math.max(1, window.devicePixelRatio || 1);
      this.canvas.width = Math.round(this.width * dpr);
      this.canvas.height = Math.round(this.height * dpr);
      this.canvas.style.width = `${this.width}px`;
      this.canvas.style.height = `${this.height}px`;
      this.context.setTransform(dpr, 0, 0, dpr, 0, 0);

      for (let i = 0; i < 8; i += 1) this.fishes.push(new Fish(this, 'anchovy'));
      for (let i = 0; i < 2; i += 1) this.fishes.push(new Fish(this, 'tuna'));

      this.createSurfacePoints();
      if (this.reducedMotion) this.layoutStaticFish();
    },

    createSurfacePoints() {
      const count = Math.max(2, Math.round(this.width / this.POINT_INTERVAL));
      this.pointInterval = this.width / (count - 1);

      for (let i = 0; i < count; i += 1) {
        const point = new SurfacePoint(this, i * this.pointInterval);
        const previous = this.points[i - 1];
        if (previous) {
          point.previous = previous;
          previous.next = point;
        }
        this.points.push(point);
      }
    },

    layoutStaticFish() {
      const anchovyLayout = [
        [0.22, 0.52, 1], [0.33, 0.57, -1], [0.47, 0.50, 1], [0.61, 0.56, -1],
        [0.74, 0.51, 1], [0.29, 0.70, -1], [0.50, 0.75, 1], [0.70, 0.79, -1]
      ];
      const tunaLayout = [[0.33, 0.84, 1], [0.67, 0.82, -1]];
      let a = 0;
      let t = 0;

      this.fishes.forEach((fish) => {
        const p = fish.species === 'anchovy'
          ? anchovyLayout[a++ % anchovyLayout.length]
          : tunaLayout[t++ % tunaLayout.length];
        fish.x = this.width * p[0];
        fish.y = this.height * p[1];
        fish.previousY = fish.y;
        fish.vx = p[2];
        fish.vy = 0;
        fish.ay = 0;
        fish.direction = p[2] < 0;
        fish.isOut = false;
      });
    },

    getAxis(event) {
      const rect = this.container.getBoundingClientRect();
      return { x: event.clientX - rect.left, y: event.clientY - rect.top };
    },

    handlePointerEnter(event) {
      if (this.reducedMotion) return;
      this.pointerAxis = this.getAxis(event);
    },

    handlePointerMove(event) {
      if (this.reducedMotion) return;
      const axis = this.getAxis(event);
      if (!this.pointerAxis) this.pointerAxis = axis;
      this.generateEpicenter(axis.x, axis.y, axis.y - this.pointerAxis.y);
      this.pointerAxis = axis;
    },

    getNominalSeaY() {
      return this.height * (1 - this.INIT_HEIGHT_RATE);
    },

    getSurfaceYAtX(x) {
      if (!this.points.length) return this.getNominalSeaY();
      const index = Math.max(0, Math.min(this.points.length - 1, Math.round(x / this.pointInterval)));
      return this.height - this.points[index].height;
    },

    generateEpicenter(x, y, velocity) {
      const waterY = this.getNominalSeaY();
      if (y < waterY - this.THRESHOLD || y > waterY + this.THRESHOLD) return;
      const index = Math.round(x / this.pointInterval);
      if (index < 0 || index >= this.points.length) return;
      this.points[index].interfere(y, velocity);
    },

    update() {
      this.points.forEach((point) => point.updateSelf());
      this.points.forEach((point) => point.updateNeighbors());
    },

    drawSky() {
      const ctx = this.context;
      ctx.save();
      ctx.fillStyle = this.SKY_COLOR;
      ctx.fillRect(0, 0, this.width, this.height);
      ctx.restore();
    },

    buildSeaPath() {
      const ctx = this.context;
      ctx.beginPath();
      ctx.moveTo(0, this.height);
      this.points.forEach((point) => ctx.lineTo(point.x, this.height - point.height));
      ctx.lineTo(this.width, this.height);
      ctx.closePath();
    },

    drawSea() {
      const ctx = this.context;
      ctx.save();
      this.buildSeaPath();
      const gradient = ctx.createLinearGradient(0, this.height * 0.40, 0, this.height);
      gradient.addColorStop(0, this.SEA_COLOR_TOP);
      gradient.addColorStop(1, this.SEA_COLOR_BOTTOM);
      ctx.fillStyle = gradient;
      ctx.fill();
      ctx.restore();
    },

    drawIsobaths() {
      if (!this.SHOW_ISOBATHS) return;
      const ctx = this.context;
      const w = this.width;
      const h = this.height;
      ctx.save();
      this.buildSeaPath();
      ctx.clip();
      ctx.strokeStyle = this.ISOBATH_COLOR;
      ctx.lineWidth = this.ISOBATH_LINE_WIDTH;
      ctx.lineCap = 'round';

      const rows = [
        [0.76, 0.73, 0.79, 0.76, 0.73, 0.79, 0.75],
        [0.85, 0.82, 0.88, 0.84, 0.80, 0.88, 0.84],
        [0.93, 0.90, 0.96, 0.92, 0.88, 0.96, 0.91]
      ];
      rows.forEach((r) => {
        ctx.beginPath();
        ctx.moveTo(w * 0.07, h * r[0]);
        ctx.bezierCurveTo(w * 0.22, h * r[1], w * 0.36, h * r[2], w * 0.50, h * r[3]);
        ctx.bezierCurveTo(w * 0.64, h * r[4], w * 0.79, h * r[5], w * 0.93, h * r[6]);
        ctx.stroke();
      });
      ctx.restore();
    },

    drawWaterline() {
      if (!this.points.length) return;
      const ctx = this.context;
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(this.points[0].x, this.height - this.points[0].height);
      for (let i = 1; i < this.points.length; i += 1) {
        ctx.lineTo(this.points[i].x, this.height - this.points[i].height);
      }
      ctx.strokeStyle = this.SEA_EDGE;
      ctx.lineWidth = 1.5;
      ctx.stroke();
      ctx.restore();
    },

    drawCountAxis(curveBaseY, liftPerUnit, rightX) {
      if (!this.SHOW_COUNT_AXIS) return;
      const ctx = this.context;
      const topY = curveBaseY - this.COUNT_AXIS_MAX * liftPerUnit;
      const axisX = this.width * 0.205;
      const tickLength = this.width * 0.010;

      ctx.save();
      ctx.strokeStyle = this.AXIS_COLOR;
      ctx.fillStyle = this.AXIS_TEXT_COLOR;
      ctx.lineWidth = 0.8;
      ctx.lineCap = 'round';

      ctx.beginPath();
      ctx.moveTo(axisX, curveBaseY);
      ctx.lineTo(axisX, topY);
      ctx.moveTo(axisX, curveBaseY);
      ctx.lineTo(rightX, curveBaseY);
      ctx.stroke();

      for (let n = 0; n <= this.COUNT_AXIS_MAX; n += 1) {
        const y = curveBaseY - n * liftPerUnit;
        ctx.beginPath();
        ctx.moveTo(axisX - tickLength, y);
        ctx.lineTo(axisX, y);
        ctx.stroke();
      }

      ctx.font = `italic ${Math.max(9, Math.round(this.width * 0.018))}px Georgia`;
      ctx.textAlign = 'left';
      ctx.textBaseline = 'middle';
      ctx.fillText('n(x)', axisX + this.width * 0.012, topY + this.height * 0.010);
      ctx.restore();
    },

    getModelTargetSeries(xs, species, curveBaseY, liftPerUnit, minimumCurveY, influenceRadius) {
      const targetY = xs.map(() => curveBaseY);
      for (let ni = 1; ni < xs.length - 1; ni += 1) {
        let abundance = 0;
        this.fishes.forEach((fish) => {
          if (fish.x < 0 || fish.x > this.width || fish.species !== species) return;
          if (fish.y < this.getSurfaceYAtX(fish.x)) return;
          const distance = Math.abs(fish.x - xs[ni]);
          if (distance > influenceRadius) return;
          abundance += 1 - distance / influenceRadius;
        });
        const target = curveBaseY - abundance * liftPerUnit;
        targetY[ni] = Math.max(target, minimumCurveY);
      }
      return targetY;
    },

    updateModelSeries(name, targetY, curveBaseY) {
      const series = this.modelNodeY[name];
      if (series.length !== targetY.length) {
        series.length = 0;
        targetY.forEach(() => series.push(curveBaseY));
      }
      series[0] = curveBaseY;
      series[series.length - 1] = curveBaseY;
      for (let i = 1; i < series.length - 1; i += 1) {
        series[i] += (targetY[i] - series[i]) * this.MODEL_SMOOTHING;
      }
    },

    drawSmoothCurve(xs, ys, color, width, dash) {
      const ctx = this.context;
      const points = xs.map((x, i) => ({ x, y: ys[i] }));
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(points[0].x, points[0].y);
      for (let i = 1; i < points.length - 1; i += 1) {
        const xc = (points[i].x + points[i + 1].x) / 2;
        const yc = (points[i].y + points[i + 1].y) / 2;
        ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc);
      }
      const last = points.length - 1;
      ctx.quadraticCurveTo(points[last - 1].x, points[last - 1].y, points[last].x, points[last].y);
      ctx.strokeStyle = color;
      ctx.lineWidth = width;
      ctx.lineJoin = 'round';
      ctx.lineCap = 'round';
      ctx.setLineDash(dash || []);
      ctx.stroke();
      ctx.restore();
    },

    drawModel() {
      const leftX = this.width * 0.235;
      const rightX = this.width * 0.885;
      const xs = Array.from({ length: this.MODEL_NODE_COUNT }, (_, i) =>
        leftX + (rightX - leftX) * (i / (this.MODEL_NODE_COUNT - 1))
      );
      const curveBaseY = this.getNominalSeaY() - this.height * this.MODEL_BASE_OFFSET;
      const liftPerUnit = this.height * this.MODEL_LIFT_PER_FISH;
      const minimumCurveY = curveBaseY - this.height * this.MODEL_MAX_LIFT;
      const influenceRadius = this.width * this.MODEL_INFLUENCE_RADIUS;

      this.drawCountAxis(curveBaseY, liftPerUnit, rightX);
      const anchovyTarget = this.getModelTargetSeries(xs, 'anchovy', curveBaseY, liftPerUnit, minimumCurveY, influenceRadius);
      const tunaTarget = this.getModelTargetSeries(xs, 'tuna', curveBaseY, liftPerUnit, minimumCurveY, influenceRadius);
      this.updateModelSeries('anchovy', anchovyTarget, curveBaseY);
      this.updateModelSeries('tuna', tunaTarget, curveBaseY);
      this.drawSmoothCurve(xs, this.modelNodeY.anchovy, this.MODEL_ANCHOVY_COLOR, 1.8, []);
      this.drawSmoothCurve(xs, this.modelNodeY.tuna, this.MODEL_TUNA_COLOR, 1.7, [5, 4]);
    },

    render() {
      if (!this.reducedMotion) this.animationFrameId = requestAnimationFrame(this.render);
      else this.animationFrameId = null;

      if (!this.reducedMotion) this.update();

      this.context.clearRect(0, 0, this.width, this.height);
      this.drawSky();
      this.drawSea();
      this.drawIsobaths();
      this.drawModel();
      this.fishes.forEach((fish) => fish.render(this.context, this.reducedMotion));
      this.drawWaterline();
    }
  };

  class SurfacePoint {
    constructor(renderer, x) {
      this.renderer = renderer;
      this.x = x;
      this.initHeight = renderer.height * renderer.INIT_HEIGHT_RATE;
      this.height = this.initHeight;
      this.fy = 0;
      this.previous = null;
      this.next = null;
      this.forcePrevious = 0;
      this.forceNext = 0;
    }

    interfere(y, velocity) {
      const sign = (this.renderer.height - this.height - y) >= 0 ? -1 : 1;
      this.fy = this.renderer.height * 0.006 * sign * Math.abs(velocity);
    }

    updateSelf() {
      this.fy += 0.018 * (this.initHeight - this.height);
      this.fy *= 0.90;
      this.height += this.fy;
    }

    updateNeighbors() {
      this.forcePrevious = this.previous ? 0.22 * (this.height - this.previous.height) : 0;
      this.forceNext = this.next ? 0.22 * (this.height - this.next.height) : 0;
      if (this.previous) {
        this.previous.height += this.forcePrevious;
        this.previous.fy += this.forcePrevious;
      }
      if (this.next) {
        this.next.height += this.forceNext;
        this.next.fy += this.forceNext;
      }
    }
  }

  class Fish {
    constructor(renderer, species) {
      this.renderer = renderer;
      this.species = species;
      this.gravity = 0.20;
      this.init();
    }

    random(min, max) {
      return min + (max - min) * Math.random();
    }

    init() {
      this.direction = Math.random() < 0.5;
      this.x = this.direction ? this.renderer.width + this.renderer.THRESHOLD : -this.renderer.THRESHOLD;
      this.vx = this.random(0.75, 1.45) * (this.direction ? -1 : 1);
      this.theta = 0;
      this.isOut = false;

      if (this.species === 'anchovy') {
        this.size = this.random(0.50, 0.68);
        this.color = '#B5C7CE';
        this.y = Math.random() < 0.65
          ? this.random(this.renderer.height * 0.56, this.renderer.height * 0.72)
          : this.random(this.renderer.height * 0.72, this.renderer.height * 0.88);
        this.vy = this.random(-0.45, -0.20);
        this.ay = this.random(-0.006, -0.002);
      } else {
        this.size = this.random(0.92, 1.10);
        this.color = '#8798A2';
        this.y = Math.random() < 0.5
          ? this.random(this.renderer.height * 0.60, this.renderer.height * 0.78)
          : this.random(this.renderer.height * 0.74, this.renderer.height * 0.90);
        this.vy = this.random(-0.40, -0.18);
        this.ay = this.random(-0.006, -0.002);
      }
      this.previousY = this.y;
    }

    controlStatus() {
      this.previousY = this.y;
      this.x += this.vx;
      this.y += this.vy;
      this.vy += this.ay;
      const waterY = this.renderer.getNominalSeaY();

      if (this.y < waterY) {
        this.vy += this.gravity;
        this.isOut = true;
      } else {
        if (this.isOut) this.ay = this.random(-0.012, -0.004);
        this.isOut = false;
      }

      if (!this.isOut) {
        this.theta = (this.theta + Math.PI / 55) % (Math.PI * 2);
      }

      this.renderer.generateEpicenter(
        this.x + (this.direction ? -1 : 1) * this.renderer.THRESHOLD,
        this.y,
        (this.y - this.previousY) * 0.30
      );

      if ((this.vx > 0 && this.x > this.renderer.width + this.renderer.THRESHOLD) ||
          (this.vx < 0 && this.x < -this.renderer.THRESHOLD)) {
        this.init();
      }
    }

    drawAnchovy(context) {
      context.fillStyle = this.color;

      context.save();
      context.translate(31, 0);
      context.scale(0.97 + 0.05 * Math.sin(this.theta), 1);
      context.beginPath();
      context.moveTo(0, -2);
      context.quadraticCurveTo(7, -5, 15, -11);
      context.quadraticCurveTo(12, -4, 8, 0);
      context.quadraticCurveTo(12, 4, 15, 11);
      context.quadraticCurveTo(7, 5, 0, 2);
      context.closePath();
      context.fill();
      context.restore();

      context.beginPath();
      context.moveTo(-2, -8);
      context.quadraticCurveTo(5, -16, 12, -18);
      context.quadraticCurveTo(10, -10, 5, -7);
      context.closePath();
      context.fill();

      context.beginPath();
      context.moveTo(14, 5);
      context.quadraticCurveTo(20, 10, 25, 11);
      context.quadraticCurveTo(22, 6, 17, 4);
      context.closePath();
      context.fill();

      context.beginPath();
      context.moveTo(-9, 2);
      context.quadraticCurveTo(-1, 7, 7, 7);
      context.quadraticCurveTo(2, 3, -9, 2);
      context.closePath();
      context.fill();

      context.beginPath();
      context.moveTo(-27, 0);
      context.quadraticCurveTo(-27, -5, -21, -8);
      context.bezierCurveTo(-10, -10, 5, -10, 22, -5);
      context.quadraticCurveTo(28, -3, 31, -1.7);
      context.quadraticCurveTo(32, 0, 31, 1.7);
      context.quadraticCurveTo(28, 3, 22, 5);
      context.bezierCurveTo(5, 9, -10, 9, -21, 8);
      context.quadraticCurveTo(-27, 5, -27, 0);
      context.closePath();
      context.fill();
    }

    drawTuna(context) {
      context.fillStyle = this.color;

      context.save();
      context.translate(41, 0);
      context.scale(0.95 + 0.06 * Math.sin(this.theta), 1);
      context.beginPath();
      context.moveTo(0, -2.5);
      context.quadraticCurveTo(8, -6, 18, -16);
      context.quadraticCurveTo(14, -6, 9, 0);
      context.quadraticCurveTo(14, 6, 18, 16);
      context.quadraticCurveTo(8, 6, 0, 2.5);
      context.closePath();
      context.fill();
      context.restore();

      context.beginPath();
      context.moveTo(-3, -10);
      context.quadraticCurveTo(5, -25, 15, -28);
      context.quadraticCurveTo(14, -15, 7, -8);
      context.closePath();
      context.fill();

      context.beginPath();
      context.moveTo(19, -7);
      context.quadraticCurveTo(27, -14, 34, -15);
      context.quadraticCurveTo(31, -8, 25, -5);
      context.closePath();
      context.fill();

      context.beginPath();
      context.moveTo(18, 7);
      context.quadraticCurveTo(26, 14, 33, 15);
      context.quadraticCurveTo(30, 8, 24, 5);
      context.closePath();
      context.fill();

      context.beginPath();
      context.moveTo(-8, 3);
      context.quadraticCurveTo(1, 10, 11, 9);
      context.quadraticCurveTo(4, 4, -8, 3);
      context.closePath();
      context.fill();

      context.beginPath();
      context.moveTo(-30, 0);
      context.quadraticCurveTo(-31, -7, -23, -12);
      context.bezierCurveTo(-9, -18, 13, -18, 31, -9);
      context.quadraticCurveTo(39, -5, 41, -2);
      context.quadraticCurveTo(42, 0, 41, 2);
      context.quadraticCurveTo(39, 5, 31, 9);
      context.bezierCurveTo(13, 17, -9, 18, -23, 12);
      context.quadraticCurveTo(-31, 7, -30, 0);
      context.closePath();
      context.fill();
    }

    render(context, staticMode) {
      context.save();
      context.translate(this.x, this.y);
      context.rotate(Math.PI + Math.atan2(this.vy, this.vx));
      context.scale(this.size, this.size * (this.direction ? 1 : -1));
      if (this.species === 'anchovy') this.drawAnchovy(context);
      else this.drawTuna(context);
      context.restore();
      if (!staticMode) this.controlStatus();
    }
  }

  RENDERER.init();
})();
