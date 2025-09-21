## Modeling3D – Advisor Task Log

Date: 2025-09-19

### Objective
Collect realistic 3D engineering models (PCBs, test equipment, photonics like PICs/LiDAR), demonstrate LLM-driven manipulation, and provide a short video, asset list, images, and notes by Monday.

### Platform
- Chosen: Blender (macOS-friendly; easy scripting; imports FBX/OBJ/STEP via add-ons).

### Initial Sources
- Omniverse LiDAR docs: https://docs.omniverse.nvidia.com/kit/docs/omni.sensors.nv.lidar/latest/lidar_extension.html
- Photonics references: https://www.flexcompute.com/tidy3d/ and https://www.flexcompute.com/photonforge/

### Deliverables (by Monday)
- 60–90s demo video of LLM manipulating a model in Blender
- Asset list (links, formats, license, compatibility)
- 5–10 representative images
- Brief write-up: what worked, blockers, next steps (incl. contractor options)

### Current Status
- Platform decided (Blender). Starting shortlist of Blender-ready assets for PCB, LiDAR sensor, and lab test equipment (oscilloscope/bench PSU).

### Next Actions
1) Source 3–5 Blender-importable models (FBX/OBJ/BLEND) across categories
2) Validate import and hierarchy in Blender; capture screenshots
3) Script basic manipulation (load, select part, move/rotate, parameter tweak); record draft video
4) Compile asset sheet and images; draft report

### Robotics addendum (Analog/Opto Electronics project)
- Hardware status (Boston office): Ubuntu 24.04 Lenovo Legion (RTX 4060, 32GB RAM, i9); MyCobot-280 PI setup pending micro‑HDMI; Meca500-R3 missing female M12 DC connector.
- Immediate tasks:
  - Order DC cord (M12) and micro‑HDMI; identify/buy probe end‑effector; 3D print mount as needed.
  - Install Isaac Sim + ROS on Linux laptop; verify sample scenes.
  - Obtain CAD/models for Elephant Robotics arm and Meca500; import to sim.
  - Build sim scene (arms, PCB fixture, cameras) and stub Expected Information Gain (EIG) planner.
  - Set up imaging station (white and colored illumination); capture PCB images and evaluate lighting wavelengths for defect visibility.
  - Procure simple analog PCBs and intentional-fault boards to form {X} dataset; start RL environment for probing.
  - Implement image→netlist hypothesis and measurement update loop; iterate with EIG.

References: NVIDIA Omniverse repos (kit-app-template, kit-automation-sample, web-viewer-sample, LearnOpenUSD, usd-exchange, PhysicalAI-SimReady-Materials) at https://github.com/orgs/NVIDIA-Omniverse/repositories


