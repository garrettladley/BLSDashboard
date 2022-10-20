import datetime
import json
import math

import pandas as pd
import plotly.express as px
import requests
from dash import Dash, dcc, html, Input, Output

import creds

# LNS14000000 = Unemployment Rate (Seasonally Adjusted)
# CUUR0000AA0 = CPI for All Urban Consumers (CPI-U) 1967=100 (Unadjusted)
desired_series = ('LNS14000000',
                  'CUUR0000AA0')


# Request that will retrieve data from the BLS Public Data API
def api_request(start_year, end_year):
    # hide my API key in an untracked credentials file
    data = json.dumps(
        {'registrationkey': creds.api_key,
         'seriesid': desired_series,
         'startyear': str(start_year), 'endyear': str(end_year),
         'calculations': 'false'})

    headers = {'Content-type': 'application/json'}

    post = requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/', data=data, headers=headers)

    return process_json_data(json.loads(post.text))


# process JSON from API request, convert to desired data types
def process_json_data(post_text):
    the_df = pd.DataFrame(columns=['seriesID', 'date', 'value'])
    for series in post_text['Results']['series']:
        series_id = str(series['seriesID'])
        for item in series['data']:
            year_period_str = f"{item['period'][1:]}-01-{item['year']}"
            date = datetime.datetime.strptime(year_period_str, '%m-%d-%Y')
            value = float(item['value'])
            the_df.loc[len(the_df.index)] = [series_id, date, value]
    return the_df


# API limits requests to a difference of 19 years, create a dataframe with batches of years 19 apart from the
# min_year to the max_year
def list_years(min_year, max_year):
    # if the years are equal, just return a list of length 1
    # design decision to return min_year
    if min_year == max_year:
        return [min_year]
    if min_year > max_year:
        raise ValueError('min_year must be less than or equal to max_year')
    result = []
    num_periods = math.ceil((max_year - min_year) / 19)
    for x in range(0, num_periods + 1):
        if max_year - 19 * x < min_year:
            result.append(min_year)
        else:
            result.append(max_year - 19 * x)

    result.reverse()
    return result


# Combine the requests into 1 dataframe
def combine_dfs():
    # 1948 is the minimum year present in the BLS data
    years = list_years(1948, datetime.date.today().year)
    period_dfs = []
    for x in range(0, len(years) + 1):
        if x < len(years) - 1:
            period_dfs.append(api_request(years[x], years[x + 1]))
    return pd.concat(period_dfs, axis=0)


df = combine_dfs()

# the first of the desired series, LNS14000000,
# dropping duplicate dates and sorting by date to allow for efficient plotting
df0 = df[df['seriesID'] == desired_series[0]].drop_duplicates('date').sort_values(by='date')

# the second of the desired series, CUUR0000AA0,
# dropping duplicate dates and sorting by date to allow for efficient plotting
df1 = df[df['seriesID'] == desired_series[1]].drop_duplicates('date').sort_values(by='date')

# Plotly dash
app = Dash(__name__)

app.layout = html.Div([
    # unemployment graph title
    html.Div([
        html.Pre(children='Unemployment Rate (Seasonally Adjusted) Over Time',
                 style={'text-align': 'center', 'font-size': '100%', 'color': 'black'})
    ]),
    # unemployment graph
    html.Div([
        dcc.Graph(id='unemployment_graph')
    ]),
    # slider for unemployment graph
    html.Div([
        dcc.RangeSlider(
            min=pd.DatetimeIndex(df['date']).year.min(),
            max=pd.DatetimeIndex(df['date']).year.max(),
            step=1,
            value=[pd.DatetimeIndex(df['date']).year.min(), pd.DatetimeIndex(df['date']).year.max()],
            tooltip={'placement': 'bottom', 'always_visible': True},
            marks=None,
            id='year_slider0'
        )
    ]),
    # cpi graph title
    html.Div([
        html.Pre(children='CPI for All Urban Consumers (CPI-U) 1967=100 (Unadjusted)',
                 style={'text-align': 'center', 'font-size': '100%', 'color': 'black'})
    ]),
    # cpi graph
    html.Div([
        dcc.Graph(id='cpi_graph')
    ]),
    # slider range for cpi graph
    html.Div([
        dcc.RangeSlider(
            min=pd.DatetimeIndex(df['date']).year.min(),
            max=pd.DatetimeIndex(df['date']).year.max(),
            step=1,
            value=[pd.DatetimeIndex(df['date']).year.min(), pd.DatetimeIndex(df['date']).year.max()],
            tooltip={'placement': 'bottom', 'always_visible': True},
            marks=None,
            id='year_slider1'
        )
    ])
])


# update unemployment graph based on rangeslider
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


# update cpi graph based on rangeslider
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
