import csv
import math
from dash import Dash, html, dcc, dash_table
import dash
# import dash_bootstrap_components as dbc
from dash.dependencies import State
from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform
from sqlalchemy import Table, create_engine, MetaData
from sqlalchemy.sql import select
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import warnings
import os
from flask_login import login_user, logout_user, current_user, LoginManager, UserMixin
import configparser
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker
# import plotly.express as px
# import pandas as pd
import pandas as pd

username = 'roshnik'
password = 'Password123#'
database = 'retail-analysis'
hostname = 'retail-analysis-cloud.mysql.database.azure.com'
root_ca = '/Users/khatr/OneDrive/Documents/Cloud-Computing-Final-Project/DigiCertGlobalRootCA.crt.pem'

db_uri = f"mysql+pymysql://{username}:{password}@{hostname}/{database}"

engine = create_engine(
    f"mysql+pymysql://{username}:{password}@{hostname}/{database}",
    connect_args={
        "ssl": {
            "ssl_ca": root_ca
        }
    },
    echo=True
)

db = SQLAlchemy()
config = configparser.ConfigParser()
conn = engine.connect()

print(engine)

Base = declarative_base()

class Household(Base):
    __tablename__ = 'household'

    hshd_num = Column(String(50), primary_key=True)
    l = Column(String(50))
    age_range = Column(String(50))
    marital = Column(String(50))
    income_range = Column(String(50))
    homeowner = Column(String(50))
    hshd_composition = Column(String(50))
    hh_size = Column(String(50))
    children = Column(String(50))

df = pd.read_csv('data/400_households.csv')
households_df = df.rename(str.strip, axis='columns')

for column in households_df.columns:
    households_df[column] = households_df[column].astype(str)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

for index, row in households_df.iterrows():
    # print(row["HSHD_NUM"], row["L"])

    h_hold = Household(hshd_num=row["HSHD_NUM"].strip() if row["HSHD_NUM"] is not None else "",
                       l=row["L"].strip() if row["L"] is not None else "",
                       age_range=row["AGE_RANGE"].strip() if row["AGE_RANGE"] is not None else "",
                       marital=row["MARITAL"].strip() if row["MARITAL"] is not None else "",
                       income_range=row["INCOME_RANGE"].strip() if row["INCOME_RANGE"] is not None else "",
                       homeowner=row["HOMEOWNER"].strip() if row["HOMEOWNER"] is not None else "",
                       hshd_composition=row["HSHD_COMPOSITION"].strip() if row["HSHD_COMPOSITION"] is not None else "",
                       hh_size=row["HH_SIZE"].strip() if row["HH_SIZE"] is not None  else "",
                       children=row["CHILDREN"].strip() if row["CHILDREN"] is not None else ""
                       )
    session.add(h_hold)
    session.commit()

# create a metadata object and load the table metadata
metadata = MetaData()
table = Table('household', metadata, autoload=True, autoload_with=engine)

# select all rows from the table
query = table.select()

# execute the query and fetch the results
result = conn.execute(query).fetchall()

print(len(result))

