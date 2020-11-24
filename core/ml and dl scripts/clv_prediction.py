from __future__ import division
from datetime import datetime
import pandas as pd
import xgboost as xgb
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
import pickle

tx_data = pd.read_csv('data.csv', encoding='unicode_escape')
tx_data['InvoiceDate'] = pd.to_datetime(tx_data['InvoiceDate'])
tx_uk = tx_data.query("Country=='United Kingdom'").reset_index(drop=True)

# Создание датафрейма за 3 и 6 месяцев активности
tx_3m = tx_uk[(tx_uk.InvoiceDate < datetime(2011, 6, 1)) & (tx_uk.InvoiceDate >= datetime(2011, 3, 1))].reset_index(
    drop=True)
tx_6m = tx_uk[(tx_uk.InvoiceDate >= datetime(2011, 6, 1)) & (tx_uk.InvoiceDate < datetime(2011, 12, 1))].reset_index(
    drop=True)

# Создание датафрейма для кластеризации
tx_user = pd.DataFrame(tx_3m['CustomerID'].unique())
tx_user.columns = ['CustomerID']


def order_cluster(cluster_field_name, target_field_name, df, ascending):
    new_cluster_field_name = 'new_' + cluster_field_name
    df_new = df.groupby(cluster_field_name)[target_field_name].mean().reset_index()
    df_new = df_new.sort_values(by=target_field_name, ascending=ascending).reset_index(drop=True)
    df_new['index'] = df_new.index
    df_final = pd.merge(df, df_new[[cluster_field_name, 'index']], on=cluster_field_name)
    df_final = df_final.drop([cluster_field_name], axis=1)
    df_final = df_final.rename(columns={"index": cluster_field_name})
    return df_final


# Рассчет активности
tx_max_purchase = tx_3m.groupby('CustomerID').InvoiceDate.max().reset_index()
tx_max_purchase.columns = ['CustomerID', 'MaxPurchaseDate']
tx_max_purchase['Recency'] = (tx_max_purchase['MaxPurchaseDate'].max() - tx_max_purchase['MaxPurchaseDate']).dt.days
tx_user = pd.merge(tx_user, tx_max_purchase[['CustomerID', 'Recency']], on='CustomerID')

kmeans = KMeans(n_clusters=4)
kmeans.fit(tx_user[['Recency']])
tx_user['RecencyCluster'] = kmeans.predict(tx_user[['Recency']])

tx_user = order_cluster('RecencyCluster', 'Recency', tx_user, False)

# Расчет частоты покупок
tx_frequency = tx_3m.groupby('CustomerID').InvoiceDate.count().reset_index()
tx_frequency.columns = ['CustomerID', 'Frequency']
tx_user = pd.merge(tx_user, tx_frequency, on='CustomerID')

kmeans = KMeans(n_clusters=4)
kmeans.fit(tx_user[['Frequency']])
tx_user['FrequencyCluster'] = kmeans.predict(tx_user[['Frequency']])

tx_user = order_cluster('FrequencyCluster', 'Frequency', tx_user, True)

# Расчет доходности
tx_3m['Revenue'] = tx_3m['UnitPrice'] * tx_3m['Quantity']
tx_revenue = tx_3m.groupby('CustomerID').Revenue.sum().reset_index()
tx_user = pd.merge(tx_user, tx_revenue, on='CustomerID')

kmeans = KMeans(n_clusters=4)
kmeans.fit(tx_user[['Revenue']])
tx_user['RevenueCluster'] = kmeans.predict(tx_user[['Revenue']])
tx_user = order_cluster('RevenueCluster', 'Revenue', tx_user, True)

# Общий итог
tx_user['OverallScore'] = tx_user['RecencyCluster'] + tx_user['FrequencyCluster'] + tx_user['RevenueCluster']
tx_user['Segment'] = 'Low-Value'
tx_user.loc[tx_user['OverallScore'] > 2, 'Segment'] = 'Mid-Value'
tx_user.loc[tx_user['OverallScore'] > 4, 'Segment'] = 'High-Value'


# ###############################################################################################################################################################################
# ###############################################################################################################################################################################
# ###############################################################################################################################################################################

# Расчет доходности и созданий датафрейма для нее

tx_6m['Revenue'] = tx_6m['UnitPrice'] * tx_6m['Quantity']
tx_user_6m = tx_6m.groupby('CustomerID')['Revenue'].sum().reset_index()
tx_user_6m.columns = ['CustomerID', 'm6_Revenue']

tx_merge = pd.merge(tx_user, tx_user_6m, on='CustomerID', how='left')
tx_merge = tx_merge.fillna(0)
# Удаление "лгунов"
tx_merge = tx_merge[tx_merge['m6_Revenue'] < tx_merge['m6_Revenue'].quantile(0.99)]

# Созщдание кластеров
kmeans = KMeans(n_clusters=3)
kmeans.fit(tx_merge[['m6_Revenue']])
tx_merge['LTVCluster'] = kmeans.predict(tx_merge[['m6_Revenue']])

# Сортировка номера LTV-кластера
tx_merge = order_cluster('LTVCluster', 'm6_Revenue', tx_merge, True)

# Содание нового датафрейма
tx_cluster = tx_merge.copy()

# Детали по кластеру
tx_cluster.groupby('LTVCluster')['m6_Revenue'].describe()

# Конвертация категорий в нумерацию
tx_class = pd.get_dummies(tx_cluster)

X = tx_class.drop(['LTVCluster', 'm6_Revenue'], axis=1)
y = tx_class['LTVCluster']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.05, random_state=56)

ltv_xgb_model = xgb.XGBClassifier(max_depth=5, learning_rate=0.1, objective='multi:softprob', n_jobs=-1).fit(X_train,
                                                                                                             y_train)
filename = 'clv_predict.sav'
pickle.dump(ltv_xgb_model, open(filename, 'wb+'))
