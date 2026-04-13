import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


APP_TITLE = "noita存档工具-电浆蓝版本"
INDEX_FILE = "archive_index.json"
CONFIG_FILE = "config.json"
ARCHIVE_DIR_NAME = "archives"
ARCHIVE_README_FILE = "README_这是Noita存档备份目录.txt"
APP_DESC_TEXT = (
    "这个程序是我根据B站一个哥们的存档工具来的灵感 (=^▽^=)\n"
    "然后自己写的一个版本。(=^_^=)\n"
    "\n"
    "去掉了那哥们的繁琐确认环节，(=^o^=)\n"
    "调整了按键的数字和顺序，操作更方便了。(=^.^=)\n"
    "\n"
    "主要还是给群友用，免得大家老是手动去存档。(=^-^=)\n"
    "欢迎大家一起来联机互相van游戏！(=^w^=)\n"
    "联机加群1023638578 (=^▽^=)\n"
    "GitHub项目地址: https://github.com/plasmaflea/noita--- (=^.^=)\n"
    "\n"
    "祝大家玩得开心~ (=^_^=)"
)


def default_noita_save_path() -> Path:
    local_low = os.environ.get("LOCALAPPDATA", "")
    # LOCALAPPDATA -> .../AppData/Local, LocalLow is sibling directory
    base = Path(local_low).parent / "LocalLow" / "Nolla_Games_Noita" / "save00"
    return base


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def now_name() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def clear_screen() -> None:
    os.system("cls")


class ArchiveManager:
    def __init__(self) -> None:
        self.base_dir = Path(__file__).resolve().parent
        self.index_path = self.base_dir / INDEX_FILE
        self.config_path = self.base_dir / CONFIG_FILE
        self.config = self._load_config()
        self.archive_root = self._resolve_archive_root()
        self.archive_root.mkdir(parents=True, exist_ok=True)
        self._ensure_archive_readme()
        self.index = self._load_index()

    def _load_config(self) -> dict:
        default_config = {
            "noita_save_path": str(default_noita_save_path()),
        }
        if not self.config_path.exists():
            self._save_json(self.config_path, default_config)
            return default_config
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
            if "noita_save_path" not in data:
                data["noita_save_path"] = default_config["noita_save_path"]
                self._save_json(self.config_path, data)
            return data
        except (json.JSONDecodeError, OSError):
            print("[警告] 配置文件损坏，已重建默认配置。")
            self._save_json(self.config_path, default_config)
            return default_config

    def _load_index(self) -> list:
        if not self.index_path.exists():
            self._save_json(self.index_path, [])
            return []
        try:
            data = json.loads(self.index_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except (json.JSONDecodeError, OSError):
            pass
        print("[警告] 索引文件损坏，已重建空索引。")
        self._save_json(self.index_path, [])
        return []

    def _save_json(self, path: Path, data) -> None:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _save_index(self) -> None:
        self._save_json(self.index_path, self.index)

    def get_noita_save_path(self) -> Path:
        return Path(self.config.get("noita_save_path", "")).expanduser()

    def _resolve_archive_root(self) -> Path:
        save_path = self.get_noita_save_path()
        # 归档目录与 save00 同级，满足“存档目录旁边”的需求。
        return save_path.parent / ARCHIVE_DIR_NAME

    def _ensure_source_exists(self) -> bool:
        src = self.get_noita_save_path()
        if not src.exists() or not src.is_dir():
            print(f"[错误] Noita 存档目录不存在：{src}")
            print("请编辑 config.json 中的 noita_save_path 后重试。")
            return False
        return True

    def _ensure_archive_readme(self) -> None:
        readme_path = self.archive_root / ARCHIVE_README_FILE
        if readme_path.exists():
            return
        content = (
            "Noita Archive Manager 备份目录说明\n"
            "================================\n"
            "1. 这是 Noita 存档备份目录，请勿随意修改子目录名称。\n"
            "2. 每个子目录代表一次备份存档。\n"
            "3. 建议使用工具进行读取、删除和覆盖操作。\n"
            "4. 如需迁移，请复制整个 archives 目录。\n"
        )
        try:
            readme_path.write_text(content, encoding="utf-8")
        except OSError:
            # 说明文件写入失败不影响核心存档功能。
            pass

    def _copy_dir(self, src: Path, dst: Path, overwrite: bool = False) -> None:
        if dst.exists():
            if overwrite:
                shutil.rmtree(dst)
            else:
                raise FileExistsError(f"目标已存在：{dst}")
        shutil.copytree(src, dst)

    def _new_archive_record(self, name: str, note: str = "") -> dict:
        archive_id = len(self.index) + 1
        folder_name = f"{now_name()}_{name}"
        return {
            "id": archive_id,
            "name": name,
            "folder": folder_name,
            "created_at": now_str(),
            "note": note,
        }

    def _reindex(self) -> None:
        for i, rec in enumerate(self.index, start=1):
            rec["id"] = i
        self._save_index()

    def save(self, quick: bool = False, overwrite_latest: bool = False) -> None:
        if not self._ensure_source_exists():
            return
        src = self.get_noita_save_path()
        if overwrite_latest:
            if not self.index:
                print("[提示] 当前没有历史存档，改为普通保存。")
                return self.save(quick=True, overwrite_latest=False)
            latest = self.index[-1]
            dst = self.archive_root / latest["folder"]
            try:
                self._copy_dir(src, dst, overwrite=True)
                latest["created_at"] = now_str()
                latest["note"] = (latest.get("note", "") + " | 覆盖更新").strip(" |")
                self._save_index()
                print(f"[成功] 已覆盖最新存档：#{latest['id']} {latest['name']}")
            except OSError as e:
                print(f"[错误] 覆盖保存失败：{e}")
            return

        if quick:
            name = "quicksave"
        else:
            name = f"save_{now_name()}"
        rec = self._new_archive_record(name=name)
        dst = self.archive_root / rec["folder"]
        try:
            self._copy_dir(src, dst, overwrite=False)
            self.index.append(rec)
            self._save_index()
            print(f"[成功] 已保存存档：#{rec['id']} {rec['name']}")
        except OSError as e:
            print(f"[错误] 保存失败：{e}")

    def _select_by_id(self) -> Optional[dict]:
        if not self.index:
            print("[提示] 当前没有存档。")
            return None
        self.log(limit=None)
        raw = input("输入要操作的存档 ID：").strip()
        if not raw.isdigit():
            print("[错误] 请输入数字 ID。")
            return None
        idx = int(raw)
        for rec in self.index:
            if rec["id"] == idx:
                return rec
        print("[错误] 未找到该 ID。")
        return None

    def load(self, quick: bool = False) -> None:
        if not self.index:
            print("[提示] 当前没有存档可读取。")
            return
        rec = self.index[-1] if quick else self._select_by_id()
        if not rec:
            return
        src = self.archive_root / rec["folder"]
        dst = self.get_noita_save_path()
        if not src.exists():
            print(f"[错误] 存档目录不存在：{src}")
            return
        try:
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"[成功] 已读取存档：#{rec['id']} {rec['name']}")
        except OSError as e:
            print(f"[错误] 读取失败：{e}")

    def log(self, limit: Optional[int] = None) -> None:
        if not self.index:
            print("[提示] 当前没有存档记录。")
            return
        records = self.index[-limit:] if limit else self.index
        print("-" * 72)
        for rec in records:
            print(
                f"#{rec['id']:<3} 名称: {rec['name']:<18} 时间: {rec['created_at']}  备注: {rec.get('note', '')}"
            )
        print("-" * 72)

    def modify_archive(self) -> None:
        rec = self._select_by_id()
        if not rec:
            return
        new_name = input(f"新名称(回车保持: {rec['name']})：").strip()
        new_note = input(f"新备注(回车保持: {rec.get('note', '')})：").strip()
        if new_name:
            rec["name"] = new_name
        if new_note:
            rec["note"] = new_note
        self._save_index()
        print("[成功] 存档信息已更新。")

    def delete_archive(self, quick: bool = False) -> None:
        if not self.index:
            print("[提示] 当前没有存档可删除。")
            return
        rec = self.index[-1] if quick else self._select_by_id()
        if not rec:
            return
        folder = self.archive_root / rec["folder"]
        try:
            if folder.exists():
                shutil.rmtree(folder)
            self.index = [x for x in self.index if x["id"] != rec["id"]]
            self._reindex()
            print("[成功] 存档已删除。")
        except OSError as e:
            print(f"[错误] 删除失败：{e}")

    def delete_all_archives(self) -> None:
        if not self.index and not self.archive_root.exists():
            print("[提示] 当前没有存档可删除。")
            return
        try:
            if self.archive_root.exists():
                shutil.rmtree(self.archive_root)
            self.archive_root.mkdir(parents=True, exist_ok=True)
            self._ensure_archive_readme()
            self.index = []
            self._save_index()
            print("[成功] 已删除全部存档。")
        except OSError as e:
            print(f"[错误] 删除全部失败：{e}")

    def usage(self) -> None:
        total_size = 0
        count = 0
        for root, _, files in os.walk(self.archive_root):
            for f in files:
                count += 1
                p = Path(root) / f
                try:
                    total_size += p.stat().st_size
                except OSError:
                    pass
        mb = total_size / (1024 * 1024)
        print(f"归档文件数: {count}")
        print(f"归档目录: {self.archive_root}")
        print(f"占用空间: {mb:.2f} MB")

    def print_help(self) -> None:
        print("\n[命令说明]")
        print("1.qsave(qs)      快速保存(名称为 quicksave)")
        print("2.rsave(rs)      覆盖式保存(覆盖最新存档目录)")
        print("3.qload(ql)      快速读取最新存档")
        print("4.load(l)        读取指定存档")
        print("5.log(lo)        查看全部存档信息")
        print("6.slog(sl)       查看近七次存档信息")
        print("7.delArch(del)   删除指定存档")
        print("8.qDelete(qd)    删除最新存档")
        print("9.deleteAll(da)  删除全部存档")
        print("10.mArchive(ma)  修改存档信息(名称/备注)")
        print("11.usage(use)    查看占用空间")
        print("12.about(ab)     程序说明")
        print("13.clearScreen(cls)      清屏")
        print("14.quit(q)       退出")
        print(f"\n程序说明: {APP_DESC_TEXT}\n")
        print(f"当前 Noita 存档路径: {self.get_noita_save_path()}\n")
        print(f"当前归档目录路径: {self.archive_root}\n")


def print_menu() -> None:
    print(f"-----:===================={APP_TITLE}====================")
    print()
    print("输入操作：(数字/编号/括号内简写)")
    print("1.qsave(qs)      快速保存       2.rsave(rs)     覆盖最新存档             3.qload(ql)      快速读取最新")
    print()
    print("4.load(l)        读取指定存档   5.log(lo)       全部存档信息             6.slog(sl)       近七次存档")
    print()
    print("7.delArch(del)   删除指定存档   8.qDelete(qd)   删除最新存档             9.deleteAll(da)  删除全部存档")
    print()
    print("10.mArchive(ma)  修改存档信息   11.usage(use)   查看占用空间")
    print()
    print("12.about(ab)     程序说明       13.clearScreen(cls) 清屏                 14.quit(q)       退出")
    print()


def print_about() -> None:
    print(APP_DESC_TEXT)
    print()


def main() -> None:
    manager = ArchiveManager()
    command_map = {
        "1": "qsave",
        "qsave": "qsave",
        "qs": "qsave",
        "2": "rsave",
        "rsave": "rsave",
        "rs": "rsave",
        "3": "qload",
        "qload": "qload",
        "ql": "qload",
        "4": "load",
        "load": "load",
        "l": "load",
        "5": "log",
        "log": "log",
        "lo": "log",
        "6": "slog",
        "slog": "slog",
        "sl": "slog",
        "7": "delarch",
        "delarch": "delarch",
        "del": "delarch",
        "8": "qdelete",
        "qdelete": "qdelete",
        "qd": "qdelete",
        "9": "deleteall",
        "deleteall": "deleteall",
        "da": "deleteall",
        "10": "marchive",
        "marchive": "marchive",
        "ma": "marchive",
        "11": "usage",
        "usage": "usage",
        "use": "usage",
        "12": "about",
        "about": "about",
        "ab": "about",
        "help": "help",
        "h": "help",
        "13": "clear",
        "clearscreen": "clear",
        "cls": "clear",
        "14": "quit",
        "quit": "quit",
        "q": "quit",
    }

    print_menu()
    print_about()
    while True:
        raw = input(">>> ").strip().lower()
        cmd = command_map.get(raw)
        if not cmd:
            print("[错误] 无效命令，输入 help 或 h 查看帮助。\n")
            continue
        if cmd == "quit":
            print("Bye.")
            break
        if cmd == "help":
            manager.print_help()
        elif cmd == "about":
            print_about()
        elif cmd == "clear":
            clear_screen()
            print_menu()
        elif cmd == "qsave":
            manager.save(quick=True, overwrite_latest=False)
        elif cmd == "rsave":
            manager.save(quick=False, overwrite_latest=True)
        elif cmd == "load":
            manager.load(quick=False)
        elif cmd == "qload":
            manager.load(quick=True)
        elif cmd == "log":
            manager.log(limit=None)
        elif cmd == "slog":
            manager.log(limit=7)
        elif cmd == "marchive":
            manager.modify_archive()
        elif cmd == "delarch":
            manager.delete_archive(quick=False)
        elif cmd == "qdelete":
            manager.delete_archive(quick=True)
        elif cmd == "deleteall":
            manager.delete_all_archives()
        elif cmd == "usage":
            manager.usage()
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断，程序退出。")
        sys.exit(0)
