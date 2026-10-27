# Update Log

## 2026-09-20

- Initialized competition database project.
- Added repository documentation.
- Started high-quality competition data collection.
- Data standards:
  - Competition name
  - Competition time
  - Official website
  - Suitable majors
  - Category
  - Organizer
  - Verification status

## Roadmap

- Phase 1: Computer science, AI, cybersecurity, robotics
- Phase 2: Engineering disciplines
- Phase 3: Mathematics, statistics, economics
- Phase 4: Medicine and life sciences
- Phase 5: Humanities, design and comprehensive competitions

## 2026-10-27

- 新增 `data/学生比赛名录/2026-10-26复判/`：学生比赛名录 1581 行的入库资格整理（复判版）。
  - 可以入库 1154、不能入库 294、未完成 133（其中 21 条需人工裁定准入口径）。
  - 上一版 478 条未完成按表内既有证据复判；复判时网络受限，未重读原文，项目准入代码未重跑。
  - 判定口径、字段说明和统计见该目录下 `字段说明与统计汇总.md`；逐条去向见 `本轮复判记录.csv`。
- 新增 `scripts/fetch_posters.py`：从可以入库记录的官方来源页面查找并转存海报，输出到 `data/学生比赛名录/海报/`。尚未运行（等待网络放开）。
