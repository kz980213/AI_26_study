"""评测路由：触发 Ragas 评测"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from app.models.schemas import EvalResponse

router = APIRouter(prefix="/eval", tags=["评测"])
logger = logging.getLogger(__name__)


@router.post("/upload-golden-set")
async def upload_golden_set(file: UploadFile = File(...)):
    """上传评测集 JSON 文件"""
    if not file.filename or not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="请上传 JSON 格式的评测集文件")

    content = await file.read()
    try:
        data = json.loads(content)
        if not isinstance(data, list):
            raise ValueError("评测集必须是 JSON 数组")
        for item in data:
            if not all(k in item for k in ("question", "answer", "contexts")):
                raise ValueError("每条记录必须包含 question / answer / contexts 字段")
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"评测集格式错误: {e}")

    # 保存到 evals 目录
    eval_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "evals")
    os.makedirs(eval_dir, exist_ok=True)
    save_path = os.path.join(eval_dir, "golden_set.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {"message": f"评测集已更新，共 {len(data)} 条记录", "count": len(data)}


@router.post("/run", response_model=EvalResponse)
async def run_eval():
    """触发 Ragas 评测"""
    eval_script = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "evals",
        "run_eval.py",
    )

    if not os.path.exists(eval_script):
        raise HTTPException(status_code=500, detail="评测脚本不存在")

    try:
        result = subprocess.run(
            [sys.executable, eval_script],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        )
        if result.returncode != 0:
            logger.error(f"评测执行失败: {result.stderr}")
            raise HTTPException(
                status_code=500, detail=f"评测执行失败: {result.stderr[:500]}"
            )

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        result_file = f"eval_result_{timestamp}.json"
        return EvalResponse(
            message=f"评测完成\n{result.stdout[:1000]}",
            result_file=result_file,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="评测超时（5分钟限制）")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评测异常: {str(e)}")
