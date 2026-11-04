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

## 2026-11-04

- `data/学生比赛名录/2026-10-26复判/` 更新并改名为 `data/学生比赛名录/2026-11-04补查/`（上一版内容见 git 历史）。
  - 可以入库 1202、不能入库 317、未完成 62（其中 26 条需人工裁定准入口径）。
  - 不能入库清单：补写关联记录 117 条，改正结论类型 13 条（离线，按表内结论原因）。
  - 未完成清单：上一版 112 条待核查全部用网页检索摘要补查（71 条分 6 组并行检索后复核合并）：转可以入库 48、转不能入库 23、转需人工裁定 5，仍待核查 36。新入库行的依据是检索摘要，入库前须读原文。
  - 逐条见 `本轮补查记录.csv`；上一轮的 `本轮复判记录.csv` 保留。
