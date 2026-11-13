# Roadmap

## Now (v3.6.x) — Trust the foundation
- [x] Localhost-first bridge + session token
- [x] Path containment for project/export IO
- [x] pytest CI + template smoke
- [x] Desktop packaging workflows (Win/Linux/macOS)
- [ ] Attach desktop zips to GitHub Releases
- [ ] Pose-aware collision (or keep clearly experimental)
- [ ] Full 6D IK option (position + orientation)

## Next — Design depth
- [ ] Formal topology schema (branched trees, joint origins)
- [ ] Independent exporter validation (URDF/MJCF load checks)
- [ ] Multi-chain simultaneous visualization & dual-arm tools
- [ ] Trajectory editor with CSV/ROS-friendly export

## Later — Platform
- [ ] Capacitor Android APK (UI shell + bridge strategy)
- [ ] Optional cloud project sync (opt-in)
- [ ] Plugin API for custom exporters

## Non-goals (explicit)
- Guaranteeing Gazebo/Isaac acceptance without external validation
- Physical motor drivers / safety-rated control
