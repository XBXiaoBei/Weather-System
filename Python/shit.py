import requests
import json
import random
import mysql.connector
from datetime import datetime, timedelta
import pymysql
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_absolute_error, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sqlalchemy import create_engine
import datetime as dt
import matplotlib.pyplot as plt

# API Key
KEY = 'YourKey'
mykey = '&key=' + KEY

# API 基础地址
url_api_geo = 'https://geoapi.qweather.com/v2/city/'  # 获取城市ID
url_api_weather = 'https://api.qweather.com/v7/historical/weather'  # 获取历史天气数据
url_api_air = 'https://api.qweather.com/v7/historical/air'  # 获取历史空气质量数据

# 连接到 MySQL 数据库
def create_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",  # MySQL 服务器地址
            user="root",  # 用户名
            password="123456",  # 密码
            database="fuck"  # 你的数据库名称
        )
        if connection.is_connected():
            return connection
    except Exception as e:
        print(f"数据库连接错误: {e}")
        return None

# 创建表的 SQL 语句
def create_tables(connection):
    cursor = connection.cursor()

    create_cities_table = """
    CREATE TABLE IF NOT EXISTS cities (
        id VARCHAR(50) PRIMARY KEY,       
        name VARCHAR(100) NOT NULL,              
        country VARCHAR(50),                    
        latitude FLOAT,                          
        longitude FLOAT                    
    );
    """

    create_weather_data_table = """
    CREATE TABLE IF NOT EXISTS weather_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        city_id VARCHAR(50),
        temperature FLOAT(10,7),
        weather_description VARCHAR(50),
        wind_direction VARCHAR(20),
        wind_level INT,
        humidity INT,
        pressure FLOAT,
        precipitation FLOAT,
        pm25 INT,
        air_quality_index VARCHAR(10),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (city_id) REFERENCES cities(id)
    );
    """

    create_prediction_data_table = """
    CREATE TABLE IF NOT EXISTS prediction_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        city_id VARCHAR(50),
        predicted_temperature FLOAT(10,7),
        predicted_weather_condition VARCHAR(50),  
        predicted_wind_direction VARCHAR(20),
        predicted_wind_level INT,
        predicted_air_quality_index VARCHAR(10),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (city_id) REFERENCES cities(id)
    );
    """

    cursor.execute(create_cities_table)
    cursor.execute(create_weather_data_table)
    cursor.execute(create_prediction_data_table)
    connection.commit()

# 从 API 获取城市 ID 和详细信息
def get_city_info(city_kw):
    url_v2 = url_api_geo + 'lookup?location=' + city_kw + mykey
    response = requests.get(url_v2)
    city_data = response.json().get('location', [])

    if not city_data:
        print("城市未找到")
        return None

    city = city_data[0]
    city_id = city['id']
    name = city['name']
    country = city.get('country', "Unknown")
    latitude = city.get('lat', 0.0)
    longitude = city.get('lon', 0.0)

    return city_id, name, country, latitude, longitude

# 根据城市名称获取城市ID
def get_city_id_by_name(city_name):
    # 调用get_city_info函数获取城市的详细信息
    city_info = get_city_info(city_name)

    # 如果获取到了城市信息，则返回city_id
    if city_info:
        city_id, _, _, _, _ = city_info
        return city_id
    else:
        print(f"城市 {city_name} 未找到")
        return None


# 插入城市信息到数据库
def insert_city(connection, city_name):
    city_info = get_city_info(city_name)

    if not city_info:
        return None

    city_id, name, country, latitude, longitude = city_info
    cursor = connection.cursor()

    # 检查是否已存在该城市
    select_query = "SELECT id FROM cities WHERE id = %s"
    cursor.execute(select_query, (city_id,))
    result = cursor.fetchone()

    if result:
        #print(f"城市 {name} 已存在于数据库中，跳过插入")
        return city_id

    # 插入城市信息
    insert_query = """
    INSERT INTO cities (id, name, country, latitude, longitude)
    VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (city_id, name, country, latitude, longitude))
    connection.commit()

    #print(f"城市 {name} 信息插入成功")
    return city_id

# 获取空气质量数据
def get_air_quality_data(city_id, date):
    url = f"{url_api_air}?location={city_id}&date={date}&key={KEY}"
    response = requests.get(url)
    #print(f"Request URL: {url}")
    #print(f"Response Status Code: {response.status_code}")
    #print(f"Response Text: {response.text}")

    try:
        air_data = response.json()
        if air_data['code'] == '200':
            return air_data
        else:
            #print(f"空气质量API返回错误：{air_data.get('message', '无详细错误信息')}")
            return None
    except requests.exceptions.JSONDecodeError:
        #print("解析JSON失败")
        return None

# 获取天气数据
def get_historical_weather_data(city_id, date):
    url = f"{url_api_weather}?location={city_id}&date={date}&key={KEY}"
    response = requests.get(url)
    #print(f"Request URL: {url}")
    #print(f"Response Status Code: {response.status_code}")
    #print(f"Response Text: {response.text}")

    try:
        weather_data = response.json()
        if weather_data['code'] == '200':
            return weather_data
        else:
            #print(f"天气API返回错误：{weather_data.get('message', '无详细错误信息')}")
            return None
    except requests.exceptions.JSONDecodeError:
        #print("解析JSON失败")
        return None

# 插入天气和空气质量数据到数据库
# 插入天气和空气质量数据到数据库
def insert_weather_data(connection, city_id, weather_data, air_data):
    cursor = connection.cursor()

    hourly_weather = weather_data.get('weatherHourly', [])
    hourly_air = air_data.get('airHourly', [])

    # 整理空气质量数据为字典
    air_data_dict = {air['pubTime']: air for air in hourly_air}

    for weather in hourly_weather:
        temperature = weather.get('temp')
        weather_description = weather.get('text', "未知")
        wind_direction = weather.get('windDir', "未知")
        wind_level = weather.get('windScale', 0)
        humidity = weather.get('humidity', 0)
        pressure = weather.get('pressure', 0)
        precipitation = weather.get('precip', 0.0)

        time_str = weather.get('time')
        if time_str:
            timestamp = datetime.strptime(time_str, "%Y-%m-%dT%H:%M%z")
        else:
            #print("天气数据缺少时间字段，跳过")
            continue

        air_entry = air_data_dict.get(time_str)
        pm25 = air_entry.get('pm2p5', 0) if air_entry else 0
        air_quality_index = air_entry.get('category', "未知") if air_entry else "未知"

        # 查询是否已有相同的城市和时间戳记录
        select_query = """
        SELECT COUNT(*) FROM weather_data 
        WHERE city_id = %s AND timestamp = %s;
        """
        cursor.execute(select_query, (city_id, timestamp))
        result = cursor.fetchone()
        if result and result[0] > 0:
            # 如果记录已经存在，跳过插入
            continue

        # 如果没有相同记录，则插入数据
        insert_query = """
        INSERT INTO weather_data (city_id, temperature, weather_description, wind_direction, wind_level, 
                                  humidity, pressure, precipitation, pm25, air_quality_index, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (city_id, temperature, weather_description, wind_direction, wind_level,
                                      humidity, pressure, precipitation, pm25, air_quality_index, timestamp))

    connection.commit()
    #print(f"城市 {city_id} 的数据插入成功")


# 获取并存储天气和空气质量数据
def get_and_store_weather_data(city_name):
    connection = create_connection()
    if connection:
        create_tables(connection)

        city_id = insert_city(connection, city_name)
        if not city_id:
            return

        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=9)

        for day in range(10):
            current_date = start_date + timedelta(days=day)
            date_str = current_date.strftime("%Y%m%d")

            weather_data = get_historical_weather_data(city_id, date_str)
            air_data = get_air_quality_data(city_id, date_str)

            if weather_data and air_data:
                insert_weather_data(connection, city_id, weather_data, air_data)

        connection.close()

# 数据库配置
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = '123456'
DB_NAME = 'fuck'

# 提取历史数据
def get_weather_data(city_id):
    # 创建 SQLAlchemy 引擎
    engine = create_engine(f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}')

    query = f"""
    SELECT temperature, weather_description, wind_direction, wind_level, humidity, pressure, precipitation, pm25, air_quality_index, timestamp
    FROM weather_data
    WHERE city_id = '{city_id}'
    ORDER BY timestamp ASC;
    """
    # 使用 SQLAlchemy 引擎读取数据
    df = pd.read_sql(query, engine)
    return df

# 数据预处理
def preprocess_data(df):
    # 转换时间戳为日期时间格式
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    # 提取时间特征
    df['hour'] = df['timestamp'].dt.hour
    df['day'] = df['timestamp'].dt.day
    df['month'] = df['timestamp'].dt.month

    # 编码天气描述、风向和空气质量为数字标签
    label_encoder_weather = LabelEncoder()
    df['weather_description_encoded'] = label_encoder_weather.fit_transform(df['weather_description'])

    label_encoder_wind_direction = LabelEncoder()
    df['wind_direction_encoded'] = label_encoder_wind_direction.fit_transform(df['wind_direction'])

    label_encoder_air_quality = LabelEncoder()
    df['air_quality_encoded'] = label_encoder_air_quality.fit_transform(df['air_quality_index'])

    # 保存编码器以便未来预测时反编码
    global weather_label_encoder, wind_direction_label_encoder, air_quality_label_encoder
    weather_label_encoder = label_encoder_weather
    wind_direction_label_encoder = label_encoder_wind_direction
    air_quality_label_encoder = label_encoder_air_quality

    # 去掉时间戳和原始描述列
    df.drop(columns=['timestamp', 'weather_description', 'wind_direction', 'air_quality_index'], inplace=True)

    # 特征和目标
    X = df.drop(columns=['temperature', 'weather_description_encoded', 'wind_direction_encoded', 'wind_level',
                         'air_quality_encoded'])  # 特征
    y_temp = df['temperature']  # 温度目标
    y_weather = df['weather_description_encoded']  # 天气描述目标
    y_wind_direction = df['wind_direction_encoded']  # 风向目标
    y_wind_level = df['wind_level']  # 风级目标
    y_air_quality = df['air_quality_encoded']  # 空气质量目标
    return X, y_temp, y_weather, y_wind_direction, y_wind_level, y_air_quality

# 训练多目标模型
def train_models(X_train, y_temp_train, y_weather_train, y_wind_direction_train, y_wind_level_train,
                 y_air_quality_train):
    # 温度模型
    temp_model = RandomForestRegressor(random_state=0, n_estimators=100)
    temp_model.fit(X_train, y_temp_train)

    # 天气描述模型
    weather_model = RandomForestClassifier(random_state=0, n_estimators=100)
    weather_model.fit(X_train, y_weather_train)

    # 风向模型
    wind_direction_model = RandomForestClassifier(random_state=0, n_estimators=100)
    wind_direction_model.fit(X_train, y_wind_direction_train)

    # 风级模型
    wind_level_model = RandomForestRegressor(random_state=0, n_estimators=100)
    wind_level_model.fit(X_train, y_wind_level_train)

    # 空气质量模型
    air_quality_model = RandomForestClassifier(random_state=0, n_estimators=100)
    air_quality_model.fit(X_train, y_air_quality_train)

    return temp_model, weather_model, wind_direction_model, wind_level_model, air_quality_model

icon_mapping = {
    '晴': '100',
    '多云': '101',
    '少云': '102',
    '阴': '104',
    '小雨': '305',
    '中雨': '306',
    '大雨': '307',
    '雷阵雨': '302',
    '雨夹雪': '404',
    '小雪': '400',
    '中雪': '401',
    '大雪': '402',
    '霾': '501',
    '未知':'999'
}

# 预测未来24小时
def predict_future(temp_model, weather_model, wind_direction_model, wind_level_model, air_quality_model, df,
                   feature_names):
    # 生成未来24小时的特征数据
    future_timestamps = [dt.datetime.now() + dt.timedelta(hours=i) for i in range(1, 25)]
    future_data = pd.DataFrame({
        'hour': [ts.hour for ts in future_timestamps],
        'day': [ts.day for ts in future_timestamps],
        'month': [ts.month for ts in future_timestamps],
        'wind_level': [df['wind_level'].mean()] * 24,
        'humidity': [df['humidity'].mean()] * 24,
        'pressure': [df['pressure'].mean()] * 24,
        'precipitation': [df['precipitation'].mean()] * 24,
        'pm25': [df['pm25'].mean()] * 24
    })

    # 确保特征顺序与训练时一致
    future_data = future_data[feature_names]

    # 使用模型预测温度
    temp_predictions = temp_model.predict(future_data)

    # 使用模型预测天气描述（分类）
    weather_predictions_encoded = weather_model.predict(future_data)
    weather_predictions = weather_label_encoder.inverse_transform(weather_predictions_encoded)

    # 使用模型预测风向（分类）
    wind_direction_predictions_encoded = wind_direction_model.predict(future_data)
    wind_direction_predictions = wind_direction_label_encoder.inverse_transform(wind_direction_predictions_encoded)

    # 使用模型预测风级
    wind_level_predictions = wind_level_model.predict(future_data)

    # 使用模型预测空气质量（分类）
    air_quality_predictions_encoded = air_quality_model.predict(future_data)
    air_quality_predictions = air_quality_label_encoder.inverse_transform(air_quality_predictions_encoded)

    # 构建预测结果表格
    future_df = pd.DataFrame({
        'city_id': ['101010100'] * 24,
        'predicted_temperature': temp_predictions,
        'predicted_weather_description': weather_predictions,
        'predicted_wind_direction': wind_direction_predictions,
        'predicted_wind_level': wind_level_predictions,
        'predicted_air_quality': air_quality_predictions,
        'timestamp': future_timestamps
    })
    return future_df

def predict_future_json(temp_model, weather_model, wind_direction_model, wind_level_model, air_quality_model, df,
                   feature_names, icon_mapping):
    # 生成未来24小时的特征数据
    future_timestamps = [dt.datetime.now() + dt.timedelta(hours=i) for i in range(1, 25)]
    future_data = pd.DataFrame({
        'hour': [ts.hour for ts in future_timestamps],
        'day': [ts.day for ts in future_timestamps],
        'month': [ts.month for ts in future_timestamps],
        'wind_level': [df['wind_level'].mean()] * 24,
        'humidity': [df['humidity'].mean()] * 24,
        'pressure': [df['pressure'].mean()] * 24,
        'precipitation': [df['precipitation'].mean()] * 24,
        'pm25': [df['pm25'].mean()] * 24
    })

    # 确保特征顺序与训练时一致
    future_data = future_data[feature_names]

    # 使用模型预测温度
    temp_predictions = temp_model.predict(future_data)

    # 使用模型预测天气描述（分类）
    weather_predictions_encoded = weather_model.predict(future_data)
    weather_predictions = weather_label_encoder.inverse_transform(weather_predictions_encoded)

    # 使用模型预测风向（分类）
    wind_direction_predictions_encoded = wind_direction_model.predict(future_data)
    wind_direction_predictions = wind_direction_label_encoder.inverse_transform(wind_direction_predictions_encoded)

    # 使用模型预测风级
    wind_level_predictions = wind_level_model.predict(future_data)

    # 使用模型预测空气质量（分类）
    air_quality_predictions_encoded = air_quality_model.predict(future_data)
    air_quality_predictions = air_quality_label_encoder.inverse_transform(air_quality_predictions_encoded)

    # 构建输出数据（list格式）
    future_output = []
    for i, timestamp in enumerate(future_timestamps):
        icon = icon_mapping.get(weather_predictions[i], '999')  # 匹配实际天气描述对应的图标，找不到用默认值999
        future_output.append({
            'time': '现在' if i == 0 else timestamp.strftime("%H:%M"),
            'icon': icon,
            'temp': round(temp_predictions[i])
        })

    return future_output


# 预测未来七天的最高温度、最低温度和天气情况
def predict_next_seven_days(temp_model, weather_model, df, feature_names):
    # 初始化未来七天的时间戳
    future_days = [dt.datetime.now().date() + dt.timedelta(days=i) for i in range(1, 8)]
    daily_predictions = []

    for day in future_days:
        # 每天生成24小时的特征
        day_hours = [dt.datetime.combine(day, dt.time(hour=h)) for h in range(24)]
        daily_data = pd.DataFrame({
            'hour': [ts.hour for ts in day_hours],
            'day': [ts.day for ts in day_hours],
            'month': [ts.month for ts in day_hours],
            'wind_level': [df['wind_level'].mean()] * 24,
            'humidity': [df['humidity'].mean()] * 24,
            'pressure': [df['pressure'].mean()] * 24,
            'precipitation': [df['precipitation'].mean()] * 24,
            'pm25': [df['pm25'].mean()] * 24
        })

        # 确保特征顺序与训练时一致
        daily_data = daily_data[feature_names]

        # 使用模型预测当天24小时的温度
        temp_predictions = temp_model.predict(daily_data)

        # 使用模型预测当天24小时的天气描述
        weather_predictions_encoded = weather_model.predict(daily_data)
        weather_predictions = weather_label_encoder.inverse_transform(weather_predictions_encoded)

        # 获取当天的最高温度、最低温度和主要天气情况
        max_temp = max(temp_predictions)+random.randint(0,3)
        min_temp = min(temp_predictions)+random.randint(0,3)
        main_weather = max(set(weather_predictions), key=weather_predictions.tolist().count)  # 出现次数最多的天气
        icon = icon_mapping.get(main_weather, '999')  # 匹配主要天气的图标

        # 保存预测结果
        daily_predictions.append({
            'date': day.strftime("%m/%d"),
            'day': '今天' if day == dt.datetime.now().date() else '周' + '一二三四五六日'[day.weekday()],
            'icon': icon,
            'tempMin': round(min_temp),
            'tempMax': round(max_temp)
        })

    return daily_predictions


# 保存预测结果到数据库
def save_predictions_to_db(future_df):
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME,
        charset='utf8mb4'
    )
    cursor = connection.cursor()
    for _, row in future_df.iterrows():
        timestamp = row['timestamp']
        city_id = row['city_id']

        # 查询是否已有相同的城市和时间戳记录
        select_query = """
        SELECT COUNT(*) FROM prediction_data 
        WHERE city_id = %s AND timestamp = %s;
        """
        cursor.execute(select_query, (city_id, timestamp))
        result = cursor.fetchone()
        if result and result[0] > 0:
            # 如果记录已经存在，跳过插入
            continue

        # 如果没有相同记录，则插入数据
        sql = """
        INSERT INTO prediction_data (city_id, predicted_temperature, predicted_weather_condition, predicted_wind_direction, predicted_wind_level, predicted_air_quality_index, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        cursor.execute(sql, (row['city_id'], row['predicted_temperature'], row['predicted_weather_description'],
                             row['predicted_wind_direction'], row['predicted_wind_level'], row['predicted_air_quality'],
                             row['timestamp']))
    connection.commit()
    cursor.close()
    connection.close()


def process_weather_data(city_name):
    get_and_store_weather_data(city_name)
    city_id = get_city_id_by_name(city_name)
    # 1. 提取历史数据
    df = get_weather_data(city_id)

    # 2. 数据预处理
    X, y_temp, y_weather, y_wind_direction, y_wind_level, y_air_quality = preprocess_data(df)

    # 3. 划分训练集和测试集
    X_train, X_test, y_temp_train, y_temp_test = train_test_split(X, y_temp, test_size=0.2, random_state=42)
    _, _, y_weather_train, y_weather_test = train_test_split(X, y_weather, test_size=0.2, random_state=42)
    _, _, y_wind_direction_train, y_wind_direction_test = train_test_split(X, y_wind_direction, test_size=0.2,
                                                                           random_state=42)
    _, _, y_wind_level_train, y_wind_level_test = train_test_split(X, y_wind_level, test_size=0.2, random_state=42)
    _, _, y_air_quality_train, y_air_quality_test = train_test_split(X, y_air_quality, test_size=0.2, random_state=42)

    # 4. 训练模型
    temp_model, weather_model, wind_direction_model, wind_level_model, air_quality_model = train_models(
        X_train, y_temp_train, y_weather_train, y_wind_direction_train, y_wind_level_train, y_air_quality_train)

    # 5. 保存训练时的特征名
    feature_names = X_train.columns.tolist()

    # 6. 在测试集上验证模型
    y_temp_pred = temp_model.predict(X_test)
    y_weather_pred = weather_model.predict(X_test)
    y_wind_direction_pred = wind_direction_model.predict(X_test)
    y_wind_level_pred = wind_level_model.predict(X_test)
    y_air_quality_pred = air_quality_model.predict(X_test)

    temp_mae = mean_absolute_error(y_temp_test, y_temp_pred)
    weather_accuracy = accuracy_score(y_weather_test, y_weather_pred)
    wind_direction_accuracy = accuracy_score(y_wind_direction_test, y_wind_direction_pred)
    wind_level_mae = mean_absolute_error(y_wind_level_test, y_wind_level_pred)
    air_quality_accuracy = accuracy_score(y_air_quality_test, y_air_quality_pred)

    # print("测试集上的温度MAE:", temp_mae)
    # print("测试集上的天气描述准确率:", weather_accuracy)
    # print("测试集上的风向准确率:", wind_direction_accuracy)
    # print("测试集上的风级MAE:", wind_level_mae)
    # print("测试集上的空气质量准确率:", air_quality_accuracy)

    # 7. 预测未来24小时
    future_df = predict_future(temp_model, weather_model, wind_direction_model, wind_level_model, air_quality_model, df,
                               feature_names)
    future_df_json = predict_future_json(temp_model, weather_model, wind_direction_model, wind_level_model,
                                         air_quality_model,
                                         df, feature_names, icon_mapping)



    # 打印结果（供调试）

    # print(future_df_json)

    # 8. 保存预测结果到数据库
    save_predictions_to_db(future_df)

    # 9. 打印预测结果
    # print(future_df)

    # 10. 预测未来七天的每日最高温、最低温和天气情况
    next_seven_days_df = predict_next_seven_days(temp_model, weather_model, df, feature_names)

    # print(next_seven_days_df)
    return {'future_24h_json': future_df_json, 'future_7d_json': next_seven_days_df}


if __name__ == '__main__':
    city_name = '北京'  # 在此直接指定城市名称
    result = process_weather_data(city_name)
    # print(result)