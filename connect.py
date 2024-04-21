import base64
import io
from dash import Dash, html, dcc, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import State
from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform
from sqlalchemy import Table, create_engine, MetaData
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import warnings
import os
from flask_login import login_user, logout_user, current_user, LoginManager, UserMixin
from flask import redirect
import configparser
import plotly.express as px
import pandas as pd

warnings.filterwarnings("ignore")

####################################
# DATABASE Setup
# ####################################

#ANUSHAS DB
username = 'roshnik'
password = 'Password123#'
database = 'retail-analysis'
hostname = 'retail-analysis-cloud.mysql.database.azure.com'
root_ca = '/Users/khatr/OneDrive/Documents/Cloud-Computing-Final-Project/DigiCertGlobalRootCA.crt.pem'


# ATHULYA'S DB FOR TESTING
#username = 'athulya'
#password = 'Password123'
#database = 'cloud-proj'
#hostname = 'cloud-server-1.mysql.database.azure.com'
#root_ca = '/Users/athulyaganesh/Desktop/Code/Cloud-Computing-Final-Project/DigiCertGlobalRootCA1.crt.pem'

db_uri = f"mysql+pymysql://{username}:{password}@{hostname}/{database}"

engine = create_engine(
   db_uri,
   connect_args = {
    "ssl": {
            "ssl_ca": root_ca
        }
   }
)

metadata = MetaData()
user_table = Table('users', metadata, autoload=True, autoload_with=engine)

# with engine.connect() as connection:
#     select_statement = user_table.select()
#     result_set = connection.execute(select_statement)
#     for row in result_set:
#         print(row)

db = SQLAlchemy()
config = configparser.ConfigParser()

class Users(db.Model):
    users_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(15), unique=True, nullable = False)
    password = db.Column(db.String(1000))
    email = db.Column(db.String(50), unique=True)
    
    def get_id(self):
        return self.users_id

Users_tbl = Table('users', Users.metadata)

####################################
# Application Setup
####################################

external_stylesheets = [
    dbc.themes.FLATLY,
    'https://codepen.io/chriddyp/pen/bWLwgP.css'
]

# app = dash.Dash(__name__)
app = DashProxy(__name__, external_stylesheets=external_stylesheets, transforms=[MultiplexerTransform()])
app.title = 'Cloud Computing Final Project'
app.layout = html.Div("Please work!")

server = app.server
app.config.suppress_callback_exceptions = True
# config
server.config.update(
    SECRET_KEY=os.urandom(12),
    SQLALCHEMY_DATABASE_URI=db_uri,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    MYSQL_SSL_CA = root_ca
)
db.init_app(server)

# Setup the LoginManager for the server
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = '/'

#User as base
# Create User class with UserMixin
class Users(UserMixin, Users):

    def get_id(self):
        return self.users_id

######################
# Graphs
######################

graphs = {}  # container to hold all graphs
households_df = None
transactions_df = None
products_df = None
transactions_combined_household_df = None
all_three_combined_df = None

def get_figures():
    global graphs
    global households_df
    global transactions_df
    global products_df
    global transactions_combined_household_df
    global all_three_combined_df

    if all_three_combined_df is None:
        # debug_engine = create_engine('sqlite:///db.sql', echo=False)
        conn = engine

        # read data from database
        households_df = pd.read_sql('SELECT * FROM household', conn)
        transactions_df = pd.read_sql('SELECT * FROM transaction', conn)
        transactions_df['purchase_month'] = pd.DatetimeIndex(transactions_df['purchase_']).month
        products_df = pd.read_sql('SELECT * FROM product', conn)

        # combine data frames
        transactions_combined_household_df = transactions_df.merge(households_df, on='hshd_num', how='left')
        all_three_combined_df = transactions_combined_household_df.merge(products_df, on='product_num', how='left')

   
    all_three_combined_df['year']=all_three_combined_df['year'].astype(int)
    all_three_combined_df['units']=all_three_combined_df['units'].astype(int)
    all_three_combined_df['spend']=all_three_combined_df['spend'].astype(float)
    all_three_combined_df['purchase_month']=all_three_combined_df['purchase_month'].astype(int)
    all_three_combined_df['week_num']=all_three_combined_df['week_num'].astype(int)

    # units by year
    units_year_df = pd.DataFrame({
        'YEAR': ['2018', '2019', '2020','2021'],
        'UNITS': [all_three_combined_df.loc[all_three_combined_df['year'] == 2018, 'units'].sum(),
                  all_three_combined_df.loc[all_three_combined_df['year'] == 2019, 'units'].sum(),
                  all_three_combined_df.loc[all_three_combined_df['year'] == 2020, 'units'].sum(),
                  all_three_combined_df.loc[all_three_combined_df['year'] == 2021, 'units'].sum()]
    })

    graphs['fig_units_by_year'] = px.bar(units_year_df, x="YEAR", y="UNITS", title='Units by Year')

    # units by month
    units_month_df = pd.DataFrame({
        'PURCHASE_MONTH': [month for month in range(1, 13)],
        'UNITS': [
            all_three_combined_df.loc[all_three_combined_df['purchase_month'] == month, 'units'].sum() for month in
            range(1, 13)
        ]
    })
    graphs['fig_units_by_month'] = px.line(units_month_df, x="PURCHASE_MONTH", y="UNITS", title="Units by Month",
                                         markers=True)

    # units by week
    units_week_df = pd.DataFrame({
        'WEEK_NUM': [week for week in range(1, 53)],
        'UNITS': [
            all_three_combined_df.loc[all_three_combined_df['week_num'] == week, 'units'].sum() for week in range(1, 53)
        ]
    })
    graphs['fig_units_by_week'] = px.line(units_week_df, x="WEEK_NUM", y="UNITS", title="Units by Week", markers=True)

    # units by store region
    units_region_df = pd.DataFrame({
        'STORE_REGION': list(all_three_combined_df['store_r'].unique()),
        'UNITS': [
            all_three_combined_df.loc[all_three_combined_df['store_r'] == store_region, 'units'].sum() for store_region
            in list(all_three_combined_df['store_r'].unique())
        ]
    })
    graphs['fig_units_by_region'] = px.pie(units_region_df, values='UNITS', names='STORE_REGION',
                                         title='Units by Store Region')

    # spend by year
    spend_year_df = pd.DataFrame({
        'YEAR': ['2018', '2019', '2020', '2021'],
        'SPEND': [all_three_combined_df.loc[all_three_combined_df['year'] == 2018, 'spend'].sum(),
                  all_three_combined_df.loc[all_three_combined_df['year'] == 2019, 'spend'].sum(),
                  all_three_combined_df.loc[all_three_combined_df['year'] == 2020, 'spend'].sum(),
                  all_three_combined_df.loc[all_three_combined_df['year'] == 2021, 'spend'].sum()]
    })
    graphs['fig_spend_by_year'] = px.bar(spend_year_df, x="YEAR", y="SPEND", title='Spend by Year')

    # spend by month
    spend_month_df = pd.DataFrame({
        'PURCHASE_MONTH': [month for month in range(1, 13)],
        'SPEND': [
            all_three_combined_df.loc[all_three_combined_df['purchase_month'] == month, 'spend'].sum() for month in
            range(1, 13)
        ]
    })
    graphs['fig_spend_by_month'] = px.line(spend_month_df, x="PURCHASE_MONTH", y="SPEND", title="Spend by Month",
                                         markers=True)

    # spend by week
    spend_week_df = pd.DataFrame({
        'WEEK_NUM': [week for week in range(1, 53)],
        'SPEND': [
            all_three_combined_df.loc[all_three_combined_df['week_num'] == week, 'spend'].sum() for week in range(1, 53)
        ]
    })
    graphs['fig_spend_by_week'] = px.line(spend_week_df, x="WEEK_NUM", y="SPEND", title="Spend by Week", markers=True)

    # spend by region
    spend_region_df = pd.DataFrame({
        'STORE_REGION': list(all_three_combined_df['store_r'].unique()),
        'SPEND': [
            all_three_combined_df.loc[all_three_combined_df['store_r'] == store_region, 'spend'].sum() for store_region
            in list(all_three_combined_df['store_r'].unique())
        ]
    })
    graphs['fig_spend_by_region'] = px.pie(spend_region_df, values='SPEND', names='STORE_REGION',
                                         title='Spend by Store Region')

    # spend by martial status
    spend_marital_df = pd.DataFrame({
        'MARITAL': list(all_three_combined_df['marital'].unique()),
        'SPEND': [
            all_three_combined_df.loc[all_three_combined_df['marital'] == marital_status, 'spend'].sum() for
            marital_status in list(all_three_combined_df['marital'].unique())
        ]
    })
    graphs['fig_spend_by_marital'] = px.pie(spend_marital_df, values='SPEND', names='MARITAL',
                                          title='Spend by Martial Status')

    # spend by number of children
    spend_children_df = pd.DataFrame({
        'CHILDREN': [children for children in list(all_three_combined_df['children'].unique())],
        'SPEND': [
            all_three_combined_df.loc[all_three_combined_df['children'] == children, 'spend'].sum() for children in
            list(all_three_combined_df['children'].unique())
        ]
    })
    graphs['fig_spend_by_children'] = px.pie(spend_children_df, values='SPEND', names='CHILDREN',
                                           title='Spend by Number of Children')

    # spend by household composition
    spend_hshdcomposition_df = pd.DataFrame({
        'HSHD_COMPOSITION': [hshd_composition for hshd_composition in
                             list(all_three_combined_df['hshd_composition'].unique())],
        'SPEND': [
            all_three_combined_df.loc[all_three_combined_df['hshd_composition'] == hshd_composition, 'spend'].sum() for
            hshd_composition in list(all_three_combined_df['hshd_composition'].unique())
        ]
    })
    graphs['fig_spend_by_hshdcomposition'] = px.pie(spend_hshdcomposition_df, values='SPEND', names='HSHD_COMPOSITION',
                                                 title='Spend by Household Composition')

    # units by region over year
    units_by_region_over_year_df = all_three_combined_df.groupby(['store_r', 'year']).sum()
    units_by_region_over_year_df.reset_index(inplace=True)
    graphs['fig_units_by_region_over_year'] = px.sunburst(units_by_region_over_year_df, path=['year', 'store_r'],
                                                        values='units', title="Units by Region by Year")

    # spend by region over year
    graphs['fig_spend_by_region_over_year'] = px.sunburst(units_by_region_over_year_df, path=['year', 'store_r'],
                                                        values='spend', title="Spend By Region by Year")

    # unit / spend department
    units_by_dept_over_year_df = all_three_combined_df.groupby(['department', 'year']).sum()
    units_by_dept_over_year_df.reset_index(inplace=True)
    units_by_dept_over_year_df['year'] = units_by_dept_over_year_df['year'].astype(str)
    graphs['fig_units_by_dept_over_year_df'] = px.sunburst(units_by_dept_over_year_df, path=['year', 'department'],
                                                         values='units', title="Units By Department")
    graphs['fig_spend_by_dept_over_year_df'] = px.sunburst(units_by_dept_over_year_df, path=['year', 'department'],
                                                         values='spend', title="Spend By Department")

    # units / spend by incomerange over a year
    units_by_incomerange_over_year_df = all_three_combined_df.groupby(['income_range', 'year']).sum()
    units_by_incomerange_over_year_df.reset_index(inplace=True)
    units_by_incomerange_over_year_df['year'] = units_by_incomerange_over_year_df['year'].astype(str)

    # units by agerange over a year
    units_by_agerange_over_year_df = all_three_combined_df.groupby(['age_range', 'year']).sum()
    units_by_agerange_over_year_df.reset_index(inplace=True)
    units_by_agerange_over_year_df['year'] = units_by_agerange_over_year_df['year'].astype(str)

    graphs['fig_units_by_agerange_over_year'] = px.bar(units_by_agerange_over_year_df,
                                                     x="age_range", y="units", color="year", barmode="group",
                                                     title="Units by Age Range")

    # spend by agerange over a year
    graphs['fig_spend_by_agerange_over_year'] = px.bar(units_by_agerange_over_year_df,
                                                     x="age_range", y="spend", color="year", barmode="group",
                                                     title="Spend By Age Range")

    # spend by agerange over a year
    graphs['fig_units_by_incomerange_over_year_df'] = px.bar(units_by_incomerange_over_year_df,
                                                           x="income_range", y="units", color="year", barmode="group",
                                                           title="Units by Income Level")

    graphs['fig_spend_by_incomerange_over_year_df'] = px.bar(units_by_incomerange_over_year_df,
                                                           x="income_range", y="spend", color="year", barmode="group",
                                                           title="Spend by Income Level")


######################
# Dashboard Layout
######################

def display_dashboard():
    get_figures()
    dashboard_layout = html.Div(children=[
        html.Hr(),
        html.H1(children=['Cloud Computing Final Project']),
        html.H3('Athulya Ganesh & Anusha Chitranshi'),
        html.Br(),
        html.H4("Retail Dashboard"),
        html.Hr(),

        dbc.Row([

            dbc.Col(html.Div([dcc.Graph(figure=graphs['fig_units_by_year'])]), width=3),
            dbc.Col(html.Div([dcc.Graph(figure=graphs['fig_spend_by_year'])]), width=3),
            dbc.Col(html.Div([dcc.Graph(figure=graphs['fig_units_by_region_over_year'])]), width=3),
            dbc.Col(html.Div([dcc.Graph(figure=graphs['fig_spend_by_region_over_year'])]), width=3)

        ]),
        html.Br(),
        dbc.Row([
            dbc.Col(html.Div([dcc.Graph(figure=graphs['fig_units_by_month'])]), width=6),
            dbc.Col(html.Div([dcc.Graph(figure=graphs['fig_units_by_week'])]), width=6),
        ]),
        html.Br(),
        dbc.Row([
            dbc.Col(html.Div([dcc.Graph(figure=graphs['fig_spend_by_month'])]), width=6),
            dbc.Col(html.Div([dcc.Graph(figure=graphs['fig_spend_by_week'])]), width=6),
        ]),
        html.Br(),
        dbc.Row([
            dbc.Col(html.Div([dcc.Graph(figure=graphs['fig_spend_by_marital'])]), width=4),
            dbc.Col(html.Div([dcc.Graph(figure=graphs['fig_spend_by_children'])]), width=4),
            dbc.Col(html.Div([dcc.Graph(figure=graphs['fig_spend_by_hshdcomposition'])]), width=4)
        ]),
        html.Br(),
        dbc.Row([
            dbc.Col(html.Div([dcc.Graph(figure=graphs['fig_units_by_dept_over_year_df'])]), width=6),
            dbc.Col(html.Div([dcc.Graph(figure=graphs['fig_spend_by_dept_over_year_df'])]), width=6)
        ]),
        html.Br(),
        dbc.Row([
            dbc.Col(html.Div([dcc.Graph(figure=graphs['fig_units_by_agerange_over_year'])]), width=6),
            dbc.Col(html.Div([dcc.Graph(figure=graphs['fig_spend_by_agerange_over_year'])]), width=6),
        ]),
        html.Br(),
        dbc.Row([
            dbc.Col(html.Div([dcc.Graph(figure=graphs['fig_units_by_incomerange_over_year_df'])]), width=6),
            dbc.Col(html.Div([dcc.Graph(figure=graphs['fig_spend_by_incomerange_over_year_df'])]), width=6),
        ]),
        html.Br(),
        html.P(['The below table combines retail data for transactions, households, and products. Each column is searchable and sortable using the second row as search input.\nHere are your search options:\neq: equals\nlt: less than\ngt: greater than\ncontains (for strings)\nEnter your command followed by a space and a number or a string. For example, if you want to filter values where hshd_num=10, write eq 10 in that column.\n\nWhere can I use these commands? Hshd_num, Basket_num, Date, Product_num, Department, Commodity']), 
        dash_table.DataTable(
            id='table-sorting-filtering',
            columns=[
                {'name': i, 'id': i, 'deletable': True} for i in sorted(all_three_combined_df.columns)
            ],
            page_current=0,
            page_size=15,
            page_action='custom',

            filter_action='custom',
            filter_query='',

            sort_action='custom',
            sort_mode='multi',
            sort_by=[],

            style_table={
                'overflow': 'auto'
            }
        ),

        html.P(
            "Use the input below to update tables. Each uploaded file must be a CSV. If the filename contains 'household', 'transaction' or 'product', the corresponding table will be updated"),
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select Files')
            ]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'backgroundColor': 'white',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px'
            },
            # Allow multiple files to be uploaded
            multiple=False
        ),
        html.Div(id='output-data-upload'),

        html.Br(),html.Br(),
        dcc.Link(html.Button("See Questions and Answers Here", style={'backgroundColor': 'white'}), href="/questions", refresh=True),
        html.Br(),html.Br(),
        dcc.Link(html.Button("Logout", style={'backgroundColor': 'white'}), href="/logout", refresh=True), html.Hr(), html.Hr()], style={'margin' : 'auto', 'width' : '100%', 'text-align' : 'center','backgroundColor':'#cad6f0' })

    return dashboard_layout

# operators for dash table filtering
operators = [['ge ', '>='],
             ['le ', '<='],
             ['lt ', '<'],
             ['gt ', '>'],
             ['ne ', '!='],
             ['eq ', '='],
             ['contains '],
             ['datestartswith ']]


def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                value_part = value_part.strip()
                v0 = value_part[0]
                if (v0 == value_part[-1] and v0 in ("'", '"', '`')):
                    value = value_part[1: -1].replace('\\' + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value

    return [None] * 3


# call back to update dash table
@app.callback(
    Output('table-sorting-filtering', 'data'),
    Input('table-sorting-filtering', "page_current"),
    Input('table-sorting-filtering', "page_size"),
    Input('table-sorting-filtering', 'sort_by'),
    Input('table-sorting-filtering', 'filter_query'))

def update_table(page_current, page_size, sort_by, filter):
    filtering_expressions = filter.split(' && ')
    dff = all_three_combined_df
    dff['hshd_num']=dff['hshd_num'].astype(int)
    dff['basket_num']=dff['basket_num'].astype(int)
    # dff['purchase_']=pd.to_datetime(dff['purchase_'], format='%d-%b-%y')
    dff['product_num']=dff['product_num'].astype(int)

    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)

        # # let's change the default operator for ints and floats
        # if dff[col_name].dtype in ['int64', 'float64'] and operator == 'contains':
        #     operator = 'eq'

        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            # these operators match pandas series operator method names
            dff = dff.loc[getattr(dff[col_name], operator)(filter_value)]
        elif operator == 'contains':
            if dff[col_name].dtype in ['int64', 'float64']:
                dff = dff.loc[getattr(dff[col_name], 'eq')(filter_value)]
            else:
                dff = dff.loc[dff[col_name].str.contains(filter_value, case=False)]
        elif operator == 'datestartswith':
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            dff = dff.loc[dff[col_name].str.startswith(filter_value, case=False)]

    if len(sort_by):
        dff = dff.sort_values(
            [col['column_id'] for col in sort_by],
            ascending=[
                col['direction'] == 'asc'
                for col in sort_by
            ],
            inplace=False
        )

    page = page_current
    size = page_size
    return dff.iloc[page * size: (page + 1) * size].to_dict('records')

####################################
# USER LOGIN AND PAGE ROUTING
####################################

# create user layout
create = html.Div([ 
        html.Br(),html.Br(),html.Br(),html.Br(),html.Br(),html.Br(),html.Br(),
        html.H1('Cloud Computing Final Project'),html.Br(),
        html.H2('''Please sign up to continue:''', id='h1'),
        html.Br(),
        dcc.Location(id='create_user', refresh=True),
        dcc.Input(id="username"
            , type="text"
            , placeholder="Enter username"
            , maxLength =15),
        html.Br(),
        html.Br(),
        dcc.Input(id="password"
            , type="password"
            , placeholder="Enter password"),
        html.Br(),
        html.Br(),
        dcc.Input(id="email"
            , type="email"
            , placeholder="Enter email"
            , maxLength = 50),
        html.Br(), html.Br(),
        html.Button('Create User', id='submit-val', n_clicks=0, style={'backgroundColor':'white'}),
        html.Br(),html.Br(),
        html.Div(id='container-button-basic'),
        dcc.Link(html.Button("Login", style={'backgroundColor':'white'}), href="/", refresh=True),
        html.Br(), html.Br() ,html.Br(),html.Br(),
    ], style={'margin' : 'auto', 'width' : '50%', 'text-align' : 'center','backgroundColor':'#DAF7A6' })#end div

# login layout
login =  html.Div([dcc.Location(id='url_login', refresh=True),
        html.Br(),html.Br(),html.Br(),html.Br(),html.Br(),html.Br(),html.Br()
            , html.H1("Cloud Computing Final Project"),
            html.Br()
            , html.H2('''Please log in to continue:''', id='h1'), html.Br()
            , dcc.Input(placeholder='Enter your username',
                    type='text',
                    id='uname-box'), html.Br(),  html.Br()
            , dcc.Input(placeholder='Enter your password',
                    type='password',
                    id='pwd-box'), html.Br(), html.Br()
            , html.Button(children='Login',
                    n_clicks=0,
                    type='submit',
                    id='login-button', style={'backgroundColor':'white'}),  html.Br(),  html.Br()
            , html.Div(children='', id='output-state'),
            dcc.Link(html.Button("Create an Account", style={'backgroundColor':'white'}), href="/create", refresh=True),
            html.Br(), html.Br(), html.Br(), html.Br()
        ] , style={'margin' : 'auto', 'width' : '50%', 'text-align' : 'center', 'backgroundColor':'#F7B3A6'}, ) #end div

success = display_dashboard()

data = html.Div([dcc.Dropdown(
    id='dropdown',
    options=[{'label': i, 'value': i} for i in ['Day 1', 'Day 2']],
    value='Day 1')
    , html.Br()
    , html.Div([dcc.Graph(id='graph')])
])  # end div

failed = html.Div([ dcc.Location(id='url_login_df', refresh=True)
            , html.Div([html.H2('Log in Failed. Please try again.')
                    ,dcc.Link(html.Button("Login", style={'backgroundColor':'white'}), href="/", refresh=True),
                ]) #end div
        ], style={'margin' : 'auto', 'width' : '50%', 'text-align' : 'center'}) #end div


logout = html.Div([dcc.Location(id='logout', refresh=True)
        , html.Br()
        , html.Div(html.H2('You have been logged out - Please login'))
        , html.Br()
        ,dcc.Link(html.Button("Login", style={'backgroundColor':'white'}), href="/", refresh=True),
    ], style={'margin' : 'auto', 'width' : '50%', 'text-align' : 'center'})#end div

questions = html.Div([
    html.Div([
    html.Hr(),
    html.H1('Retail Questions and Answers'),html.Br(),
    html.Marquee(html.H2("WHAT DO WE WANT???")),html.Br(),
    ], style={'margin':'auto', 'text-align' : 'center', 'backgroundColor':'white'}),

    html.P([
            html.Br(),
            html.B('Key Questions:'), html.Br(),
            "1. How does customer engagement change over time?", html.Br(),
            html.Li("Do households spend less or more?"),
            html.Li("What categories are growing or shrinking with changing customer engagement?"),
            "2. Which demographic factors (e.g. household size, presence of children, income) appear to affect customer engagement?",
            html.Br(),
            html.Li("How do they affect customer engagement with certain categories?"),
            html.Li("How might we re-engage customers within the store? Or within a specific category?"),
        ], style={'padding': '10px'}),

    html.Pre('''
            Customer Engagement can be affected by: (Department, Commodity, Spend, Units, Store_region, 
            Week_num, Loyalty_flag, Age_range, Income_range, Homeowner_desc, Household_size, Children)
            Customer Engagement can be shown by: (units bought, money spent)
            Department, -> Spend, Week_num, Year, Purchase_Month, Units
            Commodity, -> Spend, Week_num, Year, Purchase_Month, Units
            Brand Type -> Spend, Units, Age_range, Income_range
            Purchase_month -> Spend, Units, Age_range, Marital, Income_range, 
            Spend -> Year, Month, Week_num, Age_range, Marital, Income_range, Homeowner, HouseHold_size, Children
            Store_R -> Spend, Week_num, Year, Purchase_Month, Units
            '''
                 ),
    html.P([
        html.B(
            'Provide a short write-up on which Data Science Predictive modeling techniques would be most suitable to reasonably answer the questions below.  Please see The Top 10 Machine Learning Algorithms Links to an external site. for model section. (No more than 200 words) (3 points)'),
        html.Br(),
        html.A(href='https://colab.research.google.com/drive/1BIArCqR97f0y0cyqzPVhMQXyYVqDRtKx',
               children='Link to ML Model'),
        html.Pre(
            '''
               The given retail dataset has many columns, but the key factors for measuring customer engagement are spending
                and units sold. Therefore, a neural network was trained to predict spending and units sold based on other 
                features such as region, week number, year, purchase month, department, and others. The neural network consists
                 of an input layer, hidden layers, and an output layer, with the input layer taking in data from the retail
                 dataset and the hidden layers processing the data to extract features and patterns. The output layer makes
                  predictions based on the learned patterns. The network can be trained using various algorithms, such as 
                  the backpropagation algorithm or Adam optimizer, to adjust the weights and reduce the error rate of predictions.
                   Once trained, the network can provide insights into customer behavior and inform marketing strategies, pricing 
                   optimization, and product focus. The neural network can also identify trends in sales, predict customer spending 
                   patterns, and help optimize pricing. Overall, the insights provided by the neural network can aid organizations
                    in gaining a better understanding of customer behavior and the effectiveness of their marketing efforts.
            '''
        )], style={'padding': '10px'}),

    html.Div([
    html.Marquee(html.H2("MONEY!!!!!!")),html.Br(),
], style={'margin': 'auto', 'text-align': 'center', 'backgroundColor':'white'}),
    html.Hr(), html.Hr(),
    dcc.Link(html.Button("Back to Dashboard", style={'backgroundColor':'white'}), href="/success", refresh=True),
    html.Hr()
], style={'margin': 'auto', 'text-align': 'center', 'backgroundColor':'#eaf6ce'})

app.layout= html.Div([
            html.Div(id='page-content', className='content')
            ,  dcc.Location(id='url', refresh=False)
        ])


# callback to reload the user object
@login_manager.user_loader
def load_user(users_id):
    return Users.query.get(int(users_id))

@app.callback(
    Output('page-content', 'children')
    , [Input('url', 'pathname')])


def display_page(pathname):
    if pathname == '/':
        return login
    elif pathname == '/create':
        return create
    elif pathname == '/success':
        if current_user.is_authenticated:
            return success
        else:
            return failed
    #elif pathname =='/data':
       # if current_user.is_authenticated:
           # return data
    elif pathname == '/logout':
        if current_user.is_authenticated:
            logout_user()
            return logout
        else:
            return failed
    elif pathname == '/questions':
        return questions
    else:
        return 'Check your URL and try again.'
    
# set the callback for the dropdown interactivity
@app.callback(
    [Output('graph', 'figure')]
    , [Input('dropdown', 'value')])
def update_graph(dropdown_value):
    if dropdown_value == 'Day 1':
        return [{'layout': {'title': 'Graph of Day 1'}
                    , 'data': [{'x': [1, 2, 3, 4]
                                   , 'y': [4, 1, 2, 1]}]}]
    else:
        return [{'layout': {'title': 'Graph of Day 2'}
                    , 'data': [{'x': [1, 2, 3, 4]
                                   , 'y': [2, 3, 2, 4]}]}]

@app.callback(
    Output('url_login', 'pathname')
    , [Input('login-button', 'n_clicks')]
    , [State('uname-box', 'value'), State('pwd-box', 'value')])

def successful(n_clicks, input1, input2):
    user = Users.query.filter_by(username=input1).first()
    if user:
        if check_password_hash(user.password, input2):
            login_user(user)
            return '/success'
        else:
            pass
    else:
        pass


@app.callback(
    [Output('container-button-basic', "children")]
    , [Input('submit-val', 'n_clicks')]
    , [State('username', 'value'), State('password', 'value'), State('email', 'value')])
def insert_users(n_clicks, un, pw, em):
    if un is not None and pw is not None and em is not None:
        hashed_password = generate_password_hash(pw, method='sha256')
        ins = Users_tbl.insert().values(username=un, password=hashed_password, email=em)
        conn = engine.connect()
        conn.execute(ins)
        conn.close()
        return "You have been signed up. Please navigate to the login page now."
    else:
        return [html.Div([html.P('Already have a user account?')])]

@app.callback(
    Output('output-state', 'children')
    , [Input('login-button', 'n_clicks')]
    , [State('uname-box', 'value'), State('pwd-box', 'value')])
def update_output(n_clicks, input1, input2):
    if n_clicks > 0:
        user = Users.query.filter_by(username=input1).first()
        if user:
            if check_password_hash(user.password, input2):
                return ''
            else:
                return 'Incorrect username or password'
        else:
            return 'Incorrect username or password'
    else:
        return ''
    
@app.callback(
    Output('url_login_success', 'pathname')
    , [Input('back-button', 'n_clicks')])
def logout_dashboard(n_clicks):
    if n_clicks > 0:
        return '/'
@app.callback(
    Output('url_login_df', 'pathname')
    , [Input('back-button', 'n_clicks')])
def logout_dashboard(n_clicks):
    if n_clicks > 0:
        return '/'
# Create callbacks
@app.callback(
    Output('url_logout', 'pathname')
    , [Input('back-button', 'n_clicks')])
def logout_dashboard(n_clicks):
    if n_clicks > 0:
        return '/'

###############
# Upload data callback
###############

def parse_contents(contents, filename, date):
    global transactions_df
    global households_df
    global products_df
    global all_three_combined_df

    content_type, content_string = contents.split(',')

    filename = filename.lower()

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            upload_df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            upload_df = pd.read_excel(io.BytesIO(decoded))

        if 'transaction' in filename:
            transactions_df = pd.concat([transactions_df, upload_df], axis=0).drop_duplicates()
            all_three_combined_df = None
            return display_dashboard()
        elif 'household' in filename:
            households_df = pd.concat([households_df, upload_df], axis=0).drop_duplicates()
            all_three_combined_df = None
            return display_dashboard()
        elif 'product' in filename:
            products_df = pd.concat([products_df, upload_df], axis=0).drop_duplicates()
            all_three_combined_df = None
            return display_dashboard()
        else:
            return display_dashboard()

    except Exception as e:
        print(e)
        return html.Div([
            f'There was an error processing {filename}.'
        ])


@app.callback(Output('page-content', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def upload_data(contents, filename, file_date):
    if contents is not None:
        children = parse_contents(contents, filename, file_date)
        return children

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='80', debug=True)