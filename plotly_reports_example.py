from plotly import __version__
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly.graph_objs as go
import plotly
import pandas as pd
import numpy as np
from generate_template import generate_template


def percentile(n):
    def percentile_(x):
        return np.percentile(x, n)
    percentile_.__name__ = 'percentile_%s' % n
    return percentile_

path=r"result_Gateway(5).csv"

df = pd.read_csv(path)
#Delete rows with AllThreads=0
df=df[df.allThreads>0]
#convert all response codes to str
df['responseCode']=df['responseCode'].astype(str)
df['timeStamp']=pd.to_datetime(df['timeStamp'], unit='ms')


#create separate df with transactions
useful_col_names=['timeStamp', 'label', 'elapsed', 'success', 'allThreads']
tr_df=df[useful_col_names]
transaction_pattern=r'^\d{2,3}a?b?_.+'
tr_df=df[df.label.str.contains(transaction_pattern)]
tr_df=tr_df[tr_df.elapsed>0]

#calc stats
stats_df=tr_df[tr_df['success']].groupby("label").elapsed.agg([np.size, np.mean, np.std, np.min, np.max, percentile(50), percentile(90), percentile(97), percentile(99)])
#print (stats_df.to_html())
#stats_df.to_html('stats.html')


#response time graph
grouped = tr_df.sort_values(by=['timeStamp']).groupby(["label", "success"])
traces = []
for group_name, grouped_df in grouped:
    trace_tr = go.Scatter(
        x=grouped_df.timeStamp,
        y=grouped_df.elapsed,
        mode='lines',
        name="{0}{1}".format(group_name[0], "" if group_name[1] else ", FAILED")
    )
    traces.append(trace_tr)

layout = go.Layout(
    title='Transaction time',
)

resp_fig = go.Figure(data=traces, layout=layout)
resp_fig_json=resp_fig.to_json()

#erros vs users
grouped = tr_df[tr_df["success"] == False].sort_values(by=['timeStamp']).groupby(["label", "success"])
traces = []
for group_name, grouped_df in grouped:
    trace_tr = go.Scatter(
        x=grouped_df.allThreads,
        y=grouped_df.elapsed,
        mode='markers',
        name="{0}{1}".format(group_name[0], "" if group_name[1] else ", FAILED")
    )
    traces.append(trace_tr)

layout = go.Layout(
    title='Errors vs Number of users',
)

err_us_fig = go.Figure(data=traces, layout=layout)
err_us_fig_json = err_us_fig.to_json()

# a simple HTML template
template = """<html>
<head>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <p>Statistics<p>
    {}
    <p>divPlotly1</p>
    <div id='divPlotly1'></div>
    <script>
        var plotly_data1 = {}
        Plotly.react('divPlotly1', plotly_data1.data, plotly_data1.layout);
    </script>
    <p>divPlotly2</p>
    <div id='divPlotly2'></div>
    <script>
        var plotly_data2 = {}
        Plotly.react('divPlotly2', plotly_data2.data, plotly_data2.layout);
    </script>
</body>

</html>"""

template=generate_template(2,True)

# write the JSON to the HTML template
with open('new_plot.html', 'w') as f:
    f.write(template.format(stats_df.to_html(),resp_fig_json, err_us_fig_json))