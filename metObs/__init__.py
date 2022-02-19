# Authors: Rasmus Jensen og Søren Jessen, Københavns Universitet, Institut for Geovidenskab og Naturforvaltning (IGN), Øster Voldgade 10, 1350 København K

# The example below does this:
#    1) Downloads barometric pressure data from 29-30 November 2021, station 06184
#    2) Resamples (downsamples) the 'present 10 min' data to hourly data (the latter offset by 25 minutes)
#    3) Saves resulting data series to CSV-files
#    4) Creates plot for visual inspection

# %% STEP 1: REQUEST DATA FROM DMI's API
# The json object has a nested structure (e.g., dictionaries being contained in dictionaries)...
from pandas.io.json import json_normalize
import matplotlib.dates as mdates
import seaborn as sns
import matplotlib.pyplot as plt
import requests
import pandas as pd
import datetime as dt
import rfc3339
import pytz

# Insert you own api-key from DMI between the ''. To obtain your api-key, visit url: https://confluence.govcloud.dk/display/FDAPI/Danish+Meteorological+Institute+-+Open+Data Then choose to get an API-key for the metObsAPI 2.0.
api_key = '80bba6c4-8dfe-4d01-8019-3a724a69ddac'

url = 'https://dmigw.govcloud.dk/v2/metObs/collections/observation/items'  # DMI API v2 url

# Current timezone
tz = pytz.timezone('Europe/Copenhagen')

# Insert local start time and UTC time shift:
# yyyy-mm-ddThh:mm:ss+hh:mm UTC time shift] (2 h = DK summer time, 1 h = DK winter or normal time)
from_datetime = dt.datetime.now(tz) - dt.timedelta(days=2)
from_datetime_string = rfc3339.rfc3339(from_datetime)

# Insert local end time and UTC time shift:
# yyyy-mm-ddThh:mm:ss+hh:mm UTC time shift] (2 h = DK summer time, 1 h = DK winter or normal time)
# temp = dt.fromisoformat('2022-02-19T10:00:00+02:00')
to_datetime = dt.datetime.now(tz)
to_datetime_string = rfc3339.rfc3339(to_datetime)



# DMI's API retuns data in UTC time - not nice when you want to compare with your Danish local time. We'll need to correct for this later on. Here we just enter the season dependent time shift:
# unit = hours. Enter local time shift relative to UTC time: I.e., enter '2' h = DK summer time, or enter '1' h = DK winter or normal time

UTC_to_local_time_shift = 2

fromtotime = from_datetime_string + '/' + to_datetime_string  # concatenates from and to times

# Specify parameter:
# see parameterId-list at url: https://confluence.govcloud.dk/pages/viewpage.action?pageId=26476616
parm = 'temp_dry'

# Specify station no.:
# see stationId-list at url: https://confluence.govcloud.dk/pages/viewpage.action?pageId=41717704#Stations(metObs)-StationsavailableforthemetObsservice
stat = '06074'

# Specifies query:
params = {'api-key': api_key,
          'datetime': fromtotime,
          'stationId': stat,
          'parameterId': parm,
          # check later, that the DataFrame "data" contains less records than set limit!
          'limit': '300000',
          }

# when run, this returns a "response object" of the reqest module
r = requests.get(url, params=params)

# extracts JSON data from "response object". JSON is a human-readable format for data exchange.
json = r.json()

# converts the JSON object to a Pandas DataFrame. Using json_normalize() we select from the json object only the dictionary named 'features' and use these as columns headers in the final DataFrame
df = json_normalize(json['features'])


# %% STEP 2: USE DEFINED REQUEST, and save it to a DataFrame called 'data'

data = df

# converts values in 'properties.observed' to real datetime64ns objects in a column called 'time'
data['time'] = pd.to_datetime(data['properties.observed'])

# Set column 'time' to become index, enables resampling and eases plotting later on. Also corrects for UTM to local time time shift.
data.index = data['time'] + pd.Timedelta(hours=UTC_to_local_time_shift)

# Preparation for deletion of the parameterId-value in following command
data = data.rename(columns={'properties.value': parm})

data = data.drop(['id', 'type', 'geometry.coordinates', 'geometry.type', 'properties.created', 'properties.observed',
                 'properties.parameterId', 'properties.stationId', 'time'], axis=1)  # Delete unused columns

data = data.sort_index()  # DMI's API will show the latest data at the top - for many applications we need to the oldest data at the top and youngest in the bottom

# If required, add time offset to DatetimeIndex; offset will depend on parameter, consult: https://confluence.govcloud.dk/pages/viewpage.action?pageId=26476616
#data.index = data.index + pd.offsets.Minute(0)

data.plot(style='bo')  # Create a quick plot to get visual insight

data.info()  # Inspect sucsessful creation of 'data' with DatetimeIndex.


# %% STEP 2B: SAVE RAW DATA TO CSV
# The name will contain parameter name of resampled parameter, station number, and the time interval.
file_name = parm + '_stat' + stat + '_' + \
    str(pd.to_datetime(from_datetime_string).date()) + '-to-' + \
    str(pd.to_datetime(to_datetime_string).date()) + '.csv'
data.to_csv(file_name)


# %% STEP 3: RESAMPLE the file to obtain a more appropriate time interval
# Resampling option: D for daily, H for hourly, T for per minute, S for per second. See full list of options at url: https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#dateoffset-objects

# Custom name describing the parameter (and its new unit!) after resampling
parm_resampled = 'temp_dry_downsample'

# Downsampling:
data_resampled = data.resample('H').mean()

# Upsampling:
#data_resampled = data.resample(rule='T').interpolate(method='linear')

# Make the column header match the new/resampled parameter values
data_resampled = data_resampled.rename(columns={parm: parm_resampled})

# If required, add time offset to DatetimeIndex. E.g., some parameters are 'present', others an average over 'last 10 min', etc. Offset will depend on parameter. Consult metadata: https://confluence.govcloud.dk/pages/viewpage.action?pageId=26476616
data_resampled.index = data_resampled.index + pd.offsets.Minute(25)

# Create a quick plot to investigate effectiveness, compare with previous plot
data_resampled.plot(style='ro')

# Inspect sucsessful creation of 'data' with DatetimeIndex.
data_resampled.info()


# %% STEP 3B: SAVE RESAMPLED DATA TO CSV
# The name will contain parameter name of resampled parameter, station number, and the time interval.
file_name = parm_resampled + '_stat' + stat + '_' + \
    str(pd.to_datetime(from_datetime_string).date()) + '-to-' + \
    str(pd.to_datetime(to_datetime_string).date()) + '.csv'
data_resampled.to_csv(file_name)


# %% STEP 4: CREATE POINT PLOT FOR VISUAL COMPARISON OF ORIGINAL AND RESAMPLED DATA

fig, ax = plt.subplots(nrows=1, ncols=1)

sns.scatterplot(x=data.index, y=parm, data=data, s=10, c=[
                'blue'], edgecolor='None', ax=ax, label='Original data')
sns.scatterplot(x=data_resampled.index, y=parm_resampled, data=data_resampled, s=10, c=[
                'red'], edgecolor='None', ax=ax, label='Resampled data')

# Format tick labels: %to digit day-of-month, %b: first letter of month, %y: year without century, \' apostrof with escape character (\), %H: two-digit hour, %T: two-digit minute
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

ax.legend()

plt.ylabel(parm_resampled, labelpad=(10))
plt.xlabel('', labelpad=10)
