import datetime
import json
import math

import creds
import pandas as pd
import plotly.express as px
import requests
from dash import Dash, dcc, html, Input, Output

min_year = 1948
current_year = datetime.date.today().year

# LNS14000000 = Unemployment Rate (Seasonally Adjusted)
# CUUR0000AA0 = CPI for All Urban Consumers (CPI-U) 1967=100 (Unadjusted)
desired_series = ('LNS14000000',
                  'CUUR0000AA0')


def api_request(start_year, end_year):
    start_date = str(start_year)
    end_date = str(end_year)
    data = json.dumps(
        {"registrationkey": creds.api_key,
         "seriesid": desired_series,
         "startyear": start_date, "endyear": end_date,
         "calculations": "true"})

    headers = {'Content-type': 'application/json'}

    post = requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/', data=data, headers=headers)

    rdf = pd.DataFrame(columns=['seriesID', 'date', 'value', 'footnotes'])

    json_data = json.loads(post.text)
    for series in json_data['Results']['series']:
        series_id = series['seriesID']
        for item in series['data']:
            year_period_str = f"{item['period'][1:]}-01-{item['year']}"
            date = datetime.datetime.strptime(year_period_str, "%m-%d-%Y")
            value = item['value']
            footnotes = ""
            for footnote in item['footnotes']:
                if footnote:
                    footnotes = footnotes + footnote['text'] + ','
            rdf.loc[len(rdf.index)] = [series_id, date, value, footnotes[0:-1]]

    rdf['seriesID'] = rdf['seriesID'].astype(str)
    rdf['value'] = rdf['value'].astype(float)
    rdf['footnotes'] = rdf['footnotes'].astype(str)

    return rdf


def list_years():
    result = []
    num_periods = math.ceil((current_year - min_year) / 19)
    for x in range(0, num_periods + 1):
        if current_year - 19 * x < min_year:
            result.append(min_year)
        else:
            result.append(current_year - 19 * x)

    result.reverse()
    return result


def combine_dfs():
    years = list_years()
    period_dfs = []
    for x in range(0, len(years) + 1):
        if x < len(years) - 1:
            period_dfs.append(api_request(years[x], years[x + 1]))
    return pd.concat(period_dfs, axis=0)


df = combine_dfs()

df0 = df[df['seriesID'] == desired_series[0]].drop_duplicates('date').sort_values(by='date')

df1 = df[df['seriesID'] == desired_series[1]].drop_duplicates('date').sort_values(by='date')

app = Dash(__name__)

app.layout = html.Div([
    html.Div([
        html.Pre(children="Unemployment Rate (Seasonally Adjusted) Over Time",
                 style={"text-align": "center", "font-size": "100%", "color": "black"})
    ]),

    html.Div([
        dcc.Graph(id='unemployment_graph')
    ]),

    html.Div([
        dcc.RangeSlider(
            min=pd.DatetimeIndex(df['date']).year.min(),
            max=pd.DatetimeIndex(df['date']).year.max(),
            step=1,
            value=[pd.DatetimeIndex(df['date']).year.min(), pd.DatetimeIndex(df['date']).year.max()],
            tooltip={"placement": "bottom", "always_visible": True},
            marks=None,
            id='year_slider0'
        )
    ]),

    html.Div([
        html.Pre(children="CPI for All Urban Consumers (CPI-U) 1967=100 (Unadjusted)",
                 style={"text-align": "center", "font-size": "100%", "color": "black"})
    ]),
    html.Div([
        dcc.Graph(id='cpi_graph')
    ]), html.Div([
        dcc.RangeSlider(
            min=pd.DatetimeIndex(df['date']).year.min(),
            max=pd.DatetimeIndex(df['date']).year.max(),
            step=1,
            value=[pd.DatetimeIndex(df['date']).year.min(), pd.DatetimeIndex(df['date']).year.max()],
            tooltip={"placement": "bottom", "always_visible": True},
            marks=None,
            id='year_slider1'
        )
    ])
])


@app.callback(
    Output('unemployment_graph', 'figure'),
    [Input('year_slider0', 'value')]
)
def update_graph(years_chosen):
    dff = df0[(pd.DatetimeIndex(df0['date']).year >= years_chosen[0]) & (
            pd.DatetimeIndex(df0['date']).year <= years_chosen[1])]

    unemployment_fig = px.line(data_frame=dff,
                               x='date',
                               y='value').update_layout(xaxis_title='Date',
                                                        yaxis_title='Unemployment Rate',
                                                        transition_duration=500)

    unemployment_fig.update_traces(textposition='top center')

    return unemployment_fig


@app.callback(
    Output('cpi_graph', 'figure'),
    [Input('year_slider1', 'value')]
)
def update_graph(years_chosen):
    dff = df1[(pd.DatetimeIndex(df1['date']).year >= years_chosen[0]) & (
            pd.DatetimeIndex(df1['date']).year <= years_chosen[1])]

    cpi_fig = px.line(data_frame=dff,
                      x='date',
                      y='value').update_layout(xaxis_title='Date',
                                               yaxis_title='CPI for All Urban Consumers (CPI-U)',
                                               transition_duration=500)

    cpi_fig.update_traces(textposition='top center')

    return cpi_fig


if __name__ == '__main__':
    app.run_server(debug=True)
