from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"C:\Users\lfaf-test\Documents\测试")
OUT = ROOT / "outputs" / "skill-flowcharts"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1800, 1100


def font(size, bold=False):
    candidates = [
        r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


F_TITLE = font(48, True)
F_SUB = font(25)
F_HEAD = font(26, True)
F_BODY = font(20)
F_SMALL = font(18)

COLORS = {
    "ink": "#121212",
    "muted": "#5F6368",
    "bg": "#FFFFFF",
    "panel": "#F3F5F8",
    "line": "#C9D0D8",
    "blue": "#1F6FEB",
    "green": "#238636",
    "orange": "#E85D2A",
    "amber": "#A66A00",
    "purple": "#6F42C1",
    "red": "#B42318",
    "black": "#171717",
}


def wrap(draw, text, font_obj, width):
    lines = []
    for paragraph in text.split("\n"):
        current = ""
        for ch in paragraph:
            candidate = current + ch
            if draw.textbbox((0, 0), candidate, font=font_obj)[2] <= width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = ch
        lines.append(current)
    return lines


def text(draw, xy, content, font_obj, fill=COLORS["ink"], width=None, line_gap=8, anchor=None):
    x, y = xy
    if width:
        for line in wrap(draw, content, font_obj, width):
            draw.text((x, y), line, font=font_obj, fill=fill)
            y += font_obj.size + line_gap
        return y
    draw.text((x, y), content, font=font_obj, fill=fill, anchor=anchor)
    return y + font_obj.size


def rounded(draw, box, fill, outline=COLORS["line"], radius=16, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def arrow(draw, start, end, color=COLORS["muted"], width=4):
    draw.line([start, end], fill=color, width=width)
    sx, sy = start
    ex, ey = end
    if abs(ex - sx) >= abs(ey - sy):
        direction = 1 if ex > sx else -1
        pts = [(ex, ey), (ex - direction * 18, ey - 10), (ex - direction * 18, ey + 10)]
    else:
        direction = 1 if ey > sy else -1
        pts = [(ex, ey), (ex - 10, ey - direction * 18), (ex + 10, ey - direction * 18)]
    draw.polygon(pts, fill=color)


def node(draw, x, y, w, h, title, body, color, tag=None):
    rounded(draw, (x, y, x + w, y + h), COLORS["panel"])
    draw.rectangle((x, y, x + 8, y + h), fill=color)
    text(draw, (x + 24, y + 18), title, F_HEAD, color, width=w - 48)
    text(draw, (x + 24, y + 60), body, F_BODY, COLORS["muted"], width=w - 48, line_gap=5)


def file_band(draw, x, y, w, h, title, items, color):
    rounded(draw, (x, y, x + w, y + h), "#FFFFFF", outline=color, radius=12, width=3)
    text(draw, (x + 18, y + 14), title, F_HEAD, color, width=w - 36)
    yy = y + 58
    for item in items:
        draw.ellipse((x + 20, yy + 8, x + 30, yy + 18), fill=color)
        text(draw, (x + 40, yy), item, F_SMALL, COLORS["muted"], width=w - 58, line_gap=4)
        yy += 42


def make_ee():
    img = Image.new("RGB", (W, H), COLORS["bg"])
    d = ImageDraw.Draw(img)
    text(d, (70, 46), "EE-AI-Toolkit（电气工程师 AI 工具包）流程图", F_TITLE)
    text(d, (72, 112), "类型：工具库型 + 知识库型。重点是先查资料，再复用脚本，把计算依据和假设交付清楚。", F_SUB, COLORS["muted"])
    d.line((70, 165, 1730, 165), fill=COLORS["line"], width=3)

    nodes = [
        (90, 230, "用户输入", "电气计算、AI 提示词、负载曲线、脚本复用等问题", COLORS["blue"], None),
        (420, 230, "SKILL.md 判断", "识别是否属于电气工程 AI 工具包；确定要读哪些资料", COLORS["orange"], None),
        (750, 230, "读取资料地图", "按问题类型读取资料库中的最小必要资料", COLORS["green"], None),
        (1080, 230, "脚本与检索", "必要时调用检索脚本或 Python 示例脚本", COLORS["purple"], None),
        (1410, 230, "交付结果", "输出计算过程、单位、假设、风险和验证建议", COLORS["red"], None),
    ]
    for x, y, title_, body, color, tag in nodes:
        node(d, x, y, 260, 170, title_, body, color, tag)
    for i in range(len(nodes) - 1):
        arrow(d, (nodes[i][0] + 260, 315), (nodes[i + 1][0], 315), COLORS["muted"])

    file_band(
        d,
        100,
        520,
        470,
        280,
        "references/（资料库）",
        [
            "course-index.md（课程索引）",
            "prompt-library.md（提示词库）",
            "python-script-catalog.md（脚本目录）",
            "source-digest.md（原始资料摘要）",
        ],
        COLORS["green"],
    )
    file_band(
        d,
        665,
        520,
        470,
        280,
        "assets/ 和 scripts/（资源与工具）",
        [
            "assets/python-scripts/（100 个 Python 示例）",
            "script_001_power_calculator.py（功率计算）",
            "script_010_voltage_drop_calculator.py（电压降）",
            "scripts/search_ee_ai.py（资料检索）",
        ],
        COLORS["purple"],
    )
    file_band(
        d,
        1230,
        520,
        430,
        280,
        "输出检查",
        [
            "是否说明单位和公式",
            "是否说明输入假设",
            "是否给出验证方法",
            "是否标注不能替代现场复核",
        ],
        COLORS["red"],
    )

    arrow(d, (880, 400), (335, 520), COLORS["green"])
    arrow(d, (1210, 400), (900, 520), COLORS["purple"])
    arrow(d, (1540, 400), (1445, 520), COLORS["red"])

    text(d, (70, 960), "一句话讲解：EE-AI-Toolkit 像电气工程师的“计算器抽屉”，先找资料，再拿脚本，最后交付可复核结果。", F_SUB, COLORS["orange"])
    out = OUT / "EE-AI-Toolkit流程图.png"
    img.save(out)
    return out


def make_plc():
    img = Image.new("RGB", (W, H), COLORS["bg"])
    d = ImageDraw.Draw(img)
    text(d, (70, 46), "PLC-Programming（PLC 编程开发综合）流程图", F_TITLE)
    text(d, (72, 112), "类型：专家路由型 + 流程型。重点是先分诊，再进入通用层或厂商层，最后输出可现场复核的结果。", F_SUB, COLORS["muted"])
    d.line((70, 165, 1730, 165), fill=COLORS["line"], width=3)

    node(d, 90, 220, 300, 160, "用户输入", "品牌、CPU、I/O 点表、顺控流程、报警联锁、故障描述", COLORS["blue"])
    node(d, 500, 220, 300, 160, "SKILL.md 分诊", "判断是否 PLC 任务；信息不完整时先追问", COLORS["orange"])
    node(d, 910, 220, 300, 160, "任务路由", "读取任务路由资料，判断开发、审查、调试或解释", COLORS["green"])
    node(d, 1320, 220, 300, 160, "厂商路由", "读取厂商路由资料，识别三菱、西门子等平台", COLORS["purple"])

    arrow(d, (390, 300), (500, 300))
    arrow(d, (800, 300), (910, 300))
    arrow(d, (1210, 300), (1320, 300))

    rounded(d, (760, 500, 1060, 655), "#FFFFFF", outline=COLORS["green"], radius=16, width=3)
    text(d, (790, 522), "通用 PLC 层", F_HEAD, COLORS["green"])
    text(d, (790, 570), "references/common/\n通用顺控、状态机、\n联锁、安全边界", F_BODY, COLORS["muted"], width=240)

    rounded(d, (1240, 500, 1540, 655), "#FFFFFF", outline=COLORS["purple"], radius=16, width=3)
    text(d, (1270, 522), "厂商专用层", F_HEAD, COLORS["purple"])
    text(d, (1270, 570), "references/vendors/\nMitsubishi、Siemens、\nRockwell、Omron 等", F_BODY, COLORS["muted"], width=240)

    arrow(d, (1060, 380), (910, 500), COLORS["green"])
    arrow(d, (1470, 380), (1390, 500), COLORS["purple"])

    node(d, 360, 760, 320, 145, "生成 / 审查 / 调试", "按模板输出顺控步骤、状态机、报警联锁或调试清单", COLORS["amber"])
    node(d, 760, 760, 320, 145, "安全边界", "标注假设、风险、人工复核点和现场验证条件", COLORS["red"])
    node(d, 1160, 760, 320, 145, "交付结果", "报告、代码草稿、检查清单、问题定位建议", COLORS["blue"])

    arrow(d, (910, 655), (520, 760), COLORS["green"])
    arrow(d, (1390, 655), (520, 760), COLORS["purple"])
    arrow(d, (680, 832), (760, 832), COLORS["muted"])
    arrow(d, (1080, 832), (1160, 832), COLORS["muted"])

    file_band(
        d,
        90,
        475,
        520,
        200,
        "关键文件夹",
        [
            "SKILL.md（入口与边界）",
            "references/common/（通用资料）",
            "references/vendors/（厂商资料）",
        ],
        COLORS["orange"],
    )

    text(d, (70, 990), "一句话讲解：PLC-Programming 像现场调试老师傅，先判断问题属于哪类，再决定看通用资料还是厂商资料。", F_SUB, COLORS["orange"])
    out = OUT / "PLC-Programming流程图.png"
    img.save(out)
    return out


if __name__ == "__main__":
    print(make_ee())
    print(make_plc())
