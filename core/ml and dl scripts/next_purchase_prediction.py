from __future__ import division

import pickle
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import xgboost as xgb
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split

tx_data = pd.read_csv('data.csv', encoding='unicode_escape')

tx_data['InvoiceDate'] = pd.to_datetime(tx_data['InvoiceDate'])

tx_uk = tx_data.query("Country=='United Kingdom'").reset_index(drop=True)

# Беру информацию за 6 месяцев
tx_6m = tx_uk[(tx_uk.InvoiceDate < datetime(2011, 9, 1)) & (tx_uk.InvoiceDate >= datetime(2011, 3, 1))].reset_index(
    drop=True)
# Делаю предсказание на следующие три месяца
tx_next = tx_uk[(tx_uk.InvoiceDate >= datetime(2011, 9, 1)) & (tx_uk.InvoiceDate < datetime(2011, 12, 1))].reset_index(
    drop=True)

tx_user = pd.DataFrame(tx_6m['CustomerID'].unique())
tx_user.columns = ['CustomerID']

# Дата первой покупки в последующие три месяца
tx_next_first_purchase = tx_next.groupby('CustomerID').InvoiceDate.min().reset_index()
tx_next_first_purchase.columns = ['CustomerID', 'MinPurchaseDate']

# Дата последней покупки в исследуемых 6 месяцах
tx_last_purchase = tx_6m.groupby('CustomerID').InvoiceDate.max().reset_index()
tx_last_purchase.columns = ['CustomerID', 'MaxPurchaseDate']

# Слияние датафреймов
tx_purchase_dates = pd.merge(tx_last_purchase, tx_next_first_purchase, on='CustomerID', how='left')

# Рассчет разницы дат покупки
tx_purchase_dates['NextPurchaseDay'] = (
        tx_purchase_dates['MinPurchaseDate'] - tx_purchase_dates['MaxPurchaseDate']).dt.days

# Слияние с основным датафреймом
tx_user = pd.merge(tx_user, tx_purchase_dates[['CustomerID', 'NextPurchaseDay']], on='CustomerID', how='left')

tx_user = tx_user.fillna(999)

# Создание датафрейма с последней датой покупки
tx_max_purchase = tx_6m.groupby('CustomerID').InvoiceDate.max().reset_index()
tx_max_purchase.columns = ['CustomerID', 'MaxPurchaseDate']

# Нахожу последнюю дату покупки и добавляю ее к пользователю
tx_max_purchase['Recency'] = (tx_max_purchase['MaxPurchaseDate'].max() - tx_max_purchase['MaxPurchaseDate']).dt.days
tx_user = pd.merge(tx_user, tx_max_purchase[['CustomerID', 'Recency']], on='CustomerID')

# Кластеризация Recency
with open('recency_cluster.sav', 'rb') as f:
    kmeans = pickle.load(f)
tx_user['RecencyCluster'] = kmeans.predict(tx_user[['Recency']])


# Сортировка кластеров
def order_cluster(cluster_field_name, target_field_name, df, ascending):
    new_cluster_field_name = 'new_' + cluster_field_name
    df_new = df.groupby(cluster_field_name)[target_field_name].mean().reset_index()
    df_new = df_new.sort_values(by=target_field_name, ascending=ascending).reset_index(drop=True)
    df_new['index'] = df_new.index
    df_final = pd.merge(df, df_new[[cluster_field_name, 'index']], on=cluster_field_name)
    df_final = df_final.drop([cluster_field_name], axis=1)
    df_final = df_final.rename(columns={"index": cluster_field_name})
    return df_final


# Сортировка Recency кластеров
tx_user = order_cluster('RecencyCluster', 'Recency', tx_user, False)

# Общее количетсво купленных товаров по датам
tx_frequency = tx_6m.groupby('CustomerID').InvoiceDate.count().reset_index()
tx_frequency.columns = ['CustomerID', 'Frequency']

# Добавление Frequency к tx_user
tx_user = pd.merge(tx_user, tx_frequency, on='CustomerID')

# Кластеризация для Frequency
with open('frequency_cluster.sav', 'rb') as f:
    kmeans = pickle.load(f)
tx_user['FrequencyCluster'] = kmeans.predict(tx_user[['Frequency']])

# Сортировка кластеров Frequency
tx_user = order_cluster('FrequencyCluster', 'Frequency', tx_user, True)

# Расчет доходр от каждого пользователя
tx_6m['Revenue'] = tx_6m['UnitPrice'] * tx_6m['Quantity']
tx_revenue = tx_6m.groupby('CustomerID').Revenue.sum().reset_index()
tx_user = pd.merge(tx_user, tx_revenue, on='CustomerID')

# Кластеризация для Revenue
with open('revenue_cluster.sav', 'rb') as f:
    kmeans = pickle.load(f)
tx_user['RevenueCluster'] = kmeans.predict(tx_user[['Revenue']])

# Сортировка кластеров Revenue
tx_user = order_cluster('RevenueCluster', 'Revenue', tx_user, True)
tx_user.groupby('RevenueCluster')['Revenue'].describe()

# Создание колонки с общим счетом
tx_user['OverallScore'] = tx_user['RecencyCluster'] + tx_user['FrequencyCluster'] + tx_user['RevenueCluster']

# Разбиение на подгруппы
tx_user['Segment'] = 'Low-Value'
tx_user.loc[tx_user['OverallScore'] > 2, 'Segment'] = 'Mid-Value'
tx_user.loc[tx_user['OverallScore'] > 4, 'Segment'] = 'High-Value'

# Создание датафрейма
tx_day_order = tx_6m[['CustomerID', 'InvoiceDate']]

# InvoceDate в дни
tx_day_order['InvoiceDay'] = tx_6m['InvoiceDate'].dt.date
tx_day_order = tx_day_order.sort_values(['CustomerID', 'InvoiceDate'])
# Удаление дупликатов
tx_day_order = tx_day_order.drop_duplicates(subset=['CustomerID', 'InvoiceDay'], keep='first')

tx_day_order['PrevInvoiceDate'] = tx_day_order.groupby('CustomerID')['InvoiceDay'].shift(1)
tx_day_order['T2InvoiceDate'] = tx_day_order.groupby('CustomerID')['InvoiceDay'].shift(2)
tx_day_order['T3InvoiceDate'] = tx_day_order.groupby('CustomerID')['InvoiceDay'].shift(3)

tx_day_order['DayDiff'] = (tx_day_order['InvoiceDay'] - tx_day_order['PrevInvoiceDate']).dt.days
tx_day_order['DayDiff2'] = (tx_day_order['InvoiceDay'] - tx_day_order['T2InvoiceDate']).dt.days
tx_day_order['DayDiff3'] = (tx_day_order['InvoiceDay'] - tx_day_order['T3InvoiceDate']).dt.days

tx_day_diff = tx_day_order.groupby('CustomerID').agg({'DayDiff': ['mean', 'std']}).reset_index()
tx_day_diff.columns = ['CustomerID', 'DayDiffMean', 'DayDiffStd']
tx_day_order_last = tx_day_order.drop_duplicates(subset=['CustomerID'], keep='last')

tx_day_order_last = tx_day_order_last.dropna()
tx_day_order_last = pd.merge(tx_day_order_last, tx_day_diff, on='CustomerID')
tx_user = pd.merge(tx_user,
                   tx_day_order_last[['CustomerID', 'DayDiff', 'DayDiff2', 'DayDiff3', 'DayDiffMean', 'DayDiffStd']],
                   on='CustomerID')
tx_class = tx_user.copy()
tx_class = pd.get_dummies(tx_class)

tx_class['NextPurchaseDayRange'] = 2
tx_class.loc[tx_class.NextPurchaseDay > 20, 'NextPurchaseDayRange'] = 1
tx_class.loc[tx_class.NextPurchaseDay > 50, 'NextPurchaseDayRange'] = 0

tx_class = tx_class.drop('NextPurchaseDay',axis=1)
X, y = tx_class.drop('NextPurchaseDayRange',axis=1), tx_class.NextPurchaseDayRange
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=44)

xgb_model = xgb.XGBClassifier(max_depth=3,min_child_weight=5).fit(X_train, y_train)
filename = 'next_purchase_day_predict.sav'
pickle.dump(xgb_model, open(filename, 'wb+'))
