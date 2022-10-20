import datetime
import json
import math

import pandas as pd
import plotly.express as px
import requests
from dash import Dash, dcc, html, Input, Output

import creds

desired_series = {'LNS14000000': 'Unemployment Rate (Seasonally Adjusted)',
                  'CUUR0000AA0': 'CPI for All Urban Consumers (CPI-U) 1967=100 (Unadjusted)'}


# Request that will retrieve data from the BLS Public Data API
def api_request(start_year, end_year):
    # hide my API key in an untracked credentials file
    data = json.dumps(
        {'registrationkey': creds.api_key,
         'seriesid': list(desired_series.keys()),
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


# separate combined dataframe by seriesID
def separate_series(input_series_id):
    # dropping duplicate dates and sorting by date to allow for efficient plotting
    return df[df['seriesID'] == input_series_id].drop_duplicates('date').sort_values(by='date')


# the first of the desired series, LNS14000000
df0 = separate_series(list(desired_series.keys())[0])

# the second of the desired series, CUUR0000AA0
df1 = separate_series(list(desired_series.keys())[1])

# Plotly dash
app = Dash(__name__)

# variables to be used within the dashboard
text_style = {'text-align': 'center', 'font-size': '100%', 'color': 'black'}
slider_min = pd.DatetimeIndex(df['date']).year.min()
slider_max = pd.DatetimeIndex(df['date']).year.max()
slider_value = [pd.DatetimeIndex(df['date']).year.min(), pd.DatetimeIndex(df['date']).year.max()]
slider_tooltip = {'placement': 'bottom', 'always_visible': True}


# gets the name of the series based on the index of the series
def series_name(series_index):
    return list(desired_series.values())[series_index]


# combines the name of the series with over time
def graph_namer(the_series_name):
    return the_series_name + ' Over Time'


app.layout = html.Div([
    # unemployment graph title
    html.Div([
        html.Pre(children=graph_namer(series_name(0)),
                 style=text_style)
    ]),
    # unemployment graph
    html.Div([
        dcc.Graph(id='unemployment_graph')
    ]),
    # slider for unemployment graph
    html.Div([
        dcc.RangeSlider(
            min=slider_min,
            max=slider_max,
            step=1,
            value=slider_value,
            tooltip=slider_tooltip,
            marks=None,
            id='year_slider0'
        )
    ]),
    # cpi graph title
    html.Div([
        html.Pre(children=graph_namer(series_name(1)),
                 style=text_style)
    ]),
    # cpi graph
    html.Div([
        dcc.Graph(id='cpi_graph')
    ]),
    # slider range for cpi graph
    html.Div([
        dcc.RangeSlider(
            min=slider_min,
            max=slider_max,
            step=1,
            value=slider_value,
            tooltip=slider_tooltip,
            marks=None,
            id='year_slider1'
        )
    ])
])


# update given graph_id based on rangeslider
def graph_updater(the_app, graph_id, slider_id, input_df, y_title):
    @the_app.callback(
        Output(graph_id, 'figure'),
        [Input(slider_id, 'value')]
    )
    def update_graph(years_chosen):
        dff = input_df[(pd.DatetimeIndex(input_df['date']).year >= years_chosen[0])
                       & (pd.DatetimeIndex(input_df['date']).year <= years_chosen[1])]

        cpi_fig = px.line(data_frame=dff,
                          x='date',
                          y='value').update_layout(xaxis_title='Date',
                                                   yaxis_title=y_title,
                                                   transition_duration=500)

        cpi_fig.update_traces(textposition='top center')

        return cpi_fig


graph_updater(app, 'unemployment_graph', 'year_slider0', df0, 'Unemployment Rate')
graph_updater(app, 'cpi_graph', 'year_slider1', df1, 'CPI for All Urban Consumers (CPI-U)')

if __name__ == '__main__':
    app.run_server(debug=True)
