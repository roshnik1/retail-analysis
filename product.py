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

class Product(Base):
    __tablename__ = 'product'

    product_num = Column(String(50), primary_key=True)
    department = Column(String(50))
    commodity = Column(String(50))
    brand_ty = Column(String(50))
    natural_organic_flag = Column(String(50))

df = pd.read_csv('data/400_products.csv')
products_df = df.rename(str.strip, axis='columns')

for column in products_df.columns:
    products_df[column] = products_df[column].astype(str)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

for index, row in products_df.iterrows():
    # print(row["HSHD_NUM"], row["L"])

    prod = Product(product_num=row["PRODUCT_NUM"].strip() if row["PRODUCT_NUM"] is not None else "",
                       department=row["DEPARTMENT"].strip() if row["DEPARTMENT"] is not None else "",
                       commodity=row["COMMODITY"].strip() if row["COMMODITY"] is not None else "",
                       brand_ty=row["BRAND_TY"].strip() if row["BRAND_TY"] is not None else "",
                       natural_organic_flag=row["NATURAL_ORGANIC_FLAG"].strip() if row["NATURAL_ORGANIC_FLAG"] is not None else ""
                       )
    session.add(prod)
    session.commit()

# create a metadata object and load the table metadata
metadata = MetaData()
table = Table('product', metadata, autoload=True, autoload_with=engine)

# select all rows from the table
query = table.select()

# execute the query and fetch the results
result = conn.execute(query).fetchall()

print(len(result))

