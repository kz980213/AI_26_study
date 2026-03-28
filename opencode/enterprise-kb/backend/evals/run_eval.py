"""Ragas 评测脚本：读取 golden_set.json，运行评测并输出结果"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone

# 将 backend 目录加入 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)


async def _retrieve_for_eval(question: str) -> list[str]:
    """评测用的检索函数：复用 retriever 服务"""
    from app.core.database import async_session_factory
    from app.services.retriever import retrieve

    async with async_session_factory() as db:
        chunks = await retrieve(db, question)
        return [c.content for c in chunks]


def _generate_for_eval(question: str, contexts: list[str]) -> str:
    """评测用的生成函数：复用 generator 服务"""
    from app.models.schemas import ChunkResult

    mock_chunks = [
        ChunkResult(
            chunk_id=f"eval-{i}",
            content=c,
            metadata={"source": "eval"},
            score=0.9,
            file_name="eval_doc",
        )
        for i, c in enumerate(contexts)
    ]

    from app.services.generator import generate_sync
    return generate_sync(question, mock_chunks)


async def run_evaluation() -> None:
    """运行 Ragas 评测"""
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy, context_precision
    from datasets import Dataset

    # 读取评测集
    eval_dir = os.path.dirname(os.path.abspath(__file__))
    golden_path = os.path.join(eval_dir, "golden_set.json")

    with open(golden_path, "r", encoding="utf-8") as f:
        golden_set = json.load(f)

    logger.info(f"加载评测集: {len(golden_set)} 条记录")

    questions = []
    ground_truths = []
    answers = []
    contexts = []

    for item in golden_set:
        question = item["question"]
        questions.append(question)
        ground_truths.append(item["answer"])

        # 检索
        retrieved = await _retrieve_for_eval(question)
        contexts.append(retrieved if retrieved else item["contexts"])

        # 生成
        answer = _generate_for_eval(question, contexts[-1])
        answers.append(answer)
        logger.info(f"评测进度: 问题 '{question[:30]}...' 生成完成")

    # 构建评测数据集
    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    })

    # 运行评测
    logger.info("开始 Ragas 评测...")
    metrics = [faithfulness, answer_relevancy, context_precision]

    try:
        results = evaluate(dataset, metrics=metrics)
        logger.info("评测完成!")

        # 打印表格
        print("\n" + "=" * 60)
        print("Ragas 评测结果")
        print("=" * 60)
        df = results.to_pandas()
        print(df.to_string(index=False))
        print("=" * 60)

        # 保存结果
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        result_file = os.path.join(eval_dir, f"eval_result_{timestamp}.json")
        result_data = {
            "timestamp": timestamp,
            "metrics": {},
            "details": [],
        }

        for col in df.columns:
            if col in ("question", "answer"):
                continue
            values = df[col].dropna().tolist()
            if values:
                result_data["metrics"][col] = {
                    "mean": float(sum(values) / len(values)),
                    "values": [float(v) for v in values],
                }

        for idx, row in df.iterrows():
            detail = {"question": questions[idx] if idx < len(questions) else ""}
            for col in df.columns:
                if col == "question":
                    continue
                val = row[col]
                detail[col] = float(val) if val is not None else None
            result_data["details"].append(detail)

        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        logger.info(f"评测结果已保存: {result_file}")

    except Exception as e:
        logger.error(f"评测执行失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(run_evaluation())
