import json
import zlib
import pickle
import base64
from enum import Enum
from typing import List, Dict
from datetime import datetime
from dataclasses import dataclass

from datasets import load_dataset


class Platform(Enum):
    LEETCODE = "leetcode"
    CODEFORCES = "codeforces"
    ATCODER = "atcoder"


class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class TestType(Enum):
    STDIN = "stdin"
    FUNCTIONAL = "functional"


@dataclass
class Test:
    input: str
    output: str
    testtype: TestType

    def __post_init__(self):
        self.testtype = TestType(self.testtype)
        # if self.testtype == TestType.FUNCTIONAL:
        #     self.input = json.loads(self.input)
        #     self.output = json.loads(self.output)


@dataclass
class CodeGenerationProblem:
    question_title: str
    question_content: str
    platform: 'Platform'  # 使用字符串引用避免潜在的前向引用问题
    question_id: str
    contest_id: str
    contest_date: datetime
    starter_code: str
    difficulty: 'Difficulty'
    public_test_cases: List['Test']  # 使用 List 而不是 list
    private_test_cases: List['Test']  # 使用 List 而不是 list
    metadata: Dict  # 使用 Dict 而不是 dict

    def __post_init__(self):
        self.platform = Platform(self.platform)
        self.difficulty = Difficulty(self.difficulty)
        self.contest_date = datetime.fromisoformat(self.contest_date)

        try:
            self.public_test_cases = json.loads(self.public_test_cases)  # type: ignore
        except:
            self.public_test_cases = [json.loads(item) for item in eval(self.public_test_cases)]  # type: ignore
            
        self.public_test_cases = [Test(**t) for t in self.public_test_cases]

        try:
            if not self.private_test_cases:
                self.private_test_cases = []
            else:
                self.private_test_cases = json.loads(self.private_test_cases)  # type: ignore
        except:
            self.private_test_cases = json.loads(
                pickle.loads(
                    zlib.decompress(
                        base64.b64decode(self.private_test_cases.encode("utf-8"))  # type: ignore
                    )
                )
            )  # type: ignore
        self.private_test_cases = [Test(**t) for t in self.private_test_cases]
        
        if not self.metadata:
            self.metadata = {}
        else:
            self.metadata = json.loads(self.metadata)  # type: ignore

    def insert_output(self, output_list: List[str], code_list: List[str]) -> dict:
        return {
            "question_title": self.question_title,
            "question_content": self.question_content,
            "platform": self.platform.value,
            "question_id": self.question_id,
            "contest_id": self.contest_id,
            "contest_date": self.contest_date.isoformat(),
            "starter_code": self.starter_code,
            "difficulty": self.difficulty.value,
            "output_list": output_list,
            "code_list": code_list,
        }

    def insert_output_evaluation(
        self,
        output_list: List[str],
        code_list: List[str],
        graded_list: List[bool],
        **kwargs,
    ) -> dict:
        output = self.insert_output(output_list, code_list)
        output["graded_list"] = graded_list
        output["pass@1"] = graded_list.count(True) / len(graded_list)
        for k, v in kwargs.items():
            output[k] = v
        return output

    def get_evaluation_sample(self):
        return {
            "input_output": json.dumps(
                {
                    "inputs": [
                        t.input
                        for t in self.public_test_cases + self.private_test_cases
                    ],
                    "outputs": [
                        t.output
                        for t in self.public_test_cases + self.private_test_cases
                    ],
                    "fn_name": self.metadata.get("func_name", None),
                }
            ),
        }


def load_code_generation_dataset(release_version="release_v1") -> List[CodeGenerationProblem]:
    #dataset = load_dataset("livecodebench/code_generation_lite", split="test", version_tag=release_version, trust_remote_code=True)
    #dataset = load_dataset("/home/lixiangyang/code_llm_eval_v2/LiveCodeBench-main/code_generation_lite/code_generation_lite.py", split="test", version_tag=release_version, trust_remote_code=True, download_mode='force_redownload')
    dataset = load_dataset("/home/lixiangyang/code_llm_eval_v2/LiveCodeBench-main/code_generation_lite/code_generation_lite.py", split="test", version_tag=release_version, trust_remote_code=True)
    dataset = [CodeGenerationProblem(**p) for p in dataset]  # type: ignore
    print(f"Loaded {len(dataset)} problems")
    return dataset


def load_code_generation_dataset_not_fast(release_version="release_v1") -> List[CodeGenerationProblem]:
    dataset = load_dataset("livecodebench/code_generation", split="test")
    dataset = [CodeGenerationProblem(**p) for p in dataset]  # type: ignore
    print(f"Loaded {len(dataset)} problems")
    return dataset


if __name__ == "__main__":
    dataset = load_code_generation_dataset()
