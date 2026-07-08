"""
ATRI CF 查分与刷题分析插件 📊
查询 Codeforces 用户信息、Rating、刷题统计，生成可视化图表
支持用户绑定（QQ ↔ CF handle）
"""
import json
import os
import re
import time
import urllib.request
from collections import Counter
from pathlib import Path

from astrbot.api.all import Star, AstrMessageEvent, CommandResult, Plain, Image
from astrbot.core.star.register import register

# ---------- 数据存储 ----------
BIND_DIR = Path("data/plugins/astrbot_plugin_cf_query")
BIND_FILE = BIND_DIR / "bindings.json"


def _load_bindings() -> dict:
    if BIND_FILE.exists():
        with open(BIND_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_bindings(data: dict):
    BIND_DIR.mkdir(parents=True, exist_ok=True)
    with open(BIND_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------- CF API 工具函数 ----------
def _cf_api(url: str) -> dict | None:
    """调用 CF API，返回 dict 或 None"""
    req = urllib.request.Request(url, headers={"User-Agent": "ATRI-CF-Plugin/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        if data.get("status") == "OK":
            return data["result"]
        return None
    except Exception:
        return None


def _query_user_info(handle: str) -> dict | None:
    result = _cf_api(f"https://codeforces.com/api/user.info?handles={handle}")
    if result and len(result) > 0:
        return result[0]
    return None


def _query_rating_history(handle: str) -> list:
    result = _cf_api(f"https://codeforces.com/api/user.rating?handle={handle}")
    return result if result else []


def _query_submissions(handle: str, count: int = 200) -> list:
    result = _cf_api(
        f"https://codeforces.com/api/user.status?handle={handle}&from=1&count={count}"
    )
    return result if result else []


def _analyze_submissions(submissions: list) -> dict:
    """分析提交记录，返回统计信息"""
    total = len(submissions)
    ac = sum(1 for s in submissions if s.get("verdict") == "OK")
    wa = sum(1 for s in submissions if "WRONG_ANSWER" in s.get("verdict", ""))
    tle = sum(1 for s in submissions if "TIME_LIMIT_EXCEEDED" in s.get("verdict", ""))
    ce = sum(1 for s in submissions if "COMPILATION_ERROR" in s.get("verdict", ""))
    other = total - ac - wa - tle - ce

    # 按 rating 统计通过题数（去重）
    rating_counter = Counter()
    tag_counter = Counter()
    solved = set()
    ac_records = []
    for s in submissions:
        if s.get("verdict") == "OK":
            pid = f"{s['problem'].get('contestId', '')}{s['problem']['index']}"
            rtg = s["problem"].get("rating", 0)
            if pid not in solved:
                solved.add(pid)
                rating_counter[rtg] += 1
                for t in s["problem"].get("tags", []):
                    tag_counter[t] += 1
                ac_records.append({
                    "pid": pid,
                    "name": s["problem"]["name"],
                    "rating": rtg,
                    "tags": s["problem"].get("tags", []),
                    "time": s.get("creationTimeSeconds", 0),
                })

    # 最近 10 条 AC
    ac_records.sort(key=lambda x: x["time"], reverse=True)
    recent_ac = ac_records[:10]

    return {
        "total": total,
        "ac": ac,
        "wa": wa,
        "tle": tle,
        "ce": ce,
        "other": other,
        "solved_count": len(solved),
        "rating_dist": dict(sorted(rating_counter.items())),
        "tag_dist": dict(tag_counter.most_common(10)),
        "recent_ac": recent_ac,
    }


def _generate_rating_chart(handle: str, history: list, save_path: str) -> bool:
    """生成 Rating 变化柱状图"""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return False

    if not history:
        return False

    dates = []
    ratings = []
    old_ratings = []
    changes = []
    colors = []

    for c in history:
        ts = time.strftime("%m/%d", time.localtime(c["ratingUpdateTimeSeconds"]))
        dates.append(f"#{c['contestId']}\n{ts}")
        old_ratings.append(c["oldRating"])
        ratings.append(c["newRating"])
        ch = c["newRating"] - c["oldRating"]
        changes.append(ch)
        colors.append("#3eb86b" if ch >= 0 else "#e8785a")

    fig, ax = plt.subplots(figsize=(10, 5.5))
    fig.patch.set_facecolor("#f8f4f0")
    ax.set_facecolor("#ffffff")

    x = np.arange(len(dates))
    bars = ax.bar(x, ratings, width=0.5, color=colors, edgecolor="white", linewidth=1.5, zorder=3)
    ax.bar(x, old_ratings, width=0.5, color="#e0d0c0", alpha=0.4, edgecolor="white", linewidth=1.5, zorder=2)

    for i, (bar, rating, change) in enumerate(zip(bars, ratings, changes)):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 15,
                str(rating), ha="center", va="bottom", fontsize=13, fontweight="bold", color="#333")
        sign = "+" if change > 0 else ""
        clr = "#3eb86b" if change > 0 else "#e8785a"
        mid_y = old_ratings[i] + (rating - old_ratings[i]) / 2
        ax.annotate(f"{sign}{change}", xy=(bar.get_x() + bar.get_width() / 2, mid_y),
                    fontsize=11, fontweight="bold", color="white", ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor=clr, edgecolor="none", alpha=0.85))

    ax.set_xticks(x)
    ax.set_xticklabels(dates, fontsize=10)
    ax.set_title(f"{handle} · Rating Changes", fontsize=17, fontweight="bold", color="#d06040", pad=15)
    ax.set_ylabel("Rating", fontsize=12, fontweight="bold", color="#555")
    ax.set_ylim(0, max(ratings) * 1.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#ddd")
    ax.spines["bottom"].set_color("#ddd")
    ax.tick_params(colors="#888")
    ax.grid(axis="y", alpha=0.3, color="#ddd", zorder=0)

    plt.tight_layout()
    fig.savefig(save_path, dpi=180, bbox_inches="tight", facecolor="#f8f4f0")
    plt.close()
    return True


def _generate_problem_chart(handle: str, rating_dist: dict, save_path: str) -> bool:
    """生成解题难度分布柱状图"""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return False

    if not rating_dist:
        return False

    labels_map = {0: "Unrated"}
    labels = []
    values = []
    colors = []
    palette = ["#b0b0b0", "#8bc34a", "#4caf50", "#26a69a", "#00bcd4", "#2196f3", "#7e57c2", "#9c27b0"]

    for i, (rating, cnt) in enumerate(sorted(rating_dist.items())):
        lbl = labels_map.get(rating, str(rating))
        labels.append(lbl)
        values.append(cnt)
        colors.append(palette[i % len(palette)])

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#f8f4f0")
    ax.set_facecolor("#ffffff")

    x = np.arange(len(labels))
    bars = ax.bar(x, values, width=0.55, color=colors, edgecolor="white", linewidth=1.5, zorder=3)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                str(val), ha="center", va="bottom", fontsize=15, fontweight="bold", color="#333")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=12, fontweight="bold")
    ax.set_title(f"{handle} · Problem Ratings", fontsize=17, fontweight="bold", color="#d06040", pad=15)
    ax.set_ylabel("Problems Solved", fontsize=12, fontweight="bold", color="#555")
    ax.set_ylim(0, max(values) * 1.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#ddd")
    ax.spines["bottom"].set_color("#ddd")
    ax.tick_params(colors="#888")
    ax.grid(axis="y", alpha=0.3, color="#ddd", zorder=0)

    plt.tight_layout()
    fig.savefig(save_path, dpi=180, bbox_inches="tight", facecolor="#f8f4f0")
    plt.close()
    return True


def _generate_tag_chart(handle: str, tag_dist: dict, save_path: str) -> bool:
    """生成标签分布饼图"""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False

    if not tag_dist:
        return False

    labels = list(tag_dist.keys())
    values = list(tag_dist.values())
    colors = ["#e8785a", "#f0a030", "#4a90d9", "#3eb86b", "#9b59b6",
              "#1abc9c", "#e74c3c", "#3498db", "#f39c12", "#2ecc71", "#95a5a6"]

    fig, ax = plt.subplots(figsize=(8, 6))
    fig.patch.set_facecolor("#f8f4f0")

    wedges, texts, autotexts = ax.pie(
        values, labels=None, autopct="%1.0f%%",
        startangle=90, pctdistance=0.78,
        colors=colors[:len(labels)],
        wedgeprops=dict(width=0.4, edgecolor="white", linewidth=2),
        textprops=dict(fontsize=11, fontweight="bold"),
    )

    ax.set_title(f"{handle} · Tags Distribution", fontsize=17, fontweight="bold", color="#d06040", pad=20)
    ax.legend(wedges, [f"{l} ({v})" for l, v in zip(labels, values)],
              title="Tags", title_fontsize=12,
              loc="center left", bbox_to_anchor=(1, 0.5),
              fontsize=10, framealpha=0.9)

    plt.tight_layout(rect=[0, 0.03, 0.75, 0.97])
    fig.savefig(save_path, dpi=180, bbox_inches="tight", facecolor="#f8f4f0")
    plt.close()
    return True


def _combine_charts(chart_paths: list, save_path: str) -> bool:
    """合并多张图为一张大图"""
    try:
        from PIL import Image
    except ImportError:
        return False

    imgs = []
    for p in chart_paths:
        if os.path.exists(p):
            imgs.append(Image.open(p))

    if not imgs:
        return False

    width = max(img.width for img in imgs)
    resized = []
    for img in imgs:
        ratio = width / img.width
        resized.append(img.resize((width, int(img.height * ratio)), Image.LANCZOS))

    total_height = sum(img.height for img in resized) + 10 * (len(resized) - 1)
    combined = Image.new("RGB", (width, total_height), "#f8f4f0")
    y = 0
    for img in resized:
        combined.paste(img, (0, y))
        y += img.height + 10

    combined.save(save_path, quality=92)
    return True


def _build_text_report(handle: str, user_info: dict, history: list, analysis: dict) -> str:
    """构建文本分析报告"""
    rating = user_info.get("rating", 0)
    max_rating = user_info.get("maxRating", 0)
    rank = user_info.get("rank", "unrated")
    max_rank = user_info.get("maxRank", "unrated")

    total_contests = len(history)
    wins = sum(1 for c in history if c["newRating"] > c["oldRating"])
    losses = sum(1 for c in history if c["newRating"] < c["oldRating"])

    best_rank = min((c["rank"] for c in history), default="-")

    s = analysis
    ac_rate = f"{s['ac'] / s['total'] * 100:.1f}%" if s["total"] > 0 else "-"

    lines = [
        f"📊 CF Profile: {handle}",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"Rating: {rating} ({rank.title()})",
        f"最高: {max_rating} ({max_rank.title()})",
        f"参赛: {total_contests}场 | 涨{win if (win := wins) else 0}掉{loss if (loss := losses) else 0}",
        f"最佳排名: #{best_rank}",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"📝 刷题统计",
        f"提交: {s['total']} | AC: {s['ac']} | AC率: {ac_rate}",
        f"通过不同题目: {s['solved_count']}道",
    ]

    if s["rating_dist"]:
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        lines.append("🎯 难度分布:")
        for r, c in sorted(s["rating_dist"].items()):
            lbl = "Unrated" if r == 0 else str(r)
            bar = "█" * c
            lines.append(f"  {lbl:>7}: {bar} {c}")

    if s["recent_ac"]:
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        lines.append("🔥 最近AC:")
        for a in s["recent_ac"][:5]:
            rtg = f"[{a['rating']}]" if a["rating"] else "[?]"
            lines.append(f"  ✅ {a['pid']} {rtg} {a['name']}")

    return "\n".join(lines)


# ---------- 插件主类 ----------
class CFQueryPlugin(Star):
    def __init__(self, context=None, config: dict = None):
        super().__init__(context, config)
        self.config = config or {}
        self.temp_dir = Path("/AstrBot/data/temp")

    # ========== 用户绑定 ==========
    @register("cfbind", "绑定CF账号到QQ", "cfbind <CF用户名> 或 cfbind 用户名")
    async def cf_bind(self, event: AstrMessageEvent):
        """绑定CF账号"""
        args = event.get_args()
        if not args:
            yield CommandResult().message("❌ 用法: cfbind <CF用户名>")
            return

        handle = args[0].strip()
        # 验证handle是否存在
        info = _query_user_info(handle)
        if not info:
            yield CommandResult().message(f"❌ CF用户 {handle} 不存在，请检查用户名")
            return

        uid = str(event.get_sender_id())
        bindings = _load_bindings()
        bindings[uid] = {
            "handle": handle,
            "bind_time": int(time.time()),
            "rating": info.get("rating", 0),
        }
        _save_bindings(bindings)

        rating = info.get("rating", 0)
        rank = info.get("rank", "unrated").title()
        yield CommandResult().message(f"✅ 绑定成功！\n{handle} | Rating: {rating} ({rank})")

    @register("cfunbind", "解绑CF账号", "cfunbind")
    async def cf_unbind(self, event: AstrMessageEvent):
        """解绑CF账号"""
        uid = str(event.get_sender_id())
        bindings = _load_bindings()
        if uid not in bindings:
            yield CommandResult().message("❌ 你还没有绑定CF账号")
            return
        handle = bindings[uid]["handle"]
        del bindings[uid]
        _save_bindings(bindings)
        yield CommandResult().message(f"✅ 已解绑 {handle}")

    @register("cfwho", "查看已绑定的CF账号", "cfwho")
    async def cf_who(self, event: AstrMessageEvent):
        """查看自己的绑定"""
        uid = str(event.get_sender_id())
        bindings = _load_bindings()
        if uid not in bindings:
            yield CommandResult().message("❌ 你还没有绑定CF账号，使用 cfbind <用户名> 绑定")
            return
        info = bindings[uid]
        yield CommandResult().message(f"🔗 已绑定: {info['handle']} (绑定时间: {time.strftime('%Y-%m-%d', time.localtime(info['bind_time']))})")

    # ========== CF 查询 ==========
    @register("cf", "查询CF用户信息并生成报告", "cf <用户名> 或 cf（查已绑定用户）")
    async def cf_query(self, event: AstrMessageEvent):
        """查询CF用户信息"""
        args = event.get_args()

        # 确定要查的handle
        handle = None
        if args:
            handle = args[0].strip()
        else:
            # 尝试从绑定中获取
            uid = str(event.get_sender_id())
            bindings = _load_bindings()
            if uid in bindings:
                handle = bindings[uid]["handle"]

        if not handle:
            yield CommandResult().message("❌ 用法: cf <用户名> 或先用 cfbind 绑定后直接 cf")
            return

        yield CommandResult().message(f"🔍 正在查询 {handle} 的数据...")

        # 并行获取数据
        user_info = _query_user_info(handle)
        if not user_info:
            yield CommandResult().message(f"❌ 查询失败，用户 {handle} 不存在或网络错误")
            return

        history = _query_rating_history(handle)
        submissions = _query_submissions(handle, 200)
        analysis = _analyze_submissions(submissions)

        # 生成文本报告
        text_report = _build_text_report(handle, user_info, history, analysis)
        yield CommandResult().message(text_report)

        # 生成图表
        timestamp = int(time.time())
        chart_files = []
        style = self.config.get("default_chart_style", "combined")

        # Rating柱状图
        rating_chart = str(self.temp_dir / f"cf_rating_{handle}_{timestamp}.png")
        if _generate_rating_chart(handle, history, rating_chart):
            chart_files.append(rating_chart)

        # 难度柱状图
        problem_chart = str(self.temp_dir / f"cf_problems_{handle}_{timestamp}.png")
        if _generate_problem_chart(handle, analysis["rating_dist"], problem_chart):
            chart_files.append(problem_chart)

        # 标签饼图
        tag_chart = str(self.temp_dir / f"cf_tags_{handle}_{timestamp}.png")
        if _generate_tag_chart(handle, analysis["tag_dist"], tag_chart):
            chart_files.append(tag_chart)

        if not chart_files:
            yield CommandResult().message("📊 数据不足以生成图表")
            return

        if style == "combined" and len(chart_files) >= 2:
            combined_path = str(self.temp_dir / f"cf_combined_{handle}_{timestamp}.png")
            if _combine_charts(chart_files, combined_path):
                yield CommandResult().chain().image(combined_path)
                return

        # 分开发送
        for cf in chart_files:
            yield CommandResult().chain().image(cf)

    @register("cftop", "查看群内已绑定用户的CF排名", "cftop")
    async def cf_top(self, event: AstrMessageEvent):
        """查看群内CF排名"""
        bindings = _load_bindings()
        if not bindings:
            yield CommandResult().message("📭 还没有人绑定CF账号")
            return

        # 刷新所有已绑用户的rating
        users = []
        for uid, info in bindings.items():
            handle = info["handle"]
            fresh = _query_user_info(handle)
            rating = fresh.get("rating", 0) if fresh else info.get("rating", 0)
            users.append((handle, rating, uid))
            time.sleep(0.5)  # CF API限速

        users.sort(key=lambda x: x[1], reverse=True)

        lines = ["🏆 群内CF排行榜", "━━━━━━━━━━━━━━"]
        rank_emoji = ["🥇", "🥈", "🥉"]
        for i, (handle, rating, uid) in enumerate(users[:10]):
            emo = rank_emoji[i] if i < 3 else f"{i+1}."
            lines.append(f"{emo} {handle} — {rating}")

        yield CommandResult().message("\n".join(lines))
