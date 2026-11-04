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
  - 可以入库 1246、不能入库 301、未完成 34。
  - 不能入库清单：补写关联记录 117 条，改正结论类型 13 条（离线，按表内结论原因）。
  - 未完成清单：上一版 112 条待核查全部用网页检索摘要补查（71 条分 6 组并行检索后复核合并）：转可以入库 48、转不能入库 23、转需人工裁定 5，仍待核查 36。新入库行的依据是检索摘要，入库前须读原文。
  - 人工裁定：26 条需人工裁定准入口径的行按用户口径收录（名称不含"比赛"的展示/作品展/评奖类、体育专业组、考试排名、志愿服务、境外区域赛），23 条转可以入库，3 条缺届次年份暂留待核查。
  - 不能入库复核 97 条：体育类 60 条按"体育类专业学生组收录"口径重查，5 条入库（510、979、1001、1425 等）、8 条缺专业组规程转待核查；跨届次并入的 5 条改作历史届入库（69、432、664、735、759）；其余类别中本轮未查过的行逐条复核，3 条更正结论类型。
  - 未完成第二轮深度检索 49 条：12 条入库（含 957、1377 补到届次），3 条判不能入库，34 条仍待核查（多为缺主办方原文或当届学生资格）。
  - 逐条见 `本轮补查记录.csv`；上一轮的 `本轮复判记录.csv` 保留。
