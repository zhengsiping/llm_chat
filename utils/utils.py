from pathlib import Path


def get_project_root():
    """自动找到项目根目录（适用于 Git 或 Python 项目）"""
    path = Path(__file__).resolve()
    for parent in path.parents:
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists() or (parent / "setup.py").exists():
            return parent
    return path.parent  # 如果没有找到，默认返回上一级
