from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QDialog,
    QDialogButtonBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QPlainTextEdit, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QSpinBox, QInputDialog)

from .api import CapabilityScanner, NewAPI, display_name, is_excluded_model
from .configuration import Configurator
from .client_policy import apply_user_confirmed_mapping
from .models import ModelCapability, ProbeStatus, ScanCache
from .storage import list_backups, load_cache, load_token, restore_backup, save_cache, save_token


def mark(status: ProbeStatus) -> str:
    return {
        ProbeStatus.CONFIRMED: "是",
        ProbeStatus.DECLARED: "声明",
        ProbeStatus.FAILED: "否",
        ProbeStatus.UNKNOWN: "未知",
    }[status]


class Worker(QObject):
    done = Signal(object)
    failed = Signal(str)
    log = Signal(str)

    def __init__(self, url: str, token: str, models: list[str] | None, concurrency: int = 3, deep_context: bool = False):
        super().__init__()
        self.url, self.token, self.models = url, token, models
        self.concurrency = max(1, min(concurrency, 8))
        self.deep_context = deep_context

    def execute(self):
        try:
            self.done.emit(asyncio.run(self._run()))
        except Exception as exc:
            self.failed.emit(str(exc))

    async def _run(self):
        api = NewAPI(self.url, self.token)
        try:
            ids = self.models or await api.models()
            if self.models is None:
                return "models", ids
            # CapabilityScanner expects a normal callable. A bound Qt signal is
            # emitted through .emit(), not called like a Python function.
            scanner = CapabilityScanner(api, self.log.emit)
            total = len(ids)
            completed = 0
            guard = asyncio.Semaphore(self.concurrency)

            async def probe(model: str):
                nonlocal completed
                async with guard:
                    try:
                        capability = await scanner.scan_one(model, deep=self.deep_context)
                    except Exception as exc:
                        # One problematic gateway model must not discard the
                        # successfully tested results of every other model.
                        capability = ModelCapability(
                            model_id=model,
                            display_name=display_name(model),
                            error=str(exc)[:180],
                            test_time=datetime.now(timezone.utc),
                        )
                        self.log.emit(f"{model}：检测失败，但其余模型会继续。")
                    capability = apply_user_confirmed_mapping(capability)
                    completed += 1
                    self.log.emit(f"检测进度：{completed}/{total}（已完成 {model}）")
                    return capability

            mode = "深度上下文检测" if self.deep_context else "快速上下文检测"
            self.log.emit(f"开始并发检测 {total} 个模型，同时最多检测 {self.concurrency} 个（{mode}）。")
            return "capabilities", await asyncio.gather(*(probe(model) for model in ids))
        finally:
            await api.close()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NewAPI 三客户端自动配置工具")
        self.resize(1250, 760)
        self.models: list[ModelCapability] = []
        self.model_ids: list[str] = []
        self.thread: QThread | None = None
        self.worker: Worker | None = None

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        connection = QGroupBox("NewAPI 网关")
        form = QFormLayout(connection)
        self.url = QLineEdit("http://10.97.144.27:3000")
        self.token = QLineEdit(load_token())
        self.token.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("网关地址", self.url)
        form.addRow("访问令牌", self.token)
        layout.addWidget(connection)

        buttons = QHBoxLayout()
        self.scan = QPushButton("1. 扫描模型")
        self.probe = QPushButton("2. 检测模型能力")
        self.preview = QPushButton("3. 预览修改")
        self.apply = QPushButton("4. 一键配置")
        self.restore = QPushButton("恢复备份")
        for button in (self.scan, self.probe, self.preview, self.apply, self.restore):
            buttons.addWidget(button)
        layout.addLayout(buttons)

        choices = QHBoxLayout()
        self.only_available = QCheckBox("只显示兼容模型")
        self.require_vision = QCheckBox("仅显示支持视觉的模型")
        self.deep_context = QCheckBox("深度检测上下文（可能产生较高费用）")
        self.concurrency = QSpinBox()
        self.concurrency.setRange(1, 8)
        self.concurrency.setValue(3)
        self.concurrency.setToolTip("同时检测的模型数量。较高值更快，但可能增加网关限流或负载风险。")
        self.codex, self.claude, self.opencode = QCheckBox("Codex"), QCheckBox("Claude Code"), QCheckBox("OpenCode")
        for check in (self.codex, self.claude, self.opencode):
            check.setChecked(True)
        for item in (self.only_available, self.require_vision, self.deep_context, QLabel("并发模型数："), self.concurrency, QLabel("配置目标："), self.codex, self.claude, self.opencode):
            choices.addWidget(item)
        choices.addStretch()
        layout.addLayout(choices)

        self.table = QTableWidget(0, 11)
        self.table.setHorizontalHeaderLabels(["模型", "响应接口", "消息接口", "聊天接口", "工具调用", "视觉识别", "推理能力", "上下文窗口", "最大输出", "Codex", "Claude / OpenCode"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

        self.logs = QPlainTextEdit()
        self.logs.setReadOnly(True)
        self.logs.setPlaceholderText("运行日志（不会记录访问令牌）。工具调用“否”表示本次探针未确认，不会单独阻止 Claude Code / OpenCode 配置。")
        self.logs.setMaximumBlockCount(500)
        self.logs.setMaximumHeight(140)
        layout.addWidget(self.logs)

        self.scan.clicked.connect(self.scan_models)
        self.probe.clicked.connect(self.probe_models)
        self.preview.clicked.connect(self.show_preview)
        self.apply.clicked.connect(self.apply_changes)
        self.restore.clicked.connect(self.restore_changes)
        self.only_available.toggled.connect(self.render)
        self.require_vision.toggled.connect(self.render)

        cached = load_cache()
        if cached:
            self.url.setText(cached.gateway_url)
            self.models = [apply_user_confirmed_mapping(model) for model in cached.capabilities if not is_excluded_model(model.model_id)]
            self.model_ids = [model.model_id for model in self.models]
            self.render()
            self.log("已加载能力缓存；配置前建议重新检测。")

    def log(self, message: str):
        self.logs.appendPlainText(message)

    def selected_targets(self) -> set[str]:
        return {name for name, box in (("codex", self.codex), ("claude", self.claude), ("opencode", self.opencode)) if box.isChecked()}

    def valid_connection(self) -> bool:
        if not self.url.text().strip() or not self.token.text().strip():
            QMessageBox.warning(self, "缺少网关信息", "请先输入 NewAPI 网关地址和访问令牌。")
            return False
        return True

    def start(self, models: list[str] | None):
        if not self.valid_connection():
            return
        self.set_busy(True)
        self.thread = QThread(self)
        self.worker = Worker(self.url.text(), self.token.text(), models, self.concurrency.value(), self.deep_context.isChecked())
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.execute)
        self.worker.done.connect(self.finished)
        self.worker.failed.connect(self.failed)
        self.worker.log.connect(self.log)
        self.worker.done.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(lambda: self.set_busy(False))
        self.thread.finished.connect(lambda: setattr(self, "worker", None))
        self.thread.start()

    def scan_models(self):
        self.start(None)

    def probe_models(self):
        if not self.model_ids:
            QMessageBox.information(self, "请先扫描", "请先点击“扫描模型”，再检测模型能力。")
            return
        if self.deep_context.isChecked():
            answer = QMessageBox.warning(self, "确认深度上下文检测", "深度检测会依次发送 8K、32K、64K、128K、256K、512K、1M 的长请求（不超过已声明上限）。这可能产生较高 Token 用量和费用。\n\n确定继续吗？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.start(self.model_ids)

    def finished(self, result):
        kind, data = result
        if kind == "models":
            # A scan is authoritative: remove stale cached entries and display
            # the fresh gateway list immediately, even before capability probes.
            self.model_ids = [model_id for model_id in dict.fromkeys(data) if not is_excluded_model(model_id)]
            self.models = [apply_user_confirmed_mapping(ModelCapability(model_id=model_id, display_name=display_name(model_id))) for model_id in self.model_ids]
            self.render()
            self.log(f"已发现 {len(data)} 个模型。请点击“检测模型能力”进行真实协议验证。")
            return
        self.models = [apply_user_confirmed_mapping(model) for model in data]
        save_cache(ScanCache(gateway_url=self.url.text().rstrip("/"), capabilities=self.models))
        self.render()
        self.log("能力缓存已保存；客户端列中的“用户确认”来自本次指定的网关映射，其他结果来自 API 实测。")

    def failed(self, message: str):
        self.log(f"错误：{message}")
        QMessageBox.critical(self, "操作失败", message)

    def set_busy(self, busy: bool):
        for button in (self.scan, self.probe, self.preview, self.apply, self.restore):
            button.setEnabled(not busy)

    def render(self):
        values = []
        for model in self.models:
            if self.only_available.isChecked() and not (model.codex_compatible or model.claude_compatible or model.opencode_compatible):
                continue
            if self.require_vision.isChecked() and not model.vision:
                continue
            values.append(model)
        self.table.setRowCount(len(values))
        for row, model in enumerate(values):
            protocol = lambda result: f"文本：{mark(result.text)} / 流式：{mark(result.streaming)}"
            tools = "/".join(mark(r.tools) for r in (model.responses, model.messages, model.chat))
            vision = "/".join(mark(r.vision) for r in (model.responses, model.messages, model.chat))
            codex = "用户确认" if "codex" in model.manual_clients else mark(ProbeStatus.CONFIRMED if model.codex_compatible else ProbeStatus.FAILED)
            claude = "用户确认" if "claude" in model.manual_clients else mark(ProbeStatus.CONFIRMED if model.claude_compatible else ProbeStatus.FAILED)
            opencode = "用户确认" if "opencode" in model.manual_clients else mark(ProbeStatus.CONFIRMED if model.opencode_compatible else ProbeStatus.FAILED)
            cells = [model.display_name, protocol(model.responses), protocol(model.messages), protocol(model.chat), tools, vision, model.reasoning_summary(), model.context_summary(), str(model.max_output_tokens or "未知"), codex, f"{claude} / {opencode}"]
            for col, value in enumerate(cells):
                self.table.setItem(row, col, QTableWidgetItem(value))
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def make_configurator(self) -> Configurator:
        return Configurator(self.url.text(), self.token.text(), self.models)

    def show_preview(self):
        if not self.models:
            QMessageBox.information(self, "没有已验证模型", "请先检测模型能力，再预览配置。")
            return
        preview = self.make_configurator().preview(self.selected_targets())
        dialog = QDialog(self)
        dialog.setWindowTitle(preview.title)
        dialog.resize(720, 400)
        layout = QVBoxLayout(dialog)
        text = QPlainTextEdit(preview.text)
        text.setReadOnly(True)
        layout.addWidget(text)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        dialog.exec()

    def apply_changes(self):
        if not self.models or not self.valid_connection():
            return
        now = datetime.now(timezone.utc)
        if any(not m.test_time or (now - m.test_time).total_seconds() > 24 * 3600 for m in self.models):
            QMessageBox.warning(self, "需要重新检测", "能力缓存已超过 24 小时或尚未检测。请先重新检测模型能力，再执行配置。")
            return
        self.show_preview()
        answer = QMessageBox.question(self, "确认写入配置", "确定要写入预览中的配置和当前用户环境变量吗？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        save_token(self.token.text())
        result = self.make_configurator().apply(self.selected_targets())
        self.log("\n".join(result))
        QMessageBox.information(self, "配置完成", "\n".join(result))

    def restore_changes(self):
        backups = list_backups()
        if not backups:
            QMessageBox.information(self, "没有备份", "尚未找到可恢复的配置备份。")
            return
        labels: list[str] = []
        lookup: dict[str, object] = {}
        for backup in backups:
            try:
                manifest = json.loads((backup / "manifest.json").read_text(encoding="utf-8"))
                created_at = manifest.get("created_at", backup.name)
                files = ", ".join(manifest.get("files", {}).keys()) or "无配置文件"
                label = f"{created_at}  —  {files}"
            except (OSError, ValueError, json.JSONDecodeError):
                label = f"{backup.name}  —  备份清单无法读取"
            # Keep labels unique if two manifests happen to share a timestamp.
            label = f"{label} [{backup.name}]"
            labels.append(label)
            lookup[label] = backup
        selected, accepted = QInputDialog.getItem(self, "选择要恢复的备份", "备份版本：", labels, 0, False)
        if not accepted:
            return
        backup = lookup[selected]
        message = f"将恢复以下备份：\n{backup}\n\n这会还原 Codex、Claude Code、OpenCode 配置和相关当前用户环境变量。确定继续吗？"
        answer = QMessageBox.warning(self, "确认恢复备份", message, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            restore_backup(backup)
            self.log(f"已恢复备份：{backup}")
            QMessageBox.information(self, "恢复完成", f"已恢复所选备份：\n{backup}\n\n请重新打开 Codex、Claude Code 和 OpenCode，使它们读取恢复后的环境变量。")
        except Exception as exc:
            self.log(f"恢复失败：{exc}")
            QMessageBox.critical(self, "恢复失败", str(exc))


def run():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
