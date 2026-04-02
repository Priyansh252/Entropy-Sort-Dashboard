# entropy-sort-dashboard

**A Flask-powered dashboard that benchmarks sorting algorithms using entropy analysis to determine which algorithm performs best based on the disorder level of your data.**

---

## What It Does

The Entropy-Aware Sort Dashboard measures the "disorder" (entropy) of numerical datasets and benchmarks four sorting algorithms — Entropy-Aware, Quick Sort, Merge Sort, and Insertion Sort — against each other. The key insight is that the best sorting algorithm depends on how shuffled your data already is: nearly-sorted data has different ideal algorithms than completely random data.

The dashboard visualizes:
- **Entropy level** of each dataset category (Low / Medium / High)
- **Execution time** per algorithm per category
- **Robustness** (timing variance across categories)
- **Scorecard** with speed wins and adaptability bonus per algorithm

---

## Project Structure

```
entropy-sort-dashboard/
├── app.py                  # Flask backend — entropy engine, sorting algorithms, API
└── templates/
    └── index.html          # Frontend dashboard (Chart.js, vanilla JS)
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/entropy-sort-dashboard.git
cd entropy-sort-dashboard
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
python app.py
```

Then open [http://localhost:5000](http://localhost:5000) in your browser.

---

## Usage

### Iris Mode (default)
Uses scikit-learn's Iris dataset to generate three pre-built entropy categories (Low, Medium, High). No extra setup needed — just run and explore.
you can access it from here:https://archive.ics.uci.edu/dataset/53/iris
### Folder Mode
Point the dashboard at a local folder containing sub-directories of `.txt` files (one number per line). Each sub-directory becomes a dataset category.
you can access the tested dataset from here:https://www.kaggle.com/datasets/bekiremirhanakay/benchmark-dataset-for-sorting-algorithms
```
dataset/
├── category_a/
│   ├── file1.txt
│   └── file2.txt
└── category_b/
    └── data.txt
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/categories` | List available dataset categories from a folder |
| `POST` | `/api/run-analysis` | Run full entropy + sorting benchmark |
| `POST` | `/api/run-real-analysis` | Alias for the above |

### Example request (Iris mode)
```json
POST /api/run-analysis
{
  "mode": "iris",
  "size": 1000,
  "reps": 3
}
```

### Example request (Folder mode)
```json
POST /api/run-analysis
{
  "folder_path": "dataset",
  "max_files": 5,
  "reps": 2
}
```

---

## Algorithms

| Algorithm | Strategy |
|-----------|----------|
| **Entropy-Aware** | Detects disorder level and routes to the optimal sort path |
| **Quick Sort** | Classic divide-and-conquer |
| **Merge Sort** | Stable divide-and-conquer |
| **Insertion Sort** | Efficient for small or nearly-sorted arrays |

The Entropy-Aware algorithm earns an **adaptability bonus** in scoring for datasets with extreme entropy values (very low or very high disorder).

---

## Requirements

- Python 3.8+
- Flask
- scikit-learn

See `requirements.txt` for the full list.

---

## License

MIT
