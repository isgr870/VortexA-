# Canonical robot model contract

**Status:** Phase 1 — authoritative for exporters/importers  
**Schema id:** `vortexa.canonical_robot`  
**Schema version:** `1.0.0`  
**Baseline:** VortexA Studio ≥ 3.6.5 (`main` @ provenance + event-bind commits)

This document defines what a robot **is** inside VortexA before any export or import transform. Exporters consume this contract (or a documented projection of it). They must not invent independent physics or hierarchy rules silently.

---

## 1. Purpose

| Goal | Rule |
|------|------|
| Single source of truth | One validated model feeds all exporters |
| No silent loss | Unsupported or transformed fields are **reported** |
| Provenance | Estimated / defaulted / generated values stay labeled |
| Honest claims | Structural validity ≠ simulator import ≠ physical verification |

---

## 2. Units and frames (system-wide)

| Quantity | Unit | Notes |
|----------|------|--------|
| Length | metres (m) | |
| Mass | kilograms (kg) | |
| Angle | radians | UI may show degrees; storage is rad |
| Time | seconds (s) | |
| Inertia | kg·m² about link CoM | Full tensor preferred |
| Force / torque | N / N·m | When present |

**Frames**

- Default model frame: right-handed; **Z up** unless a format forces another convention (then transform is explicit in the export report).
- Each link has a local frame; joint origin is parent → child transform.
- Rotation: RPY (roll-pitch-yaw) about fixed axes **or** explicit 3×3; exporters document which they emit.

Invalid non-finite numbers (`NaN`, `Inf`) are **rejected** at validation.

---

## 3. Model root

```json
{
  "schema": "vortexa.canonical_robot",
  "schema_version": "1.0.0",
  "id": "string-stable-id",
  "name": "human readable",
  "units": { "length": "m", "mass": "kg", "angle": "rad" },
  "frames": { "up_axis": "Z", "handedness": "right" },
  "links": [],
  "joints": [],
  "provenance": {},
  "validation": {
    "structural_ok": false,
    "compatibility_verification": "not_tested"
  }
}
```

Legacy topology arrays (link list with embedded joint fields) are **admitted** as a projection of this schema until migration is complete. New code should prefer explicit `links` + `joints`.

---

## 4. Link

Required:

- `id` — stable string, unique in model  
- `name` — unique display name  

Optional / validated when present:

- `mass` (kg) > 0  
- `com` — `{x,y,z}` in link frame (m)  
- `inertia` — `{ixx,iyy,izz,ixy,ixz,iyz}` about CoM  
- `visuals[]` — geometry primitives or mesh refs  
- `collisions[]` — geometry primitives or mesh refs  
- `material` — string key or RGBA  

**Geometry primitives (supported subset v1):** `box`, `cylinder`, `sphere`.  
**Mesh:** allowed in project storage; each exporter must either embed/reference mesh or mark `unsupported: mesh`.

---

## 5. Joint

Required:

- `id`, `name`  
- `type` — one of: `fixed`, `revolute`, `continuous`, `prismatic` (v1)  
- `parent` — link id  
- `child` — link id  

Optional:

- `origin` — `{xyz: [x,y,z], rpy: [r,p,y]}` parent → child  
- `axis` — unit vector `[x,y,z]` (not only dominant axis)  
- `limit` — `{lower, upper, effort, velocity}`  
- `dynamics` — `{damping, friction}` when known  

**Reject:** missing parent/child, cycles (unless future closed-chain profile), unknown type without explicit map.

**Do not:** silently default invalid type to `revolute` without a warning in the export/validation report.

---

## 6. Provenance

Every physical or geometric field that enrichment touches must carry origin:

| Value | Meaning |
|-------|---------|
| `present_in_input` | Caller supplied a value (not proof it is measured) |
| `estimated` | Computed from geometry/material heuristics |
| `defaulted` | Fixed fallback when missing |
| `generated` | Created geometry (e.g. collision proxy) |
| `not_applicable` | Field does not apply |

Provenance lives **beside** topology (e.g. `field_provenance` / model `provenance`), not as a silent overwrite of user fields when avoidable.

`present_in_input` ≠ lab-measured ≠ simulator-verified.

---

## 7. Validation layers (do not collapse)

1. **Structural** — graph, names, types, finite numbers  
2. **Format** — target file is well-formed (XML/USD package layout)  
3. **Import** — target tool loads the artifact (version pinned)  
4. **Physical** — optional checks; never implied by (1)–(3)  
5. **Safety certification** — out of scope unless a formal process exists  

API / UI:

- Prefer `structural_targets` over “ready for MuJoCo/Isaac”.  
- Always allow `compatibility_verification: "not_tested" | "passed" | "failed"`.  
- Deprecated: implying simulator readiness from score thresholds alone.

---

## 8. Exporter obligations

Each exporter **must**:

1. Take validated canonical model (or documented legacy projection).  
2. Preserve supported fields or list them under `approximated` / `defaulted` / `unsupported` in an **export report**.  
3. Refuse or hard-warn on unresolved parents (no silent re-parent to “previous link”).  
4. Record exporter name + version + schema_version in the report.  
5. Never claim “simulation-ready” without a recorded load test for that target.

### v1 support intent (to be evidenced, not assumed)

| Target | Structural export | Physics fidelity | Load test required for “compatible” claim |
|--------|-------------------|------------------|-------------------------------------------|
| URDF | Yes | Mass/inertia/geometry subset | Parser + one consumer |
| MJCF | Hierarchy from parents | Mass/inertia/joints subset | MuJoCo version X load |
| USD | Hierarchy + meshes/prims | Joint schemas only if implemented | Declared USD/Isaac path |
| ROS 2 | Description package | Via URDF | `colcon` + launch smoke |
| PyBullet | Runner + URDF | Via URDF | Load + joint count check |

---

## 9. Importer obligations (URDF v1)

1. Publish supported URDF feature list.  
2. Preserve supported properties; **warn** on drop.  
3. Reject or quarantine models that cannot be represented without unacceptable loss (policy: warn vs reject TBD per feature).  
4. Round-trip test: import → canonical → export → diff within tolerance for supported subset.

---

## 10. Reject rules (minimum)

- Empty link set  
- Duplicate link/joint ids or names  
- Non-finite mass, inertia, limits, axes  
- Mass ≤ 0 when mass required by validation profile  
- Joint axis not unit length (after normalization policy)  
- Unknown joint type without explicit mapping entry  

---

## 11. Out of scope for schema 1.0.0

- Full mesh-to-mesh collision certification  
- Complete articulated-body dynamics (CRBA/ABA) as product truth  
- Closed-loop mechanisms  
- Hardware `ros2_control` deployment  
- Safety certification  

Approximate dynamics and heuristic collision remain **labeled design-time tools**.

---

## 12. Implementation map (repo)

| Concern | Likely home |
|---------|-------------|
| Enrichment + provenance | `scripts/health_validator.py`, server `enrich_physics` |
| Structural validate | `scripts/health_validator.py` |
| URDF out | `scripts/urdf_generator_api.py` |
| MJCF out | `scripts/mjcf_export.py` |
| USD out | `scripts/usd_export.py` |
| ROS 2 out | `scripts/ros2_export.py` |
| URDF in | `scripts/urdf_import.py` |
| Project persist | server project actions + schema version field |

---

## 13. Change control

- Bump `schema_version` on breaking field changes.  
- Project files should record `canonical_schema_version` when emission starts.  
- Exporters pin the minimum schema they understand.

**Principle:** smaller verified contract > large implied capability.
