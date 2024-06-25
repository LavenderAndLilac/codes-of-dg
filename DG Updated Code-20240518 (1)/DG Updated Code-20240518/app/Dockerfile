FROM arm64v8/python:3.6.15-slim-bullseye
WORKDIR /app
RUN apt-get update
RUN pip install --upgrade pip
RUN mkdir data
COPY Imports.py ./
COPY IOT_functions.py ./
COPY Automation_functions.py ./
COPY BMS_functions.py ./
COPY Variables.py ./
COPY IOT_functions.py ./
COPY requirements.txt ./
COPY abc.csv ./
COPY BatteryAhData.csv ./
COPY lookuptable.csv ./
COPY data/plant_constants ./data
COPY data/Forecasted_values ./data
COPY data/reset_parameter.txt ./data
COPY data/id.txt ./data
COPY data/country_code.txt ./data
RUN pip install --no-cache -r requirements.txt
RUN chmod 777 /app/abc.csv
RUN chmod 777 /app/BatteryAhData.csv
RUN chmod 777 /app/data/reset_parameter.txt
RUN chmod 777 /app/data/id.txt
RUN chmod 777 /app/data/Forecasted_values

COPY . .

CMD [ "python3", "-u", "./main.py" ]