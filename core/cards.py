from .models import *


def monthly_revenue_card():
    import pandas as pd
    tx_data = pd.DataFrame(list(Purchase.objects.all().values()))
    tx_data = tx_data.drop('id', axis=1)
    tx_data.columns = ['Description', 'UnitPrice', 'Quantity', 'InvoiceDate', 'CustomerID', 'InvoiceNo']
    tx_data['InvoiceDate'] = pd.to_datetime(tx_data['InvoiceDate'])
    tx_data['InvoiceYearMonth'] = tx_data['InvoiceDate'].map(lambda date: 100 * date.year + date.month)
    tx_data['Revenue'] = tx_data['UnitPrice'] * tx_data['Quantity']
    # first_and_second
    tx_revenue = tx_data.groupby(['InvoiceYearMonth'])['Revenue'].sum().reset_index()
    x = tx_revenue.loc[tx_revenue['InvoiceYearMonth'] == tx_revenue['InvoiceYearMonth'].max()]['Revenue'].values
    return int(x)


def annual_revenue_card():
    import pandas as pd
    tx_data = pd.DataFrame(list(Purchase.objects.all().values()))
    tx_data = tx_data.drop('id', axis=1)
    tx_data.columns = ['Description', 'UnitPrice', 'Quantity', 'InvoiceDate', 'CustomerID', 'InvoiceNo']
    # Изменяю колонку InvoiceDate на поле типа datetime
    tx_data['InvoiceDate'] = pd.to_datetime(tx_data['InvoiceDate'])
    tx_data['InvoiceDate'] = tx_data['InvoiceDate'].dt.year.astype(str) + '-' + tx_data[
        'InvoiceDate'].dt.month.astype(
        str) + '-' + tx_data['InvoiceDate'].dt.day.astype(str)
    tx_data['InvoiceDate'] = pd.to_datetime(tx_data['InvoiceDate'])
    # Создание поля YearMonth, которое содержит в себе год и месяц совершения покупки
    # #рассчет дохода от каждой покупки
    tx_data['Revenue'] = tx_data['UnitPrice'] * tx_data['Quantity']
    # #создание нового датафрейма с колонками InvoiceYearMonth и Revenue, где рассчитан доход за каждый месяц
    # tx_revenue = tx_data.groupby(['InvoiceYearMonth'])['Revenue'].sum().reset_index()
    # tx_revenue
    tx_annual = tx_data[(tx_data['InvoiceDate'].dt.year == tx_data['InvoiceDate'].dt.year.max())]
    tx_annual1 = tx_annual.groupby(tx_annual['InvoiceDate'].dt.year)['Revenue'].sum().reset_index()
    return '{:,}'.format(int(tx_annual1['Revenue'].values)).replace(',', ' ')
