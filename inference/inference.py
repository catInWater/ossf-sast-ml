import os
import json
import argparse
import hashlib
import re
import pickle
from pathlib import Path
from tqdm import tqdm

from prediction import predict


def _file_name_to_pickle_prefix(file_name, run_id):
    pickle_prefix = Path(os.path.dirname(os.path.abspath(__file__))) / 'cache' / run_id
    file_name = re.sub(r"[-.]", "_", file_name)
    file_name_parts = file_name.split('sources')[-1].split(os.path.sep)
    while file_name_parts:
        part = file_name_parts.pop()
        if part:
            pickle_prefix /= part

    return pickle_prefix


def _load_pickled_result(pickle_file):
    try:
        if pickle_file.exists():
            with open(pickle_file, 'rb') as f:
                return pickle.load(f)

    except Exception as e:
        print(f"Error loading pickled result {pickle_file}: {e}")

    return None


def _write_pickled_result(pickle_file, prediction):
    pickle_file.parent.mkdir(parents=True, exist_ok=True)
    with open(pickle_file, 'wb') as f:
        pickle.dump(prediction, f)


def _interval_contains(a_start, a_end, b_start, b_end):
    return a_start <= b_start and a_end >= b_end


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="path to input json containing function data")
    parser.add_argument("-r", "--run_id", help="run id")
    return parser.parse_args()

def _message_entry(messages_map, start, end, prediction):
    messages_map[start] = {
        "startLine": start,
        "endLine": end,
        "vulnerable": prediction
    }

def _update_messages_map(prediction, start, end, messages_map, m_start):
    m_data = messages_map[m_start]
    m_end = m_data["endLine"]

    if _interval_contains(m_start, m_end, start, end):
        if prediction == m_data["vulnerable"]:
            return True

        if m_start == start and m_end == end:
            _message_entry(messages_map, start, end, 1)
            return True

        if m_start < start:
            _message_entry(messages_map, m_start, start - 1, m_data["vulnerable"])

        _message_entry(messages_map, start, end, prediction)
        if m_end > end:
            _message_entry(messages_map, end + 1, m_end, m_data["vulnerable"])

        return True

    return False


def main(input_file, run_id=None):
    """
    input format:
[
  {
    "filePath": "C:\\...\\karma.conf.js",
    "messages": [
      {
        "functionBody": "function(config) {...}",
        "startLine": 3,
        "endLine": 36,
        "nodeType": "FunctionExpression"
      }, ...
    ]
  }, ...
]
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        function_data = json.load(f)

    result_data = []
    with tqdm(total=sum(len(file_data["messages"]) for file_data in function_data)) as pbar:
        for file_data in function_data:
            pickle_prefix = _file_name_to_pickle_prefix(file_data.get("filePath", ''), run_id or 'run_1')
            messages_map = {}
            alerts = sorted(file_data.get("messages", []), key=lambda m: m.get("startLine", 0))
            for a in alerts:
                start = a.get("startLine", 0)
                end = a.get("endLine", 0)
                function_body = a.get("functionBody")
                if not function_body:
                    pbar.update(1)
                    continue

                function_body_hash = hashlib.sha512(function_body.encode('utf-8')).hexdigest()
                pickle_file = pickle_prefix / function_body_hash
                pickled_result = _load_pickled_result(pickle_file=pickle_file)
                if pickled_result is None:
                    prediction = predict(function_body=function_body)
                    _write_pickled_result(pickle_file=pickle_file, prediction=prediction)

                else:
                    prediction = pickled_result

                for m_start in messages_map:
                    if _update_messages_map(prediction, start, end, messages_map, m_start):
                        break

                else:
                    messages_map[start] = {
                        "startLine": a["startLine"],
                        "endLine": a["endLine"],
                        "vulnerable": prediction
                    }

                pbar.update(1)

            if messages_map:
                result_data.append({
                    "filePath": file_data.get("filePath", ""),
                    "messages": list(messages_map.values())
                })

    with open(input_file, 'w') as f:
        json.dump(result_data, f, indent=2)

    print("SUCCESS")


if __name__ == "__main__":
    args = _parse_args()
    # test with "python inference.py -i test.json -r test"
    main(input_file=args.input, run_id=args.run_id)
