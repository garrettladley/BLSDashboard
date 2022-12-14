from datetime import datetime

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

import main


# tests whether the appropriate dataframe is returned based on sample JSON post_text for Jan. 2022 to Sept. 2022
def test_process_json_data():
    df_expected = pd.DataFrame([['LNS14000000', datetime(2022, 9, 1), 3.500],
                                ['LNS14000000', datetime(2022, 8, 1), 3.700],
                                ['LNS14000000', datetime(2022, 7, 1), 3.500],
                                ['LNS14000000', datetime(2022, 6, 1), 3.600],
                                ['LNS14000000', datetime(2022, 5, 1), 3.600],
                                ['LNS14000000', datetime(2022, 4, 1), 3.600],
                                ['LNS14000000', datetime(2022, 3, 1), 3.600],
                                ['LNS14000000', datetime(2022, 2, 1), 3.800],
                                ['LNS14000000', datetime(2022, 1, 1), 4.000],
                                ['CUUR0000AA0', datetime(2022, 9, 1), 889.104],
                                ['CUUR0000AA0', datetime(2022, 8, 1), 887.197],
                                ['CUUR0000AA0', datetime(2022, 7, 1), 887.511],
                                ['CUUR0000AA0', datetime(2022, 6, 1), 887.615],
                                ['CUUR0000AA0', datetime(2022, 5, 1), 875.589],
                                ['CUUR0000AA0', datetime(2022, 4, 1), 866.042],
                                ['CUUR0000AA0', datetime(2022, 3, 1), 861.235],
                                ['CUUR0000AA0', datetime(2022, 2, 1), 849.887],
                                ['CUUR0000AA0', datetime(2022, 1, 1), 842.196]
                                ],
                               columns=['seriesID', 'date', 'value'])
    df_actual = main.process_json_data({'status': 'REQUEST_SUCCEEDED',
                                        'responseTime': 199,
                                        'message': [],
                                        'Results':
                                            {'series': [
                                                {'seriesID': 'LNS14000000', 'data': [
                                                    {'year': '2022', 'period': 'M09', 'periodName': 'September',
                                                     'latest': 'true', 'value': '3.5', 'footnotes': [{}]},
                                                    {'year': '2022', 'period': 'M08', 'periodName': 'August',
                                                     'value': '3.7', 'footnotes': [{}]},
                                                    {'year': '2022', 'period': 'M07', 'periodName': 'July',
                                                     'value': '3.5',
                                                     'footnotes': [{}]},
                                                    {'year': '2022', 'period': 'M06', 'periodName': 'June',
                                                     'value': '3.6',
                                                     'footnotes': [{}]},
                                                    {'year': '2022', 'period': 'M05', 'periodName': 'May',
                                                     'value': '3.6',
                                                     'footnotes': [{}]},
                                                    {'year': '2022', 'period': 'M04', 'periodName': 'April',
                                                     'value': '3.6',
                                                     'footnotes': [{}]},
                                                    {'year': '2022', 'period': 'M03', 'periodName': 'March',
                                                     'value': '3.6',
                                                     'footnotes': [{}]},
                                                    {'year': '2022', 'period': 'M02', 'periodName': 'February',
                                                     'value': '3.8', 'footnotes': [{}]},
                                                    {'year': '2022', 'period': 'M01', 'periodName': 'January',
                                                     'value': '4.0', 'footnotes': [{}]}]},
                                                {'seriesID': 'CUUR0000AA0',
                                                 'data': [{'year': '2022',
                                                           'period': 'M09',
                                                           'periodName': 'September',
                                                           'latest': 'true',
                                                           'value': '889.104',
                                                           'footnotes': [{}]},
                                                          {'year': '2022',
                                                           'period': 'M08',
                                                           'periodName': 'August',
                                                           'value': '887.197',
                                                           'footnotes': [{}]},
                                                          {'year': '2022',
                                                           'period': 'M07',
                                                           'periodName': 'July',
                                                           'value': '887.511',
                                                           'footnotes': [{}]},
                                                          {'year': '2022',
                                                           'period': 'M06',
                                                           'periodName': 'June',
                                                           'value': '887.615',
                                                           'footnotes': [{}]},
                                                          {'year': '2022',
                                                           'period': 'M05',
                                                           'periodName': 'May',
                                                           'value': '875.589',
                                                           'footnotes': [{}]},
                                                          {'year': '2022',
                                                           'period': 'M04',
                                                           'periodName': 'April',
                                                           'value': '866.042',
                                                           'footnotes': [{}]},
                                                          {'year': '2022',
                                                           'period': 'M03',
                                                           'periodName': 'March',
                                                           'value': '861.235',
                                                           'footnotes': [{}]},
                                                          {'year': '2022',
                                                           'period': 'M02',
                                                           'periodName': 'February',
                                                           'value': '849.887',
                                                           'footnotes': [{}]},
                                                          {'year': '2022',
                                                           'period': 'M01',
                                                           'periodName': 'January',
                                                           'value': '842.196',
                                                           'footnotes': [{}]}]}]}})
    assert_frame_equal(df_expected, df_actual)


# generates list from 1913 (minimum year in BLS data) to 2022
def test_2022_default():
    assert main.list_years(1913, 2022) == [1913, 1927, 1946, 1965, 1984, 2003, 2022]


# generates list for case of 20 year difference
def test_20_year_diff():
    assert main.list_years(2002, 2022) == [2002, 2003, 2022]


# generates list for case of 19 year difference
def test_19_year_diff():
    assert main.list_years(2003, 2022) == [2003, 2022]


# generates list for case of 1 year difference
def test_0_year_diff():
    assert main.list_years(2022, 2022) == [2022]


# tests that a ValueError is raised when min_year > max_year
def test_min_greater_than_max():
    with pytest.raises(ValueError) as e:
        main.list_years(2023, 2022)
        assert str(e) == 'min_year must be less than or equal to max_year'
