# compares results from prompting the LLM with truncated page text versus
# full page text
# usage: uv run --with pandas --with scikit-learn --no-project validate_truncated_results.py <dataset_csv_path>

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_auc_score
)
import sys

if len(sys.argv) < 1:
    print("missing dataset csv path argument.")
    print("Usage: uv run --with pandas --no-project validate_truncated_results.py <dataset_csv_path>")
    sys.exit(1)

dataset_csv_path=sys.argv[1]

df = pd.read_csv(dataset_csv_path)
print(f"Analyzing {len(df)} samples")
df["personal_blog"] = df["personal_blog"].map({True: 1, False: 0})
df["personal_blog_1000"] = df["personal_blog_1000"].map({True: 1, False: 0})

print()
print("----------")
print("Class balance (personal_blog)")
pct_true = len(df[df['personal_blog'] == 1]) / len(df)
pct_false = len(df[df['personal_blog'] == 0]) / len(df)
print("True: ", pct_true)
print("False: ", pct_false)

print()
print("----------")
print("Class balance (personal_blog_1000)")
pct_true = len(df[df['personal_blog_1000'] == 1]) / len(df)
pct_false = len(df[df['personal_blog_1000'] == 0]) / len(df)
print("True: ", pct_true)
print("False: ", pct_false)

y_true = []
y_pred = []

for _, row in df.iterrows():
    y_true.append(row["personal_blog"])
    y_pred.append(row["personal_blog_1000"])

accuracy = accuracy_score(y_true, y_pred)
precision = precision_score(y_true, y_pred)
recall = recall_score(y_true, y_pred)
f1 = f1_score(y_true, y_pred)
cm = confusion_matrix(y_true, y_pred)

print()
print("----------")
print("Accuracy:", accuracy)
print("Precision:", precision)
print("Recall:", recall)
print("F1:", f1)
print("Confusion Matrix:\n", cm)

print()
print("----------")
false_negative = df[(df['personal_blog'] == 1) & (df['personal_blog_1000'] == 0)]
if not false_negative.empty:
    print("Example false negative:")
    print(false_negative.iloc[0])
else:
    print("No false negatives.")

false_positive = df[(df['personal_blog'] == 0) & (df['personal_blog_1000'] == 1)]
if not false_positive.empty:
    print("Example false positive:")
    print(false_positive.iloc[0])
else:
    print("No false positives.")
