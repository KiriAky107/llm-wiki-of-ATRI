"""
ATRI CF 查分与刷题分析插件 📊 v1.0
查询 Codeforces 用户信息、Rating、刷题统计
支持用户绑定、可视化图表、分析报告
"""
import json
import os
import re
import time
import urllib.request
from collections import Counter
from pathlib import Path

from astrbot.api.all import *
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register

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
    """调用 CF API，返回 result 或 None"""
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
                    "time": s.get("creationTimeSeconds", 0),
                })

    ac_records.sort(key=lambda x: x["time"], reverse=True)

    return {
        "total": total,
        "ac": ac,
        "wa": wa,
        "tle": tle,
        "ce": ce,
        "solved_count": len(solved),
        "rating_dist": dict(sorted(rating_counter.items())),
        "tag_dist": dict(tag_counter.most_common(10)),
        "recent_ac": ac_records[:10],
    }


def _generate_rating_chart(handle: str, history: list, save_path: str) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return False
    if not history:
        return False
    dates, ratings, old_ratings, changes, colors = [], [], [], [], []
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
    for i, (bar, r, ch) in enumerate(zip(bars, ratings, changes)):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()+15, str(r),
                ha="center", va="bottom", fontsize=13, fontweight="bold", color="#333")
        sign = "+" if ch > 0 else ""
        clr = "#3eb86b" if ch > 0 else "#e8785a"
        mid = old_ratings[i] + (r - old_ratings[i]) / 2
        ax.annotate(f"{sign}{ch}", xy=(bar.get_x()+bar.get_width()/2, mid),
                    fontsize=11, fontweight="bold", color="white", ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor=clr, edgecolor="none", alpha=0.85))
    ax.set_xticks(x)
    ax.set_xticklabels(dates, fontsize=10)
    ax.set_title(f"{handle} · Rating Changes", fontsize=17, fontweight="bold", color="#d06040", pad=15)
    ax.set_ylabel("Rating", fontsize=12, fontweight="bold", color="#555")
    ax.set_ylim(0, max(ratings) * 1.3)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]:
        ax.spines[s].set_color("#ddd")
    ax.tick_params(colors="#888")
    ax.grid(axis="y", alpha=0.3, color="#ddd", zorder=0)
    plt.tight_layout()
    fig.savefig(save_path, dpi=180, bbox_inches="tight", facecolor="#f8f4f0")
    plt.close()
    return True


def _generate_problem_chart(handle: str, rating_dist: dict, save_path: str) -> bool:
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
    labels, values, colors = [], [], []
    palette = ["#b0b0b0", "#8bc34a", "#4caf50", "#26a69a", "#00bcd4", "#2196f3", "#7e57c2", "#9c27b0"]
    for i, (rtg, cnt) in enumerate(sorted(rating_dist.items())):
        labels.append(labels_map.get(rtg, str(rtg)))
        values.append(cnt)
        colors.append(palette[i % len(palette)])
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#f8f4f0")
    ax.set_facecolor("#ffffff")
    x = np.arange(len(labels))
    bars = ax.bar(x, values, width=0.55, color=colors, edgecolor="white", linewidth=1.5, zorder=3)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()+0.1, str(val),
                ha="center", va="bottom", fontsize=15, fontweight="bold", color="#333")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=12, fontweight="bold")
    ax.set_title(f"{handle} · Problem Ratings", fontsize=17, fontweight="bold", color="#d06040", pad=15)
    ax.set_ylabel("Problems Solved", fontsize=12, fontweight="bold", color="#555")
    ax.set_ylim(0, max(values) * 1.3)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]:
        ax.spines[s].set_color("#ddd")
    ax.tick_params(colors="#888")
    ax.grid(axis="y", alpha=0.3, color="#ddd", zorder=0)
    plt.tight_layout()
    fig.savefig(save_path, dpi=180, bbox_inches="tight", facecolor="#f8f4f0")
    plt.close()
    return True


def _generate_tag_chart(handle: str, tag_dist: dict, save_path: str) -> bool:
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
    wedges, texts, autotexts = ax.pie(values, labels=None, autopct="%1.0f%%",
                                       startangle=90, pctdistance=0.78,
                                       colors=colors[:len(labels)],
                                       wedgeprops=dict(width=0.4, edgecolor="white", linewidth=2),
                                       textprops=dict(fontsize=11, fontweight="bold"))
    ax.set_title(f"{handle} · Tags", fontsize=17, fontweight="bold", color="#d06040", pad=20)
    ax.legend(wedges, [f"{l} ({v})" for l, v in zip(labels, values)],
              title="Tags", title_fontsize=12,
              loc="center left", bbox_to_anchor=(1, 0.5),
              fontsize=10, framealpha=0.9)
    plt.tight_layout(rect=[0, 0.03, 0.75, 0.97])
    fig.savefig(save_path, dpi=180, bbox_inches="tight", facecolor="#f8f4f0")
    plt.close()
    return True


def _combine_charts(paths: list, save_path: str) -> bool:
    try:
        from PIL import Image
    except ImportError:
        return False
    imgs = [Image.open(p) for p in paths if os.path.exists(p)]
    if not imgs:
        return False
    width = max(img.width for img in imgs)
    resized = []
    for img in imgs:
        ratio = width / img.width
        resized.append(img.resize((width, int(img.height * ratio)), Image.LANCZOS))
    total_h = sum(img.height for img in resized) + 10 * (len(resized) - 1)
    combined = Image.new("RGB", (width, total_h), "#f8f4f0")
    y = 0
    for img in resized:
        combined.paste(img, (0, y))
        y += img.height + 10
    combined.save(save_path, quality=92)
    return True


def _build_text_report(handle: str, user_info: dict, history: list, analysis: dict) -> str:
    """构建文本分析报告"""
    rating = user_info.get("rating", 0)
    max_r = user_info.get("maxRating", 0)
    rank = user_info.get("rank", "unrated").title()
    wins = sum(1 for c in history if c["newRating"] > c["oldRating"])
    losses = sum(1 for c in history if c["newRating"] < c["oldRating"])
    best_rank = min((c["rank"] for c in history), default="-")
    s = analysis
    ac_rate = f"{s['ac'] / s['total'] * 100:.1f}%" if s["total"] > 0 else "-"
    lines = [
        f"📊 CF Profile: {handle}",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"Rating: {rating} ({rank.title()})",
        f"最高: {max_r} ({user_info.get('maxRank', 'unrated').title()})",
        f"参赛: {len(history)}场 | 涨{wins}掉{losses}",
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
            lines.append(f"  {lbl:>7}: {'█'*c} {c}")
    if s["recent_ac"]:
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        lines.append("🔥 最近AC:")
        for a in s["recent_ac"][:5]:
            rtg = f"[{a['rating']}]" if a["rating"] else "[?]"
            lines.append(f"  ✅ {a['pid']} {rtg} {a['name']}")
    return "\n".join(lines)


def _build_analysis_prompt(handle: str, user_info: dict, history: list, analysis: dict) -> str:
    """构建AI分析用的prompt"""
    rating = user_info.get("rating", 0)
    max_r = user_info.get("maxRating", 0)
    rank = user_info.get("rank", "unrated").title()
    total_contests = len(history)
    wins = sum(1 for c in history if c["newRating"] > c["oldRating"])
    losses = sum(1 for c in history if c["newRating"] < c["oldRating"])
    best_rank = min((c["rank"] for c in history), default="无")
    ac_rate = f"{analysis['ac']/analysis['total']*100:.1f}%" if analysis["total"] > 0 else "无数据"
    recent = analysis["recent_ac"][:5]
    recent_str = "\n".join(f"  - {a['pid']} [{a['rating']}] {a['name']}" for a in recent) if recent else "  无"
    dist_parts = []
    for r, c in sorted(analysis["rating_dist"].items()):
        lbl = "Unrated" if r == 0 else str(r)
        dist_parts.append(f"{lbl}: {c}题")
    dist_str = ", ".join(dist_parts)
    return f"""请根据以下Codeforces用户数据，生成一段简短、有温度的分析与建议（50~100字，中文，语气像朋友聊天一样自然，不要过于正式）：

用户：{handle}
当前Rating：{rating}（{rank}）
最高Rating：{max_r}
参赛：{total_contests}场（涨{wins}掉{losses}）
最佳排名：#{best_rank}
AC率：{ac_rate}
通过题目数：{analysis['solved_count']}道
难度分布：{dist_str}
最近AC：
{recent_str}

请从以下角度给出简短分析：
1. 当前水平总结（一句话）
2. 优势和不足
3. 后续练习建议"""


# ---------- 主插件类 ----------
@register("astrbot_plugin_cf_query", "ATRI (YHN-04B-009)", "CF 查分与刷题分析，支持绑定、图表、报告", "1.0.0", "https://gitea.kronecker.cc/Kronecker/ATRI-NOTES")
class CFQueryPlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context, config)
        self.config = config or {}
        self.temp_dir = Path("/AstrBot/data/temp")

    # ========== 绑定 ==========
    @filter.command("cfbind")
    async def cf_bind(self, event: AstrMessageEvent, handle: str = None):
        """绑定CF账号：cfbind <用户名>"""
        if not handle:
            yield event.plain_result("❌ 用法: cfbind <CF用户名>")
            return
        handle = handle.strip()
        info = _query_user_info(handle)
        if not info:
            yield event.plain_result(f"❌ CF用户 {handle} 不存在，请检查用户名")
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
        yield event.plain_result(f"✅ 绑定成功！\n{handle} | Rating: {rating} ({rank})")

    @filter.command("cfunbind")
    async def cf_unbind(self, event: AstrMessageEvent):
        """解绑CF账号"""
        uid = str(event.get_sender_id())
        bindings = _load_bindings()
        if uid not in bindings:
            yield event.plain_result("❌ 你还没有绑定CF账号")
            return
        yield event.plain_result(f"✅ 已解绑 {bindings[uid]['handle']}")
        del bindings[uid]
        _save_bindings(bindings)

    @filter.command("cfwho")
    async def cf_who(self, event: AstrMessageEvent):
        """查看绑定信息"""
        uid = str(event.get_sender_id())
        bindings = _load_bindings()
        if uid not in bindings:
            yield event.plain_result("❌ 你还没有绑定CF账号，使用 cfbind <用户名> 绑定")
            return
        info = bindings[uid]
        t = time.strftime('%Y-%m-%d', time.localtime(info['bind_time']))
        yield event.plain_result(f"🔗 已绑定: {info['handle']} ({t})")

    @filter.command("cftop")
    async def cf_top(self, event: AstrMessageEvent):
        """群内CF排行榜"""
        bindings = _load_bindings()
        if not bindings:
            yield event.plain_result("📭 还没有人绑定CF账号")
            return
        users = []
        for uid, info in bindings.items():
            handle = info["handle"]
            fresh = _query_user_info(handle)
            rating = fresh.get("rating", 0) if fresh else info.get("rating", 0)
            users.append((handle, rating))
            time.sleep(0.5)
        users.sort(key=lambda x: x[1], reverse=True)
        lines = ["🏆 群内CF排行榜", "━━━━━━━━━━━━━━"]
        emojis = ["🥇", "🥈", "🥉"]
        for i, (handle, rating) in enumerate(users[:10]):
            emo = emojis[i] if i < 3 else f"{i+1}."
            lines.append(f"{emo} {handle} — {rating}")
        yield event.plain_result("\n".join(lines))

    # ========== 主查询 ==========
    @filter.command("cf")
    async def cf_query(self, event: AstrMessageEvent, handle: str = None):
        """查询CF用户：cf <用户名> 或 cf（查已绑定）"""
        if not handle:
            uid = str(event.get_sender_id())
            bindings = _load_bindings()
            if uid in bindings:
                handle = bindings[uid]["handle"]
        if not handle:
            yield event.plain_result("❌ 用法: cf <用户名> 或先用 cfbind 绑定后直接 cf")
            return

        yield event.plain_result(f"🔍 正在查询 {handle} 的数据...")

        user_info = _query_user_info(handle)
        if not user_info:
            yield event.plain_result(f"❌ 查询失败，用户 {handle} 不存在或网络异常")
            return

        history = _query_rating_history(handle)
        submissions = _query_submissions(handle, 200)
        analysis = _analyze_submissions(submissions)

        # --- 文本报告 ---
        rating = user_info.get("rating", 0)
        max_r = user_info.get("maxRating", 0)
        rank = user_info.get("rank", "unrated").title()
        wins = sum(1 for c in history if c["newRating"] > c["oldRating"])
        losses = sum(1 for c in history if c["newRating"] < c["oldRating"])
        best_rank = min((c["rank"] for c in history), default="-")
        ac_rate = f"{analysis['ac']/analysis['total']*100:.1f}%" if analysis["total"] > 0 else "-"

        lines = [
            f"📊 CF Profile: {handle}",
            f"━━━━━━━━━━━━━━━━━━━━",
            f"Rating: {rating} ({rank}) | 最高: {max_r}",
            f"参赛: {len(history)}场 | 涨{wins}掉{losses} | 最佳排名: #{best_rank}",
            f"━━━━━━━━━━━━━━━━━━━━",
            f"提交: {analysis['total']} | AC: {analysis['ac']} | AC率: {ac_rate}",
            f"通过不同题目: {analysis['solved_count']}道",
        ]
        if analysis["rating_dist"]:
            lines.append("━━━━━━━━━━━━━━━━━━━━")
            lines.append("🎯 难度分布:")
            for r, c in sorted(analysis["rating_dist"].items()):
                lbl = "Unrated" if r == 0 else str(r)
                lines.append(f"  {lbl:>7}: {'█'*c} {c}")
        if analysis["recent_ac"]:
            lines.append("━━━━━━━━━━━━━━━━━━━━")
            lines.append("🔥 最近AC:")
            for a in analysis["recent_ac"][:5]:
                rtg = f"[{a['rating']}]" if a["rating"] else "[?]"
                lines.append(f"  ✅ {a['pid']} {rtg} {a['name']}")
        text_report = "\n".join(lines)

        # --- 图表 ---
        ts = int(time.time())
        charts = []
        rc = str(self.temp_dir / f"cf_rating_{handle}_{ts}.png")
        if _generate_rating_chart(handle, history, rc):
            charts.append(rc)
        pc = str(self.temp_dir / f"cf_problems_{handle}_{ts}.png")
        if _generate_problem_chart(handle, analysis["rating_dist"], pc):
            charts.append(pc)
        tc = str(self.temp_dir / f"cf_tags_{handle}_{ts}.png")
        if _generate_tag_chart(handle, analysis["tag_dist"], tc):
            charts.append(tc)

        style = self.config.get("default_chart_style", "combined")
        if charts:
            # 先发图表
            if style == "combined" and len(charts) >= 2:
                combined = str(self.temp_dir / f"cf_combined_{handle}_{ts}.png")
                if _combine_charts(charts, combined):
                    yield event.image_result(combined)
            else:
                for c in charts:
                    yield event.image_result(c)

            # 再用AI生成分析文本
            try:
                analysis_prompt = _build_analysis_prompt(handle, user_info, history, analysis)
                provider_id = self.context.get_current_chat_provider_id(event.unified_msg_origin)
                llm_resp = await self.context.llm_generate(
                    chat_provider_id=provider_id,
                    prompt=analysis_prompt,
                )
                if llm_resp and llm_resp.completion_text:
                    yield event.plain_result(llm_resp.completion_text)
            except Exception as e:
                # AI分析失败时打印错误但不影响主流程
                yield event.plain_result(f"⚠️ AI分析异常: {type(e).__name__}: {e}")
            return

        # 没有图表时才发文本报告
        yield event.plain_result(text_report)
