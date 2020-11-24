from .models import *
from plotly.offline import plot
import plotly.graph_objs as go


def monthly_revenue():
    import pandas as pd
    tx_data = pd.DataFrame(list(Purchase.objects.all().values()))
    tx_data = tx_data.drop('id', axis=1)
    tx_data.columns = ['Description', 'UnitPrice', 'Quantity', 'InvoiceDate', 'CustomerID', 'InvoiceNo']
    tx_data['InvoiceDate'] = pd.to_datetime(tx_data['InvoiceDate'])
    tx_data['InvoiceYearMonth'] = tx_data['InvoiceDate'].map(lambda date: 100 * date.year + date.month)
    tx_data['Revenue'] = tx_data['UnitPrice'] * tx_data['Quantity']
    # first_and_second
    tx_revenue = tx_data.groupby(['InvoiceYearMonth'])['Revenue'].sum().reset_index()
    tx_revenue['MonthlyGrowth'] = tx_revenue['Revenue'].pct_change()
    ###
    tx_uk = tx_data
    # Активные пользователи за месяц/monthly_active_customers
    tx_monthly_active = tx_uk.groupby('InvoiceYearMonth')['CustomerID'].nunique().reset_index()
    ###
    # Общее количество купленных товаров/total_purchased_items
    tx_monthly_sales = tx_uk.groupby('InvoiceYearMonth')['Quantity'].sum().reset_index()
    ###
    # Средний чек за месяц($)/monthly_order_average
    tx_monthly_order_avg = tx_uk.groupby('InvoiceYearMonth')['Revenue'].mean().reset_index()
    ###

    tx_min_purchase = tx_uk.groupby('CustomerID').InvoiceDate.min().reset_index()
    tx_min_purchase.columns = ['CustomerID', 'MinPurchaseDate']
    tx_min_purchase['MinPurchaseYearMonth'] = tx_min_purchase['MinPurchaseDate'].map(
        lambda date: 100 * date.year + date.month)
    tx_uk = pd.merge(tx_uk, tx_min_purchase, on='CustomerID')
    tx_uk['UserType'] = 'New'
    tx_uk.loc[tx_uk['InvoiceYearMonth'] > tx_uk['MinPurchaseYearMonth'], 'UserType'] = 'Existing'
    # Доход от пользователей в зависимости от их типа/new_vs_existing
    tx_user_type_revenue = tx_uk.groupby(['InvoiceYearMonth', 'UserType'])['Revenue'].sum().reset_index()
    ###
    tx_user_ratio = tx_uk.query("UserType == 'New'").groupby(['InvoiceYearMonth'])['CustomerID'].nunique() / \
                    tx_uk.query("UserType == 'Existing'").groupby(['InvoiceYearMonth'])['CustomerID'].nunique()
    tx_user_ratio = tx_user_ratio.reset_index()
    # Соотношений кол-ва новых пользователей к старым/new_customer_ratio
    tx_user_ratio = tx_user_ratio.dropna()
    ###

    tx_user_purchase = tx_uk.groupby(['CustomerID', 'InvoiceYearMonth'])['Revenue'].sum().reset_index()
    tx_retention = pd.crosstab(tx_user_purchase['CustomerID'], tx_user_purchase['InvoiceYearMonth']).reset_index()
    months = tx_retention.columns[2:]
    retention_array = []
    for i in range(len(months) - 1):
        retention_data = {}
        selected_month = months[i + 1]
        prev_month = months[i]
        retention_data['InvoiceYearMonth'] = int(selected_month)
        retention_data['TotalUserCount'] = tx_retention[selected_month].sum()
        retention_data['RetainedUserCount'] = \
            tx_retention[(tx_retention[selected_month] > 0) & (tx_retention[prev_month] > 0)][selected_month].sum()
        retention_array.append(retention_data)

    tx_retention = pd.DataFrame(retention_array)
    # Процент активности клиентов/monthly_retention_rate
    tx_retention['RetentionRate'] = tx_retention['RetainedUserCount'] / tx_retention['TotalUserCount']
    ###
    return {'first_and_second': tx_revenue, 'monthly_active_customers': tx_monthly_active,
            'total_purchased_items': tx_monthly_sales, 'monthly_order_average': tx_monthly_order_avg,
            'new_vs_existing': tx_user_type_revenue, 'new_customer_ratio': tx_user_ratio,
            'monthly_retention_rate': tx_retention
            }


def monthly_revenue_scatter():
    tx_revenue = monthly_revenue()['first_and_second']
    trace = go.Scatter(
        x=tx_revenue['InvoiceYearMonth'],
        y=tx_revenue['Revenue'],
    )
    layout = go.Layout(
        xaxis={"type": "category"},
        title='Щомісячний прибуток'
    )
    fig = go.Figure(data=[trace], layout=layout)
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div


def monthly_growth_scatter():
    tx_revenue = monthly_revenue()['first_and_second']
    trace = go.Scatter(
        x=tx_revenue['InvoiceYearMonth'],
        y=tx_revenue['MonthlyGrowth'],
    )
    layout = go.Layout(
        xaxis={"type": "category"},
        title='Щомісячний ріст прибутку'
    )
    fig = go.Figure(data=[trace], layout=layout)
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div


def monthly_active_customers_scatter():
    tx_monthly_active = monthly_revenue()['monthly_active_customers']
    trace = go.Scatter(
        x=tx_monthly_active['InvoiceYearMonth'],
        y=tx_monthly_active['CustomerID'],
    )
    layout = go.Layout(
        xaxis={"type": "category"},
        title='Активні користувачі за місяць'
    )
    fig = go.Figure(data=[trace], layout=layout)
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div


def total_purchased_items_scatter():
    tx_monthly_sales = monthly_revenue()['total_purchased_items']
    trace = go.Scatter(
        x=tx_monthly_sales['InvoiceYearMonth'],
        y=tx_monthly_sales['Quantity'],
    )

    layout = go.Layout(
        xaxis={"type": "category"},
        title='Загальна кількість придбаних товарів'
    )
    fig = go.Figure(data=[trace], layout=layout)
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div


def monthly_order_average_scatter():
    tx_monthly_order_avg = monthly_revenue()['monthly_order_average']
    trace = go.Scatter(
        x=tx_monthly_order_avg['InvoiceYearMonth'],
        y=tx_monthly_order_avg['Revenue'],
    )

    layout = go.Layout(
        xaxis={"type": "category"},
        title='Середній чек за місяць'
    )
    fig = go.Figure(data=[trace], layout=layout)
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div


def new_vs_existing_scatter():
    tx_user_type_revenue = monthly_revenue()['new_vs_existing']
    trace = [
        go.Scatter(
            x=tx_user_type_revenue.query("UserType == 'Existing' and InvoiceYearMonth>201912")['InvoiceYearMonth'],
            y=tx_user_type_revenue.query("UserType == 'Existing' and InvoiceYearMonth>201912")['Revenue'],
            name='Старі користувачі'
        ),
        go.Scatter(
            x=tx_user_type_revenue.query("UserType == 'New' and InvoiceYearMonth>201912")['InvoiceYearMonth'],
            y=tx_user_type_revenue.query("UserType == 'New' and InvoiceYearMonth>201912")['Revenue'],
            name='Нові користувачі'
        )
    ]
    layout = go.Layout(
        xaxis={"type": "category"},
        title='Прибуток від користувача в залежності від їх типу'
    )
    fig = go.Figure(data=trace, layout=layout)
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div


def new_customer_ratio_scatter():
    tx_user_ratio = monthly_revenue()['new_customer_ratio']
    trace = go.Line(
        x=tx_user_ratio['InvoiceYearMonth'],
        y=tx_user_ratio['CustomerID'],
    )

    layout = go.Layout(
        xaxis={"type": "category"},
        title='Відношення кількості нових користувачів до старих'
    )
    fig = go.Figure(data=[trace], layout=layout)
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div


def monthly_retention_rate_scatter():
    tx_retention = monthly_revenue()['monthly_retention_rate']
    trace = go.Scatter(
        x=tx_retention['InvoiceYearMonth'],
        y=tx_retention['RetentionRate'],
    )

    layout = go.Layout(
        xaxis={"type": "category"},
        title='Відсоток активності клієнтів'
    )
    fig = go.Figure(data=[trace], layout=layout)
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div


def monthly_active_customers_pie():
    night_colors = [ '#70b5bb', '#3b8f71', '#459c8c', '#64b6e3', '#57a9a6',
                    '#0081f1', '#009dec', '#a7ccdc', '#8bc1ce', '#0060ee', '#1d76a8', ]
    tx_monthly_active = monthly_revenue()['monthly_active_customers']
    trace = go.Pie(
        labels=tx_monthly_active['InvoiceYearMonth'],
        values=tx_monthly_active['CustomerID'],
        hole=.85,
        marker_colors=night_colors,

    )
    layout = go.Layout(
        xaxis={"type": "category"},
        title='Активні користувачі за місяць',
    )
    fig = go.Figure(data=[trace], layout=layout)
    fig.update_traces(hoverinfo='label+percent', textinfo='none')
    fig.update(layout_showlegend=False)
    fig.update_layout(
        hoverlabel=dict(
            font_size=12,
            font_family="Rockwell",
            font_color='White'
        )
    )
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div


def monthly_revenue_scatter_mainpage():
    tx_revenue = monthly_revenue()['first_and_second']
    trace = go.Scatter(
        x=tx_revenue['InvoiceYearMonth'],
        y=tx_revenue['Revenue'],
    )
    layout = go.Layout(
        xaxis={"type": "category"},
        title='Щомісячний прибуток',
        plot_bgcolor='rgb(255,255,255)'
    )
    fig = go.Figure(data=[trace], layout=layout)
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#D9D9D9')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#D9D9D9')
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div
