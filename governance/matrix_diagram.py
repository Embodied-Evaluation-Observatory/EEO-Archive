"""Render the module/timeline/band diagram used in the client-facing positioning page.

Two timelines (ex-ante, post-hoc) on one baseline; four module columns; two horizontal
bands that visibly cross every column. Text stays short: the diagram argues structure,
the document carries detail.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, Rectangle

FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
fm.fontManager.addfont(FONT)
fm.fontManager.addfont(FONT_B)
plt.rcParams["font.family"] = "Noto Sans CJK SC"
plt.rcParams["axes.unicode_minus"] = False

INK, MID = "#1f2933", "#5b6b7c"
BLUE, BLUE_L = "#2f5d8a", "#cfdced"
GREY_L = "#dcdfe3"

fig, ax = plt.subplots(figsize=(14.2, 7.6), dpi=200)
ax.set_xlim(0, 16)
ax.set_ylim(0, 9.2)
ax.axis("off")

BX0, BX1 = 0.4, 15.3
J_LO, J_HI = 5.20, 6.70
D_LO, D_HI = 2.45, 3.95

xs = [4.85, 7.65, 10.45, 13.25]
W, H, Y0 = 2.35, 4.55, 2.42
TOP = Y0 + H

# boxes first, bands over them (translucent) so the crossing is visible inside each column
modules = [
    ("样本预算", "多重校正后的\n最小可辨识差异", "预算表\n+ 分级 + 收据"),
    ("过程证据核验", "字段与声称\n口径同一", "PEV 单\n三态 + 未核清单"),
    ("数据体检", "ρ 按层报告\n不跨域借用", "体检报告\n+ 派生表哈希"),
    ("复现核验", "同任务集\n同提示 同判据", "复现记录\n+ 容差"),
]
for x, (name, jtxt, dtxt) in zip(xs, modules):
    ax.add_patch(FancyBboxPatch((x - W / 2, Y0), W, H,
                                boxstyle="round,pad=0.02,rounding_size=0.10",
                                facecolor="white", edgecolor=BLUE, lw=1.3, zorder=2))

# bands drawn above the boxes, below the text
ax.add_patch(Rectangle((BX0, J_LO), BX1 - BX0, J_HI - J_LO,
                       facecolor=BLUE_L, alpha=0.55, edgecolor="none", zorder=2.5))
ax.add_patch(Rectangle((BX0, D_LO), BX1 - BX0, D_HI - D_LO,
                       facecolor=GREY_L, alpha=0.55, edgecolor="none", zorder=2.5))
for y in (J_LO, J_HI):
    ax.plot([BX0, BX1], [y, y], color=BLUE, lw=0.9, alpha=0.55, zorder=2.6)
for y in (D_LO, D_HI):
    ax.plot([BX0, BX1], [y, y], color=MID, lw=0.9, alpha=0.4, zorder=2.6)

# left labels, clear of the first column
ax.text(0.45, J_HI + 0.18, "判据层", fontsize=14, color=BLUE, weight="bold")
ax.text(0.45, J_HI - 0.22, "这两个数字\n能不能比？", fontsize=10, color=BLUE, va="top", linespacing=1.5)
ax.text(0.45, D_HI + 0.18, "交付层", fontsize=14, color=MID, weight="bold")
ax.text(0.45, D_HI - 0.22, "交付物长什么\n样、几级、\n有没有凭证？", fontsize=10, color=MID, va="top", linespacing=1.5)

# module name in the white gap between bands, criterion above, deliverable below
for x, (name, jtxt, dtxt) in zip(xs, modules):
    ax.text(x, 4.57, f"M{modules.index((name, jtxt, dtxt)) + 1}", ha="center", va="center",
            fontsize=9, color=MID, zorder=3)
    ax.text(x, 4.25, name, ha="center", va="center", fontsize=12, color=INK,
            weight="bold", zorder=3)
    ax.text(x, 6.05, jtxt, ha="center", va="center", fontsize=9.6, color=BLUE, zorder=3)
    ax.text(x, 3.20, dtxt, ha="center", va="center", fontsize=9.6, color=MID, zorder=3)

# two timelines
ax.annotate("", xy=(8.30, 1.58), xytext=(1.60, 1.58),
            arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.5))
ax.annotate("", xy=(14.95, 1.58), xytext=(8.95, 1.58),
            arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.5))
ax.plot([8.62, 8.62], [1.05, 7.85], ls=(0, (4, 3)), color=MID, lw=1.0, alpha=0.7, zorder=1)

ax.text(1.60, 1.18, "事前", fontsize=10.5, color=INK)
ax.text(4.85, 1.18, "事中", fontsize=10.5, color=INK, ha="center")
ax.text(10.45, 1.18, "投稿前", fontsize=10.5, color=INK, ha="center")
ax.text(14.95, 1.18, "发表后", fontsize=10.5, color=INK, ha="right")

ax.text(6.25, 7.16, "嵌入式 · 预防性", fontsize=11, color=BLUE, weight="bold", ha="center")
ax.text(11.85, 7.16, "事后 · 可独立交付", fontsize=11, color=MID, weight="bold", ha="center")
ax.text(8.62, 7.86, "开跑 → 收工", fontsize=9.5, color=MID, ha="center")

# the ex-ante constraint, as a caption strip under both ex-ante columns
ax.add_patch(Rectangle((1.55, 0.28), (8.30 - 1.55), 0.62, facecolor="none",
                       edgecolor=BLUE, lw=1.0, ls=(0, (2, 2)), zorder=1))
ax.text((1.55 + 8.30) / 2, 0.59,
        "时点约束 = 过程元数据须当时埋点：seed / 初始状态摘要 / 终止原因 / 评分方式 / 重跑与替换标记",
        ha="center", va="center", fontsize=8.6, color=BLUE)

ax.text(1.55, 8.95, "四个模块，两条时间轴，两条横切带", fontsize=16, color=INK, weight="bold")
ax.text(1.55, 8.52, "每个模块都同时穿过两带；前两模块只在事前/事中有力，后两模块事后即可独立交付。",
        fontsize=9.6, color=MID)

plt.tight_layout(pad=0.3)
OUT = "governance/matrix-diagram"
fig.savefig(OUT + ".png", bbox_inches="tight", facecolor="white")
fig.savefig(OUT + ".svg", bbox_inches="tight", facecolor="white")
print("written", OUT)
