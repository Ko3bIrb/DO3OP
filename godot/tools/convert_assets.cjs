// Development-only converter. Runtime uses native Godot scenes and GDScript.
// Run: npm install --prefix godot/tools && node godot/tools/convert_assets.cjs
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const { createCanvas } = require('@napi-rs/canvas');
const root = path.resolve(__dirname, '../..');
const THREE = require(path.join(root, 'vendor/three-r128/three.min.js'));
const output = path.join(root, 'godot/assets/models');
fs.mkdirSync(output, { recursive: true });
function context(map) {
    const math = Object.create(Math); let seed = map === 'Hell' ? 1701 : 4201;
    math.random = () => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed / 4294967296; };
    const c = vm.createContext({ THREE, Math: math, console, performance: { now: () => 0 },
        navigator: { userAgent: 'Godot asset conversion' }, window: { innerWidth: 1440, innerHeight: 900, addEventListener() {} },
        document: { createElement: () => createCanvas(16, 16) }, setTimeout() {} });
    for (const file of ['js/core/engine.js', 'js/towers/towers-data.js', 'js/towers/towers-models.js',
        `js/core/${map}/textures.js`, `js/world/${map}/maps.js`, `js/world/${map}/path.js`, `js/world/${map}/decor.js`,
        `js/enemies/${map}/enemies-data.js`, `js/enemies/${map}/enemies-models.js`, `js/enemies/${map}/enemies-spawn.js`]) {
        vm.runInContext(fs.readFileSync(path.join(root, file), 'utf8'), c, { filename: file });
    }
    return c;
}

// Merge static geometry by material while preserving functional pivots separately.
function merge(rootNode, name) {
    rootNode.updateMatrixWorld(true);
    const groups = new Map(); const sprites = [];
    rootNode.traverse(o => {
        if (o.isSprite) { sprites.push(o); return; }
        if (!o.isMesh || !o.geometry.attributes.position) return;
        const geometry = o.geometry;
        const mats = Array.isArray(o.material) ? o.material : [o.material];
        const slices = geometry.groups.length ? geometry.groups : [{ start: 0, count: geometry.index ? geometry.index.count : geometry.attributes.position.count, materialIndex: 0 }];
        for (let instance = 0; instance < (o.isInstancedMesh ? o.count : 1); instance++) {
            let matrix = o.matrixWorld.clone();
            if (o.isInstancedMesh) { const local = new THREE.Matrix4(); o.getMatrixAt(instance, local); matrix.multiply(local); }
            const normalMatrix = new THREE.Matrix3().getNormalMatrix(matrix);
            for (const slice of slices) {
                const mat = mats[slice.materialIndex || 0]; if (!mat || mat.opacity === 0) continue;
                const key = JSON.stringify([mat.type, mat.color?.getHex(), mat.emissive?.getHex(), mat.emissiveIntensity, mat.opacity, mat.side, mat.roughness, mat.metalness, mat.map?.uuid, mat.map?.repeat.toArray(), mat.vertexColors]);
                if (!groups.has(key)) groups.set(key, { mat, p: [], n: [], uv: [], colors: [] });
                const g = groups.get(key); const pos = geometry.attributes.position, normals = geometry.attributes.normal, uv = geometry.attributes.uv, colors = geometry.attributes.color;
                for (let k = slice.start; k < Math.min(slice.start + slice.count, geometry.index ? geometry.index.count : pos.count); k++) {
                    const index = geometry.index ? geometry.index.getX(k) : k;
                    const p = new THREE.Vector3().fromBufferAttribute(pos, index).applyMatrix4(matrix);
                    const n = normals ? new THREE.Vector3().fromBufferAttribute(normals, index).applyMatrix3(normalMatrix).normalize() : new THREE.Vector3(0, 1, 0);
                    g.p.push(p.x, p.y, p.z); g.n.push(n.x, n.y, n.z);
                    g.uv.push(uv ? uv.getX(index) : 0, uv ? uv.getY(index) : 0);
                    if (mat.vertexColors) g.colors.push(colors ? colors.getX(index) : 1, colors ? colors.getY(index) : 1, colors ? colors.getZ(index) : 1);
                }
            }
        }
    });
    const result = new THREE.Group(); result.name = name;
    for (const g of groups.values()) {
        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(g.p, 3));
        geometry.setAttribute('normal', new THREE.Float32BufferAttribute(g.n, 3));
        geometry.setAttribute('uv', new THREE.Float32BufferAttribute(g.uv, 2));
        if (g.colors.length) geometry.setAttribute('color', new THREE.Float32BufferAttribute(g.colors, 3));
        result.add(new THREE.Mesh(geometry, g.mat));
    }
    for (const sprite of sprites) {
        const p = new THREE.Vector3(), q = new THREE.Quaternion(), s = new THREE.Vector3(); sprite.matrixWorld.decompose(p, q, s);
        const mesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), sprite.material);
        mesh.name = 'billboard'; mesh.position.copy(p); mesh.scale.copy(s); result.add(mesh);
    }
    return result;
}

function glb(rootNode, file) {
    const json = { asset: { version: '2.0', generator: 'Game Defender source asset migration' }, scene: 0, scenes: [{ nodes: [] }], nodes: [], meshes: [], materials: [], accessors: [], bufferViews: [], buffers: [{ byteLength: 0 }], images: [], textures: [], samplers: [], extensionsUsed: ['KHR_materials_unlit', 'KHR_texture_transform'] };
    const chunks = []; let length = 0; const materials = new Map(), textures = new Map();
    function buffer(data) {
        const bytes = Buffer.from(data.buffer || data, data.byteOffset || 0, data.byteLength || data.length);
        const index = json.bufferViews.length;
        json.bufferViews.push({ buffer: 0, byteOffset: length, byteLength: bytes.length });
        chunks.push(bytes); length += bytes.length;
        const padding = (4 - length % 4) % 4; if (padding) { chunks.push(Buffer.alloc(padding)); length += padding; }
        return index;
    }
    function accessor(array, width) {
        const values = new Float32Array(array); const min = Array(width).fill(Infinity), max = Array(width).fill(-Infinity);
        for (let i = 0; i < values.length; i++) { min[i % width] = Math.min(min[i % width], values[i]); max[i % width] = Math.max(max[i % width], values[i]); }
        const index = json.accessors.length;
        json.accessors.push({ bufferView: buffer(values), componentType: 5126, count: values.length / width, type: ['','SCALAR','VEC2','VEC3','VEC4'][width], min, max });
        return index;
    }
    function texture(tex) {
        if (textures.has(tex.uuid)) return textures.get(tex.uuid);
        const image = tex.image; const c = createCanvas(image.width, image.height); const ctx = c.getContext('2d');
        if (tex.flipY) { ctx.translate(0, image.height); ctx.scale(1, -1); }
        ctx.drawImage(image, 0, 0);
        const source = json.images.length; json.images.push({ bufferView: buffer(c.toBuffer('image/png')), mimeType: 'image/png' });
        const sampler = json.samplers.length; json.samplers.push({ magFilter: 9729, minFilter: 9987, wrapS: tex.wrapS === THREE.RepeatWrapping ? 10497 : 33071, wrapT: tex.wrapT === THREE.RepeatWrapping ? 10497 : 33071 });
        const index = json.textures.length; json.textures.push({ source, sampler }); textures.set(tex.uuid, index); return index;
    }
    function material(m) {
        if (materials.has(m.uuid)) return materials.get(m.uuid);
        const color = m.color || new THREE.Color(0xffffff);
        const data = { name: m.type, pbrMetallicRoughness: { baseColorFactor: [...color.toArray(), m.opacity ?? 1], metallicFactor: m.metalness ?? 0, roughnessFactor: m.roughness ?? 1 }, doubleSided: m.side === THREE.DoubleSide || m.isSpriteMaterial };
        if (m.transparent || m.isSpriteMaterial) data.alphaMode = 'BLEND';
        if (m.alphaTest) { data.alphaMode = 'MASK'; data.alphaCutoff = m.alphaTest; }
        if (m.isMeshBasicMaterial || m.isSpriteMaterial) data.extensions = { KHR_materials_unlit: {} };
        if (m.emissive) data.emissiveFactor = m.emissive.toArray().map(v => Math.min(1, v * (m.emissiveIntensity ?? 1)));
        if (m.map) data.pbrMetallicRoughness.baseColorTexture = { index: texture(m.map), extensions: { KHR_texture_transform: { offset: m.map.offset.toArray(), scale: m.map.repeat.toArray() } } };
        const index = json.materials.length; json.materials.push(data); materials.set(m.uuid, index); return index;
    }
    function visit(o) {
        const index = json.nodes.length; const node = { name: o.name || 'object', translation: o.position.toArray(), rotation: o.quaternion.toArray(), scale: o.scale.toArray() }; json.nodes.push(node);
        if (o.isMesh) {
            const attrs = o.geometry.attributes;
            const attributes = { POSITION: accessor(attrs.position.array, 3) };
            if (attrs.normal) attributes.NORMAL = accessor(attrs.normal.array, 3);
            if (attrs.uv) attributes.TEXCOORD_0 = accessor(attrs.uv.array, 2);
            if (attrs.color) attributes.COLOR_0 = accessor(attrs.color.array, 3);
            const primitive = { attributes, material: material(o.material), mode: 4 };
            if (o.geometry.index) {
                const indices = new Uint32Array(o.geometry.index.array), acc = json.accessors.length;
                json.accessors.push({ bufferView: buffer(indices), componentType: 5125, count: indices.length, type: 'SCALAR' }); primitive.indices = acc;
            }
            node.mesh = json.meshes.length; json.meshes.push({ primitives: [primitive] });
        }
        if (o.children.length) node.children = o.children.map(visit);
        return index;
    }
    json.scenes[0].nodes.push(visit(rootNode)); json.buffers[0].byteLength = length;
    const text = Buffer.from(JSON.stringify(json)); const jsonChunk = Buffer.concat([text, Buffer.alloc((4 - text.length % 4) % 4, 32)]), bin = Buffer.concat(chunks);
    const header = Buffer.alloc(20); header.writeUInt32LE(0x46546c67); header.writeUInt32LE(2, 4); header.writeUInt32LE(12 + 8 + jsonChunk.length + 8 + bin.length, 8); header.writeUInt32LE(jsonChunk.length, 12); header.writeUInt32LE(0x4e4f534a, 16);
    const binHeader = Buffer.alloc(8); binHeader.writeUInt32LE(bin.length); binHeader.writeUInt32LE(0x004e4942, 4);
    fs.writeFileSync(path.join(output, file), Buffer.concat([header, jsonChunk, binHeader, bin]));
    console.log(file, json.meshes.length, 'surfaces', Math.round(bin.length / 1024), 'KiB');
}

const data = { schema: 1, source_commit: '423218a9bdd971566c51c4cea87b2c29fbd8c3dc', maps: {} };
for (const mapName of ['Hell', 'Ice']) {
    const c = context(mapName); const id = mapName.toLowerCase();
    const map = vm.runInContext(`setCurrentMap('${id}')`, c);
    data.maps[id] = JSON.parse(vm.runInContext(`JSON.stringify({id: currentMap.id, name: currentMap.name, waypoints: currentMap.waypoints.map(p=>[p.x,p.y,p.z]), spots: currentMap.towerSpots.map(p=>({position:[p.x,p.y,p.z], restricted_to:p.restrictedTo||''})), enemies: ENEMIES_DATA, waves: WAVES_TABLE, gaps: SPAWN_GAP, group_gap: GROUP_EXTRA_GAP})`, c));
    if (id === 'hell') {
        data.towers = JSON.parse(vm.runInContext('JSON.stringify(TOWERS_DATA)', c));
        data.difficulty = JSON.parse(vm.runInContext('JSON.stringify(DIFFICULTY_PRESETS)', c));
        for (const type of Object.keys(data.towers)) {
            data.towers[type].levels = [1,2,3].map(level => JSON.parse(vm.runInContext(`JSON.stringify(getTowerStatsForLevel('${type}', ${level}))`, c)));
            data.towers[type].upgrade_costs = [1,2,3].map(level => vm.runInContext(`getUpgradeCost('${type}', ${level})`, c));
            data.towers[type].muzzles = [];
            for (const level of [1,2,3]) {
                const tower = vm.runInContext(`buildTowerModel('${type}',${level})`, c);
                tower.updateMatrixWorld(true);
                data.towers[type].muzzles.push(tower.userData.muzzlePoint.getWorldPosition(new THREE.Vector3()).toArray());
                const turret = tower.userData.turret; tower.remove(turret); tower.updateMatrixWorld(true);
                const base = merge(tower, 'base'); const model = new THREE.Group(); model.add(base);
                turret.updateMatrix();
                const pivotPosition = new THREE.Vector3().copy(turret.position).multiply(tower.scale);
                turret.position.set(0,0,0); turret.scale.multiply(tower.scale);
                const top = merge(turret, 'turret'); top.position.copy(pivotPosition); model.add(top);
                glb(model, `tower_${type}_${level}.glb`);
            }
        }
    }
    for (const type of Object.keys(data.maps[id].enemies)) glb(merge(vm.runInContext(`buildEnemyModel('${type}')`, c), type), `enemy_${type}.glb`);
    vm.runInContext('scene = new THREE.Scene(); renderer = {capabilities:{getMaxAnisotropy:()=>4}}; createFloor(); createPath(currentMap); createDecor(currentMap.waypoints, currentMap.towerSpots);', c);
    glb(merge(vm.runInContext('scene', c), id), `world_${id}.glb`);
}
fs.writeFileSync(path.join(root, 'godot/data/game_data.json'), JSON.stringify(data, null, 2) + '\n');
const manifest = Object.fromEntries(fs.readdirSync(output).filter(f=>f.endsWith('.glb')).map(f=>[f, crypto.createHash('sha256').update(fs.readFileSync(path.join(output,f))).digest('hex')]));
fs.writeFileSync(path.join(root, 'godot/data/asset_manifest.json'), JSON.stringify({source_commit:data.source_commit,files:manifest},null,2)+'\n');
