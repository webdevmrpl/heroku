from __future__ import division
import pandas as pd
from sklearn.cluster import KMeans
import pickle

tx_data = pd.read_csv('data.csv', encoding='unicode_escape')
tx_data['InvoiceDate'] = pd.to_datetime(tx_data['InvoiceDate'])
tx_uk = tx_data.query("Country=='United Kingdom'").reset_index(drop=True)

tx_user = pd.DataFrame(tx_data['CustomerID'].unique())
tx_user.columns = ['CustomerID']

# Активность
tx_max_purchase = tx_uk.groupby('CustomerID')['InvoiceDate'].max().reset_index()
tx_max_purchase.columns = ['CustomerID', 'MaxPurchaseDate']
tx_max_purchase['Recency'] = (tx_max_purchase['MaxPurchaseDate'].max() - tx_max_purchase['MaxPurchaseDate']).dt.days
tx_user = pd.merge(tx_user, tx_max_purchase[['CustomerID', 'Recency']], on='CustomerID')
kmeans = KMeans(n_clusters=4)
kmeans.fit(tx_user[['Recency']])
filename = 'recency_cluster.sav'
pickle.dump(kmeans, open(filename, 'wb+'))


# Частота
tx_frequency = tx_uk.groupby('CustomerID').InvoiceDate.count().reset_index()
tx_frequency.columns = ['CustomerID', 'Frequency']
tx_user = pd.merge(tx_user, tx_frequency, on='CustomerID')
kmeans = KMeans(n_clusters=4)
kmeans.fit(tx_user[['Frequency']])
filename = 'frequency_cluster.sav'
pickle.dump(kmeans, open(filename, 'wb+'))
tx_user['FrequencyCluster'] = kmeans.predict(tx_user[['Frequency']])

# Доход
tx_uk['Revenue'] = tx_uk['UnitPrice'] * tx_uk['Quantity']
tx_revenue = tx_uk.groupby('CustomerID').Revenue.sum().reset_index()
tx_user = pd.merge(tx_user, tx_revenue, on='CustomerID')
kmeans = KMeans(n_clusters=4)
kmeans.fit(tx_user[['Revenue']])
filename = 'revenue_cluster.sav'
pickle.dump(kmeans, open(filename, 'wb+'))
tx_user['RevenueCluster'] = kmeans.predict(tx_user[['Revenue']])
