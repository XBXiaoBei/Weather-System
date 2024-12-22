from flask import Flask, request, jsonify
import shit

app = Flask(__name__)

# 测试路由
@app.route('/')
def home():
    return "Python 后端运行正常！"

# 接收天气数据
@app.route('/weather', methods=['POST'])
def process_weather():
    # 获取 JSON 数据
    data = request.json
    print(data)
    city = data.get('name', '未知城市')  # 获取城市，默认为 "未知城市"

    result = shit.process_weather_data(city)

    try:

        # 返回结果
        return jsonify({
            'status': 'success',
            'message': f'成功接收数据：{city}',
            'data': {
                'city': city,
                'forecastData': result['future_7d_json'],
                'weatherData': result['future_24h_json']
            }
        })
    except ValueError:
        # 处理数据格式错误的情况
        return jsonify({
            'status': 'error',
            'message': '温度格式错误，请输入数字'
        }), 400

if __name__ == '__main__':
    # 启动服务
    app.run(host='0.0.0.0', port=5000)  # 在本地监听 5000 端口
