import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn

csv = pd.read_csv('heart.csv') # test file, target is the regression target
#print(csv.head())

X = csv.drop("target", axis=1)
y = csv["target"]
#print(X.head())

#print(y.head(), y.value_counts())

from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.25)
#print(X_train.shape, X_test.shape, y_train.shape, y_test.shape)

from sklearn.ensemble import RandomForestClassifier
clf = RandomForestClassifier()
#print(clf.get_params())

clf.fit(X=X_train, y=y_train)

y_pred = clf.predict(X=X_test)

train_accuracy = clf.score(X=X_train, y=y_train)
print(f"Model Accuracy on training dataset: {train_accuracy*100}%")

test_accuracy = clf.score(X=X_test, y=y_test)
print(f"Model Accuracy on testing dataset: {test_accuracy*100:.2f}%")

from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
print(classification_report(y_test, y_pred))

conf_matrix = confusion_matrix(y_test, y_pred)
#print(conf_matrix)

print(accuracy_score(y_test, y_pred))

np.random.seed(100)
'''

for i in range(100, 200, 10):
    print(f"Trying model with {i} estimators...")
    model = RandomForestClassifier(n_estimators=i).fit(X_train, y_train)
    print(f"Model accuracy on test dataset: {model.score(X_test, y_test)*100:.2f}%")
    print()
'''

from sklearn.model_selection import cross_val_score


for i in range(100, 200, 10):
    print(f"Trying model with {i} estimators...")
    model = RandomForestClassifier(n_estimators=i).fit(X_train, y_train)
    model_score = model.score(X_test, y_test)
    cross_val_mean = np.mean(cross_val_score(model, X, y, cv=5)) #5 different training sets
    print(f"Five-fold validation score: {cross_val_mean*100:.2f}%")
    print()

from sklearn.model_selection import GridSearchCV
param_grid = {'n_estimators': [i for i in range(100, 200, 10)]}

grid = GridSearchCV(estimator=RandomForestClassifier(), param_grid=param_grid, cv=5, verbose=1)
grid.fit(X, y)
print(f"Best parameters: {grid.best_params_}")
print(f"Best score: {grid.best_score_*100:.2f}%")

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
