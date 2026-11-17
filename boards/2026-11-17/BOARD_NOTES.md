# 榜单接入记录（2026-11-17）

本轮把四家公开榜单接进同一套单元表，并做了两件此前只在 robocurve 上做过的事：一是用不需要样本量的检验判断"两个模型是否分得开"，二是对照各站是否公布每格次数。

## 一、接入方式

| 榜单 | 入口 | 形态 | 抓取方式 |
|---|---|---|---|
| robocurve | `robocurve.org/all-runs/` → `runs.robocurve.org/.../log/` | 逐次记录，含日志与视频链接 | 已有 `releases/2026-11-17/robocurve_allruns.json` |
| RoboChallenge | `robochallenge.ai/api/v2/leaderboard/leaderboard_task_all.json`（486KB） | 任务×模型聚合，30 任务，4 本体 | 直接 JSON，前端为 Vue SPA，接口在 JS 里 |
| RoboArena | `roboarena-api-domain-name.online/api/leaderboard`（7.9KB） | Elo + 标准差 + 对局数，24 策略 | 静态站 `robo-arena.github.io` 只做展示，数据走独立 API 域 |
| RoboTwin 2.0 | `robotwin-platform.github.io/data/robotwin_leaderboard.json`（66KB） | 任务×方法成功率，50 任务，36 方法，每格 100 次 | 静态 JSON，含 leaderboard schema |

RoboChallenge 的任务与本体映射藏在打包 JS 里（`task_id`、`robot_tag`、`task_name` 三元组），已抽成 `raw/robochallenge_task_meta.json`。四类本体的任务分布：ARX5、UR5、W1、ALOHA。

未接入：FlagEval-Robo（`flagevalrobo.baai.ac.cn`，Vue SPA，榜单接口需登录态，未找到公开 JSON）；RoboDojo（`robodojo-benchmark.com`，数据在 `/data/rolloutManifest.generated.json`，7.4MB，下载超时，且内容是视频清单而非成绩）；RoboColiseum（域名不可达，仅见于厂商宣传）。

## 二、各站披露情况

| 榜单 | 单元 | 是否公布每格次数 | 说明 |
|---|---|---|---|
| robocurve | 逐次 run | 是（可从记录数出） | 4,239 条 run |
| RoboChallenge | 任务×模型 | 否（769 格中 0 格写 n） | 只有基准级总回合数 32,980 |
| RoboArena | 策略 | 部分（公布对局数，非每对次数） | 中位 39 局；13/24 策略不足 50 局 |
| RoboTwin 2.0 | 任务×方法 | 是（每格 100 次，协议写明） | 唯一在页面上写明每格次数的榜单 |

这一栏是本次接入最有用的结果：四个榜单里只有一个把"每格多少次"写在明面上。

## 三、两种不需要样本量的检验

**任务符号一致性（RoboChallenge、RoboTwin）**：在同一任务上比两个模型，记谁高。若 A 在 m 个共同任务里有 k 个高于 B，用精确二项检验（H0: p = 0.5）判断这是不是巧合。它检验的是"跨任务方向是否稳定"，不是抽样误差。

**评级差（RoboArena）**：Elo 差与榜单自报标准差比较，`|Δ| > 1.96·sqrt(σa² + σb²)` 记为分得开。这是榜单自报的不确定性，不是对局次数的置信区间。

**合并比例（RoboTwin）**：每格 100 次，把共同任务的成功率取平均，标准误按各格二项方差汇总，`|Δ| > 1.96·SE` 记为分得开。

三种检验的口径都写在 `tools/board_audit.py` 的注释里，可替换。

## 四、结果

| 榜单 | 可比较对 | 分得开 | 不可分辨 | 依据 |
|---|---|---|---|---|
| robocurve（五个基准） | 143 | 57 | 60.1% | 任务聚类 95% 区间 |
| RoboChallenge（Table 30 V2） | 681 | 172 | 74.7% | 任务符号一致性，≥4 共同任务 |
| RoboArena | 276 | 53 | 80.8% | Elo 差 vs 自报标准差 |
| RoboTwin 2.0 | 630 | 601 | 4.6% | 每格 100 次，50 任务合并 |

差异不需要解释成"某些榜单的模型更接近"。RoboTwin 每格 100 次、50 个任务、同一本体，证据密度高，自然分得开；RoboArena 中位 39 局、标准差最大到 176，自然分不开；RoboChallenge 每格次数不公布，只能看方向一致性，而方向一致性本身对差距不敏感。

一句话：不可分辨的比例主要由证据密度决定，不主要由模型强弱决定。这是本档案最想让人接受的一点。

## 五、RoboArena 的两个具体现象

榜首 `j2-vla` 1788 分，但只有 25 局，标准差 106；第四名 `ReDROID-0.0` 1634 分、6 局、标准差 176。两者与中位策略的差距都落在自报不确定性之内。榜单把这类低局数策略与 745 局的 `pi05_droid` 排在同一张表上，读者容易把"名次"读成"能力"。

## 六、复算

```
python3 tools/board_audit.py --raw boards/2026-11-17/raw --out boards/2026-11-17
```

输出：`robochallenge_cells.csv`、`robochallenge_sign_pairs.csv`、`roboarena_board.csv`、`roboarena_pairs.csv`、`robotwin_cells.csv`、`robotwin_pairs.csv`、`board_summary.json`。原始响应与哈希在 `raw/` 与 `board_summary.json` 的 `raw_hashes` 里。

## 七、下一步

RoboTwin 是唯一能直接与 robocurve 比口径的榜单，先把它做成纵向跟踪对象，每月留快照。
RoboChallenge 补抓 `leaderboard_tag_*.json`，把本体内与本体间的对子分开算。
FlagEval-Robo 需要登录态，若要接入，走浏览器会话，不硬猜接口。
RoboDojo 与 RoboColiseum 暂列不可接入，记录原因即可。

## Comparability warning

The undiscernible shares in this directory are not directly comparable across boards:
RoboChallenge uses an exact sign test on shared tasks, RoboArena uses Elo differences
against self-reported standard deviations, RoboTwin uses a pooled two-proportion test,
and the archive's own stratum work uses cluster intervals. A figure such as 74.7% or
4.6% answers "how much of this board's ordering is separable under the test this board
permits", not "how much of robot evaluation is reproducible". Cross-board statements
should quote the method alongside the number.
