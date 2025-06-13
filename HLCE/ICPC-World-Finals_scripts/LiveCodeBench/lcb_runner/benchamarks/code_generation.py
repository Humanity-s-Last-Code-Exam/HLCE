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
    ICPC_world_final_2015 = "ICPC_world_final_2015"

class TestType(Enum):
    STDIN = "stdin"

@dataclass
class Test:
    input: str
    output: str

    def __post_init__(self):
        self.testtype = TestType("stdin")


@dataclass
class CodeGenerationProblem:
    question_title: str
    question_content: str
    platform: 'Platform'
    question_id: str
    test_cases: List['Test']
    instruct: str
    prompt: str

    def __post_init__(self):
        self.platform = Platform(self.platform)
        
        try:
            self.test_cases = json.loads(self.test_cases)  # type: ignore
        except:
            # self.test_cases = [json.loads(item) for item in eval(self.test_cases)]  # type: ignore
            self.test_cases = self.test_cases

        self.test_cases = [Test(**t) for t in self.test_cases]


    def insert_output(self, output_list: List[str], code_list: List[str]) -> dict:
        return {
            "question_title": self.question_title,
            "question_content": self.question_content,
            "platform": self.platform.value,
            "question_id": self.question_id,
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
                        for t in self.test_cases
                    ],
                    "outputs": [
                        t.output
                        for t in self.test_cases
                    ]
                }
            ),
        }


def load_code_generation_dataset(release_version="release_v1") -> List[CodeGenerationProblem]:
    dataset = [] 
    iterable_dataset = load_dataset("HumanLastCodeExam/icpc-world-finals", streaming=True) 
    for example in iterable_dataset["train"]:
        dataset.append(example)

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
