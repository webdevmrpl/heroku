from __future__ import division


def make_predictions(df_data):
    from sys import platform
    import pandas as pd
    import xgboost as xgb
    from sklearn.cluster import KMeans
    from sklearn.model_selection import train_test_split
    import pickle
    import warnings
    warnings.filterwarnings("ignore")
    df_data['InvoiceDate'] = pd.to_datetime(df_data['InvoiceDate'])

    # Создание датафрейма за 3 и 6 месяцев активности
    df_6m = df_data[(df_data.InvoiceDate >= pd.to_datetime('2020-01-01').tz_localize('UTC')) & (
            df_data.InvoiceDate < pd.to_datetime('2020-07-01').tz_localize('UTC'))].reset_index(drop=True)
    if 'Unnamed: 0' in df_6m:
        df_6m = df_6m.drop('Unnamed: 0', axis=1)
    # Создание датафрейма для кластеризации
    df_user = pd.DataFrame(df_data['CustomerID'].unique())
    df_user.columns = ['CustomerID']

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
    df_max_purchase = df_data.groupby('CustomerID').InvoiceDate.max().reset_index()
    df_max_purchase.columns = ['CustomerID', 'MaxPurchaseDate']
    df_max_purchase['Recency'] = (df_max_purchase['MaxPurchaseDate'].max() - df_max_purchase['MaxPurchaseDate']).dt.days
    df_user = pd.merge(df_user, df_max_purchase[['CustomerID', 'Recency']], on='CustomerID')
    df_max_purchase.max()
    if platform == 'win32':
        with open(r'scripts\recency_cluster.sav', 'rb') as f:
            kmeans = pickle.load(f)
    elif platform == 'linux' or platform == 'darwin':
        with open(r'scripts/recency_cluster.sav', 'rb') as f:
            kmeans = pickle.load(f)

    df_user['RecencyCluster'] = kmeans.predict(df_user[['Recency']])

    df_user = order_cluster('RecencyCluster', 'Recency', df_user, False)

    # Расчет частоты покупок
    df_frequency = df_data.groupby('CustomerID').InvoiceDate.count().reset_index()
    df_frequency.columns = ['CustomerID', 'Frequency']
    df_user = pd.merge(df_user, df_frequency, on='CustomerID')
    if platform == 'win32':
        with open(r'scripts\frequency_cluster.sav', 'rb') as f:
            kmeans1 = pickle.load(f)
    elif platform == 'darwin' or platform == 'linux':
        with open(r'scripts/frequency_cluster.sav', 'rb') as f:
            kmeans1 = pickle.load(f)

    df_user['FrequencyCluster'] = kmeans1.predict(df_user[['Frequency']])
    df_user = order_cluster('FrequencyCluster', 'Frequency', df_user, True)

    # Расчет доходности
    df_data['Revenue'] = df_data['UnitPrice'] * df_data['Quantity']
    df_revenue = df_data.groupby('CustomerID').Revenue.sum().reset_index()
    df_user = pd.merge(df_user, df_revenue, on='CustomerID')
    if platform == 'win32':
        with open(r'scripts\revenue_cluster.sav', 'rb') as f:
            kmeans2 = pickle.load(f)
    elif platform == 'linux' or platform == 'darwin':
        with open(r'scripts/revenue_cluster.sav', 'rb') as f:
            kmeans2 = pickle.load(f)
    df_user['RevenueCluster'] = kmeans2.predict(df_user[['Revenue']])
    df_user = order_cluster('RevenueCluster', 'Revenue', df_user, True)

    # Общий итог
    df_user['OverallScore'] = df_user['RecencyCluster'] + df_user['FrequencyCluster'] + df_user['RevenueCluster']
    df_user['Segment'] = 'Low-Value'
    df_user.loc[df_user['OverallScore'] > 2, 'Segment'] = 'Mid-Value'
    df_user.loc[df_user['OverallScore'] > 4, 'Segment'] = 'High-Value'

    # Создание датафрейма
    df_day_order = df_6m[['CustomerID', 'InvoiceDate']]

    # InvoceDate в дни
    df_day_order['InvoiceDay'] = df_6m['InvoiceDate'].dt.date
    df_day_order = df_day_order.sort_values(['CustomerID', 'InvoiceDate'])
    # #Удаление дупликатов
    df_day_order = df_day_order.drop_duplicates(subset=['CustomerID', 'InvoiceDay'], keep='first')

    df_day_order['PrevInvoiceDate'] = df_day_order.groupby('CustomerID')['InvoiceDay'].shift(1)
    df_day_order['T2InvoiceDate'] = df_day_order.groupby('CustomerID')['InvoiceDay'].shift(2)
    df_day_order['T3InvoiceDate'] = df_day_order.groupby('CustomerID')['InvoiceDay'].shift(3)

    df_day_order['DayDiff'] = (df_day_order['InvoiceDay'] - df_day_order['PrevInvoiceDate']).dt.days
    df_day_order['DayDiff2'] = (df_day_order['InvoiceDay'] - df_day_order['T2InvoiceDate']).dt.days
    df_day_order['DayDiff3'] = (df_day_order['InvoiceDay'] - df_day_order['T3InvoiceDate']).dt.days

    df_day_diff = df_day_order.groupby('CustomerID').agg({'DayDiff': ['mean', 'std']}).reset_index()
    df_day_diff.columns = ['CustomerID', 'DayDiffMean', 'DayDiffStd']
    df_day_order_last = df_day_order.drop_duplicates(subset=['CustomerID'], keep='last')

    df_day_order_last = df_day_order_last.dropna()
    df_day_order_last = pd.merge(df_day_order_last, df_day_diff, on='CustomerID')
    df_user = pd.merge(df_user, df_day_order_last[
        ['CustomerID', 'DayDiff', 'DayDiff2', 'DayDiff3', 'DayDiffMean', 'DayDiffStd']], on='CustomerID')

    df_class = df_user.copy()
    df_class = pd.get_dummies(df_class)

    def additional_data(data):
        if 'Segment_High-Value' not in data:
            data['Segment_High-Value'] = 0
        if 'Segment_Mid-Value' not in data:
            data['Segment_Mid-Value'] = 0
        if 'Segment_Low-Value' not in data:
            data['Segment_Low-Value'] = 0
        return data

    df_class = additional_data(df_class)
    df_class = df_class.reindex(['CustomerID', 'Recency', 'RecencyCluster', 'Frequency',
                                 'FrequencyCluster', 'Revenue', 'RevenueCluster', 'OverallScore',
                                 'DayDiff', 'DayDiff2', 'DayDiff3', 'DayDiffMean', 'DayDiffStd', 'Segment_High-Value',
                                 'Segment_Low-Value', 'Segment_Mid-Value'], axis='columns')

    # CLV предсказание
    if platform == 'win32':
        with open(r'scripts\clv_predict.sav', 'rb') as f:
            ltv_xgb_model = pickle.load(f)
    elif platform == 'linux' or platform == 'darwin':
        with open(r'scripts/clv_predict.sav', 'rb') as f:
            ltv_xgb_model = pickle.load(f)

    if 'LTVClusterPrediction' in df_class and 'NextPurchaseDayRange' in df_class:
        df_class['LTVClusterPrediction'] = ltv_xgb_model.predict(df_class.drop(
            ['DayDiff', 'DayDiff2', 'DayDiff3', 'DayDiffMean', 'DayDiffStd', 'LTVClusterPrediction',
             'NextPurchaseDayRange'], axis=1))
    elif 'NextPurchaseDayRange' in df_class:
        df_class['LTVClusterPrediction'] = ltv_xgb_model.predict(
            df_class.drop(['DayDiff', 'DayDiff2', 'DayDiff3', 'DayDiffMean', 'DayDiffStd', 'NextPurchaseDayRange'],
                          axis=1))
    elif 'LTVClusterPrediction' in df_class:
        df_class['LTVClusterPrediction'] = ltv_xgb_model.predict(
            df_class.drop(['DayDiff', 'DayDiff2', 'DayDiff3', 'DayDiffMean', 'DayDiffStd', 'LTVClusterPrediction'],
                          axis=1))
    else:
        df_class['LTVClusterPrediction'] = ltv_xgb_model.predict(
            df_class.drop(['DayDiff', 'DayDiff2', 'DayDiff3', 'DayDiffMean', 'DayDiffStd'], axis=1))

    # NPD предсказание
    if platform == 'win32':
        with open(r'scripts\next_purchase_day_predict.sav', 'rb') as f1:
            xgb_model = pickle.load(f1)
    elif platform == 'linux' or platform == 'darwin':
        with open(r'scripts/next_purchase_day_predict.sav', 'rb') as f1:
            xgb_model = pickle.load(f1)

    if 'LTVClusterPrediction' in df_class and 'NextPurchaseDayRange' in df_class:
        df_class['NextPurchaseDayRange'] = xgb_model.predict(
            df_class.drop(['LTVClusterPrediction', 'NextPurchaseDayRange'], axis=1))
    elif 'NextPurchaseDayRange' in df_class:
        df_class['NextPurchaseDayRange'] = xgb_model.predict(df_class.drop(['NextPurchaseDayRange'], axis=1))
    else:
        df_class['NextPurchaseDayRange'] = xgb_model.predict(df_class.drop(['LTVClusterPrediction'], axis=1))

    df_class = pd.merge(df_class, df_user[['CustomerID', 'Segment']], on='CustomerID')
    df_class = df_class.drop(
        ['Segment_High-Value', 'Segment_Low-Value', 'Segment_Mid-Value', 'DayDiff', 'DayDiff2', 'DayDiff3',
         'DayDiffMean', 'DayDiffStd'], axis=1)
    return df_class


def predict_sales(df_sales):
    import pandas as pd
    import numpy as np
    from keras.models import load_model
    import warnings
    warnings.filterwarnings("ignore")
    import pickle
    if 'Unnamed: 0' in df_sales.columns:
        df_sales = df_sales.drop('Unnamed: 0', axis=1)
    df_sales['invoice_date'] = pd.to_datetime(df_sales['invoice_date'])
    df_sales['invoice_date'] = df_sales['invoice_date'].dt.year.astype('str') + '-' + df_sales[
        'invoice_date'].dt.month.astype('str') + '-01'
    df_sales['invoice_date'] = pd.to_datetime(df_sales['invoice_date'])
    df_sales = df_sales.groupby('invoice_date').quantity.sum().reset_index()
    df_sales.columns = ['date', 'sales']
    df_diff = df_sales.copy()
    df_diff['prev_sales'] = df_diff['sales'].shift(1)
    df_diff = df_diff.dropna()
    df_diff['diff'] = (df_diff['sales'] - df_diff['prev_sales'])
    df_supervised = df_diff.drop(['prev_sales'], axis=1)
    for inc in range(1, 3):
        field_name = 'lag_' + str(inc)
        df_supervised[field_name] = df_supervised['diff'].shift(inc)
    df_supervised = df_supervised.dropna().reset_index(drop=True)
    df_supervised = df_diff.drop(['prev_sales'], axis=1)
    for inc in range(1, 3):
        field_name = 'lag_' + str(inc)
        df_supervised[field_name] = df_supervised['diff'].shift(inc)
    df_supervised = df_supervised.dropna().reset_index(drop=True)
    from sklearn.preprocessing import MinMaxScaler
    df_model = df_supervised.drop(['sales', 'date'], axis=1)
    test_set = df_model[-6:].values
    scaler = pickle.load(open('scaler.sav', 'rb'))
    test_set = test_set.reshape(test_set.shape[0], test_set.shape[1])
    test_set_scaled = scaler.transform(test_set)
    X_test = test_set_scaled[:, 1:]
    X_test = X_test.reshape(X_test.shape[0], 1, X_test.shape[1])
    model = load_model('model.h5')
    y_pred = model.predict(X_test, batch_size=1)
    y_pred = y_pred.reshape(y_pred.shape[0], 1, y_pred.shape[1])
    pred_test_set = []
    for index in range(0, len(y_pred)):
        print(np.concatenate([y_pred[index], X_test[index]], axis=1))
        pred_test_set.append(np.concatenate([y_pred[index], X_test[index]], axis=1))
    pred_test_set = np.array(pred_test_set)
    pred_test_set = pred_test_set.reshape(pred_test_set.shape[0], pred_test_set.shape[2])
    pred_test_set_inverted = scaler.inverse_transform(pred_test_set)
    result_list = []
    sales_dates = list(df_sales[-7:].date)
    act_sales = list(df_sales[-7:].sales)
    for index in range(0, len(pred_test_set_inverted)):
        result_dict = {}
        result_dict['pred_value'] = int(pred_test_set_inverted[index][0] + act_sales[index])
        result_dict['date'] = sales_dates[index + 1]
        result_list.append(result_dict)
    df_result = pd.DataFrame(result_list)
    df1 = df_sales[5::]
    df = pd.merge(df1, df_result, on='date')
    df['diff'] = df['sales'] - df['pred_value']
    df['date'] = df['date'].astype(str)
    return df
