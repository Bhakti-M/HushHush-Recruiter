import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report ,confusion_matrix
file_path = "/content/Processed_GitHub_Data.csv"
df = pd.read_csv(file_path)

features = df.drop(columns=["Username"])

scaler = StandardScaler()
scaled_features = scaler.fit_transform(features)


kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
df["Cluster"] = kmeans.fit_predict(scaled_features)


numeric_cols = df.select_dtypes(include=[np.number]).columns
df_numeric = df[numeric_cols]
cluster_means = df_numeric.groupby("Cluster").mean().sum(axis=1)
good_cluster = cluster_means.idxmax()
df["Candidate_Label"] = df["Cluster"].apply(lambda x: "Good" if x == good_cluster else "Bad")


features_to_plot = ["Public Repos", "Followers", "Top Repositories", "Total Stars", "Total Pull Requests", "Total_Commits"]
df_transformed = df.copy()
for feature in features_to_plot:
    df_transformed[feature] = np.log1p(df[feature])


scaled_features_transformed = scaler.fit_transform(df_transformed[features_to_plot])
kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
df_transformed["Cluster"] = kmeans.fit_predict(scaled_features_transformed)


df_transformed_numeric = df_transformed[numeric_cols]
cluster_means_transformed = df_transformed_numeric.groupby("Cluster").mean().sum(axis=1)
good_cluster_transformed = cluster_means_transformed.idxmax()
df_transformed["Candidate_Label"] = df_transformed["Cluster"].apply(lambda x: "Good" if x == good_cluster_transformed else "Bad")

X = df_transformed[features_to_plot]
y = df_transformed["Candidate_Label"].map({"Good": 1, "Bad": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
clf_rf = RandomForestClassifier(n_estimators=100, random_state=42)
clf_rf.fit(X_train, y_train)
y_pred_rf = clf_rf.predict(X_test)


accuracy_rf = accuracy_score(y_test, y_pred_rf)
report_rf = classification_report(y_test, y_pred_rf)
print(f"Random Forest Accuracy: {accuracy_rf:.2f}\n")
print(report_rf)


conf_matrix_rf = confusion_matrix(y_test, y_pred_rf)
print("Confusion Matrix - Random Forest:")
print(conf_matrix_rf)


clf_gb = GradientBoostingClassifier(n_estimators=100, random_state=42)
clf_gb.fit(X_train, y_train)
y_pred_gb = clf_gb.predict(X_test)


accuracy_gb = accuracy_score(y_test, y_pred_gb)
report_gb = classification_report(y_test, y_pred_gb)
print(f"Gradient Boosting Accuracy: {accuracy_gb:.2f}\n")
print(report_gb)


conf_matrix_gb = confusion_matrix(y_test, y_pred_gb)
print("Confusion Matrix - Gradient Boosting:")
print(conf_matrix_gb)

model = report_gb


"""
df_transformed_numeric = df_transformed[numeric_cols]
cluster_means_transformed = df_transformed_numeric.groupby("Cluster").mean().sum(axis=1)
good_cluster_transformed = cluster_means_transformed.idxmax()
df_transformed["Candidate_Label"] = df_transformed["Cluster"].apply(lambda x: "Good" if x == good_cluster_transformed else "Bad")


X = df_transformed[features_to_plot]
y = df_transformed["Candidate_Label"].map({"Good": 1, "Bad": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)
y_pred = clf.predict(X_test)"""


candidate_counts = df_transformed["Candidate_Label"].value_counts()
print(candidate_counts)


plt.figure(figsize=(6, 4))
plt.bar(candidate_counts.index, candidate_counts.values, color=['red', 'green'])
plt.xlabel("Candidate Type")
plt.ylabel("Count")
plt.title("Distribution of Good and Bad Candidates")
plt.show()


fig, axes = plt.subplots(nrows=2, ncols=3, figsize=(15, 10))
axes = axes.flatten()
for i, feature in enumerate(features_to_plot):
    axes[i].hist(df[feature], bins=30, alpha=0.7, color='blue', edgecolor='black')
    axes[i].set_title(feature)
plt.tight_layout()
plt.show()

import pickle
MODEL_FILE = "/content/trained_model.pkl"  # Model save path
with open(MODEL_FILE, "wb") as model_file:
    pickle.dump(clf_gb, model_file)
    print("Model saved successfully!")
