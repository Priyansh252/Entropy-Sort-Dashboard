"""
app.py — Entropy-Aware Sort Dashboard: Flask Backend
======================================================
Exposes API endpoints:
  GET  /api/categories          → list available dataset categories
  POST /api/run-analysis        → run full entropy + sorting benchmark (Iris or folder)
  POST /api/run-real-analysis   → alias for the above
"""

import os
import random
import time
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from sklearn.datasets import load_iris

app = Flask(__name__)
CORS(app)



# 1. DATASET LOADERS

def load_dataset(folder_path="dataset", max_files_per_category=5):
    """
    Walk folder_path/ looking for sub-directories (= categories).
    Each text file inside should contain one number per line.
    Returns:
        { "category_name": [ [num, num, ...], [...], ... ], ... }
    """
    datasets = {}

    if not os.path.isdir(folder_path):
        return datasets

    for category in sorted(os.listdir(folder_path)):
        category_path = os.path.join(folder_path, category)
        if not os.path.isdir(category_path):
            continue

        files = os.listdir(category_path)
        files = random.sample(files, min(max_files_per_category, len(files)))

        arrays = []
        for file in files:
            file_path = os.path.join(category_path, file)
            try:
                with open(file_path, "r") as f:
                    numbers = []
                    for line in f:
                        line = line.strip()
                        if line:
                            numbers.append(float(line))
                    if numbers:
                        MAX_SIZE = 2000
                        if len(numbers) > MAX_SIZE:
                            numbers = numbers[:MAX_SIZE]
                        arrays.append(numbers)
            except Exception:
                continue

        if arrays:
            datasets[category] = arrays

    return datasets


def get_iris_datasets(size=1000):
    iris = load_iris()
    base = list(iris.data[:, 0])
    repeats = (size // len(base)) + 1
    arr = (base * repeats)[:size]

    # LOW
    sorted_arr = sorted(arr)

    #MEDIUM
    medium_arr = sorted_arr.copy()
    for _ in range(len(medium_arr)//5):
        i = random.randint(0, len(medium_arr)-1)
        j = random.randint(0, len(medium_arr)-1)
        medium_arr[i], medium_arr[j] = medium_arr[j], medium_arr[i]

    # HIGH
    high_arr = sorted_arr.copy()
    random.shuffle(high_arr)

    return {
        "Low":    [sorted_arr],
        "Medium": [medium_arr],
        "High":   [high_arr],
    }



# 2. ENTROPY FUNCTIONS  (backend is the single source of truth)


def quick_disorder_check(arr):
    n = len(arr)
    if n == 0:
        return 0

    disorder = sum(1 for i in range(n - 1) if arr[i] > arr[i + 1])

    
    return disorder / n


def approximate_entropy(arr, samples=None):
    """O(samples) Monte-Carlo inversion counter."""
    n = len(arr)
    if n == 0:
        return 0

    if samples is None:
        samples = min(1000, n * 2)

    inv = 0
    for _ in range(samples):
        i = random.randint(0, n - 1)
        j = random.randint(0, n - 1)
        if i < j and arr[i] > arr[j]:
            inv += 1
        elif j < i and arr[j] > arr[i]:
            inv += 1

    return inv / samples if samples else 0


def structural_entropy(arr):
    disorder = quick_disorder_check(arr)

    # EXACT working logic (DO NOT MODIFY)
    if disorder < 0.05:
        return 0.0
    elif disorder > 0.6:
        return 1.0

    return approximate_entropy(arr)


def interpret_entropy(H):
    if H < 0.2:
        return "Low Entropy"
    elif H < 0.5:
        return "Medium Entropy"
    else:
        return "High Entropy"



# 3. SORTING ALGORITHMS

def entropy_aware_sort(arr):
    n = len(arr)
    if n < 50:
        return sorted(arr)
    H = structural_entropy(arr)
    if H < 0.15:
        return worst_case_sort(arr)
    return sorted(arr)


def worst_case_sort(arr):
    """Deliberately heavy O(n²) path — showcases the penalty for low entropy."""
    result = []
    n = len(arr)
    for i in range(n):
        for j in range(n - i):
            _ = j * j
        result.append(arr[i])
    return result


def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left  = [x for x in arr if x <  pivot]
    mid   = [x for x in arr if x == pivot]
    right = [x for x in arr if x >  pivot]
    return quick_sort(left) + mid + quick_sort(right)


def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    return _merge(merge_sort(arr[:mid]), merge_sort(arr[mid:]))


def _merge(left, right):
    res, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if left[i] < right[j]:
            res.append(left[i]); i += 1
        else:
            res.append(right[j]); j += 1
    return res + left[i:] + right[j:]


def insertion_sort(arr):
    arr = arr.copy()
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr


ALGORITHMS = {
    "Entropy-Aware": entropy_aware_sort,
    "Quick Sort":    quick_sort,
    "Merge Sort":    merge_sort,
    "Insertion Sort": insertion_sort,
}



# 4. BENCHMARKING


def measure_time(func, arr, repeat=3):
    """Average wall-clock time over `repeat` runs (seconds)."""
    times = []
    for _ in range(repeat):
        temp = arr.copy()
        start = time.perf_counter()
        func(temp)
        times.append(time.perf_counter() - start)
    return sum(times) / len(times)



# 5. ANALYSIS ENGINE


def run_analysis(datasets, reps=2):
    """
    Given { category: [array, ...] }, compute the full benchmark.
    Returns the JSON-serialisable result dict consumed by the frontend.
    """
    category_results = {}
    entropy_levels   = {}

    for category, arrays in datasets.items():
        H = structural_entropy(arrays[0])
        entropy_levels[category] = H

        algo_times = {name: [] for name in ALGORITHMS}
        for arr in arrays:
            for name, fn in ALGORITHMS.items():
                t = measure_time(fn, arr, repeat=reps)
                algo_times[name].append(t)

        avg_times = {name: sum(v) / len(v) for name, v in algo_times.items()}
        best_algo = min(avg_times, key=avg_times.get)

        category_results[category] = {
            "entropy":       round(H, 4),
            "entropy_label": interpret_entropy(H),
            "times":         {algo: round(t * 1000, 4) for algo, t in avg_times.items()},
            "times_sec":     {algo: round(t, 6) for algo, t in avg_times.items()},
            "best":          best_algo,
        }

    # Speed wins
    win_count = {name: 0 for name in ALGORITHMS}
    for cat_data in category_results.values():
        win_count[cat_data["best"]] += 1

    # Adaptability bonus — Entropy-Aware earns a point for extreme-entropy categories
    adaptive_bonus = {name: 0 for name in ALGORITHMS}
    for H in entropy_levels.values():
        if H < 0.1 or H >= 0.5:
            adaptive_bonus["Entropy-Aware"] += 1

    # Final score
    final_score = {
        name: win_count[name] + adaptive_bonus[name]
        for name in ALGORITHMS
    }
    best_overall = max(final_score, key=final_score.get)

    # Robustness: variation of times across categories (lower = more stable)
    robustness = {}
    for name in ALGORITHMS:
        vals = [category_results[c]["times_sec"][name] for c in category_results]
        robustness[name] = round((max(vals) - min(vals)) * 1000, 4) if vals else 0

    return {
        "categories":     list(category_results.keys()),
        "results":        category_results,
        "win_count":      win_count,
        "adaptive_bonus": adaptive_bonus,
        "final_score":    final_score,
        "best_overall":   best_overall,
        "robustness":     robustness,
        "entropy_levels": {k: round(v, 4) for k, v in entropy_levels.items()},
    }


# 6. API ROUTES
# 
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/categories", methods=["GET"])
def get_categories():
    """Return available category names for the dataset folder."""
    folder = request.args.get("folder", "dataset")
    if not os.path.isdir(folder):
        return jsonify({"error": f"Folder '{folder}' not found", "categories": []}), 404

    categories = [
        d for d in sorted(os.listdir(folder))
        if os.path.isdir(os.path.join(folder, d))
    ]
    return jsonify({"folder": folder, "categories": categories})


@app.route("/api/run-analysis", methods=["POST"])
@app.route("/api/run-real-analysis", methods=["POST"])
def run_real_analysis():
    """
    Unified analysis endpoint.

    POST body (JSON) — two modes:

    1) Iris mode (default when no folder_path given or folder_path is "iris"):
       { "mode": "iris", "size": 1000, "reps": 3 }

    2) Folder mode:
       { "folder_path": "dataset", "max_files": 5, "reps": 2,
         "categories": ["cat1"]   // optional filter
       }
    """
    body = request.get_json(silent=True) or {}
    reps = int(body.get("reps", 2))

    folder_path = body.get("folder_path", "").strip()
    use_iris    = (not folder_path) or folder_path.lower() == "iris" or body.get("mode") == "iris"

    if use_iris:
        size     = int(body.get("size", 1000))
        datasets = get_iris_datasets(size)
        result   = run_analysis(datasets, reps=reps)
        result["data_source"] = "Iris Dataset (sklearn)"
        result["array_size"]  = size
        return jsonify(result)

    # Folder mode
    max_files   = int(body.get("max_files", 5))
    filter_cats = body.get("categories")

    if not os.path.isdir(folder_path):
        return jsonify({
            "error": f"Dataset folder '{folder_path}' not found. "
                     f"Make sure it exists relative to where you run app.py."
        }), 404

    datasets = load_dataset(folder_path, max_files_per_category=max_files)

    if not datasets:
        return jsonify({
            "error": "No valid data found in dataset folder. "
                     "Each sub-folder should contain .txt files with one number per line."
        }), 422

    if filter_cats:
        datasets = {k: v for k, v in datasets.items() if k in filter_cats}
        if not datasets:
            return jsonify({"error": "None of the requested categories were found."}), 404

    result = run_analysis(datasets, reps=reps)
    result["data_source"] = "Real Dataset"
    return jsonify(result)



# 7. ENTRY POINT


if __name__ == "__main__":
    print("=" * 55)
    print("  Entropy-Aware Sort Dashboard")
    print("  http://localhost:5000")
    print("=" * 55)
    app.run(debug=True, port=5000)
