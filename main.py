import datetime
import json

import math
import pandas as pd
import plotly.express as px
import requests
from dash import Dash, dcc, html, Input, Output

import creds

# dictionary with series id as the key and a list containing the minimum year of the series, the graph title of the
# series, and the axis title of the series as the value
DESIRED_SERIES = {'LNS14000000': [1948,
                                  'Unemployment Rate (Seasonally Adjusted)',
                                  'Unemployment Rate'],
                  'CUUR0000AA0': [1913,
                                  'CPI for All Urban Consumers (CPI-U) 1967=100 (Unadjusted)',
                                  'CPI for All Urban Consumers (CPI-U)'],
                  'EIUIR': [1983,
                            'Imports for All Commodities',
                            'Imports (All Commodities)'],
                  'EIUIQ': [1983,
                            'Exports for All Commodities',
                            'Exports (All Commodities)']
                  }


# Request that will retrieve data from the BLS Public Data API
def api_request(series_id, start_year, end_year):
    # hide my API key in an untracked credentials file
    data = json.dumps(
        {'registrationkey': creds.api_key,
         'seriesid': [series_id],
         'startyear': str(start_year), 'endyear': str(end_year),
         'calculations': 'false'})

    headers = {'Content-type': 'application/json'}

    try:
        post = requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/', data=data, headers=headers)
        post.raise_for_status()
    except requests.exceptions.HTTPError as error:
        raise SystemExit(error)

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
    for x in range(num_periods + 1):
        if max_year - 19 * x < min_year:
            result.append(min_year)
        else:
            result.append(max_year - 19 * x)

    result.reverse()
    return result


# Combine the requests into 1 dataframe
def make_df(current_index):
    cur_year = datetime.date.today().year
    period_dfs = []
    years = list_years(list(DESIRED_SERIES.values())[current_index][0], cur_year)
    for idx, elem in enumerate(years):
        if idx < len(years) - 1:
            period_dfs.append(api_request(list(DESIRED_SERIES)[current_index], years[idx], years[idx + 1]))
    return pd.concat(period_dfs, axis=0).drop_duplicates('date').sort_values(by='date')


def pop_df_list():
    result = []
    for idx, elem in enumerate(DESIRED_SERIES):
        result.append(make_df(idx))
    return result


def grapher(the_list):
    result = []
    text_style = {'text-align': 'center', 'font-size': '100%', 'color': 'black'}
    slider_tooltip = {'placement': 'bottom', 'always_visible': True}
    for idx, series in enumerate(the_list):
        the_min = pd.DatetimeIndex(the_list[idx]['date']).year.min()
        the_max = pd.DatetimeIndex(the_list[idx]['date']).year.max()

        result.append(
            html.Div([html.Pre(children=list(DESIRED_SERIES.values())[idx][1] + ' Over Time', style=text_style)]))
        result.append(
            html.Div([dcc.Graph(id='graph_' + str(idx), config={'showAxisDragHandles': False})]))
        result.append(
            html.Div([dcc.RangeSlider(min=the_min,
                                      max=the_max,
                                      step=1,
                                      value=[the_min, the_max],
                                      tooltip=slider_tooltip,
                                      marks=None,
                                      id='year_slider_' + str(idx))]))

    return result


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


if __name__ == '__main__':
    df_list = pop_df_list()
    app = Dash(__name__)
    app.layout = html.Div(grapher(df_list))
    for index, element in enumerate(DESIRED_SERIES):
        graph_updater(app,
                      'graph_' + str(index),
                      'year_slider_' + str(index),
                      df_list[index],
                      list(DESIRED_SERIES.values())[index][2])
    app.run_server(debug=True)
