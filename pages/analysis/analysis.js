// pages/analysis/analysis.js
Page({
  data: {
    forecastData: [
        { date: "12/20", day: "昨天", icon: "101", tempMin: 0, tempMax: 0 },
        { date: "12/21", day: "今天", icon: "100", tempMin: 0, tempMax: 0 },
        { date: "12/22", day: "明天", icon: "100", tempMin: 0, tempMax: 0 },
        { date: "12/23", day: "周一", icon: "100", tempMin: 0, tempMax: 0 },
        { date: "12/24", day: "周二", icon: "101", tempMin: 0, tempMax: 0 },
        { date: "12/25", day: "周三", icon: "100", tempMin: 0, tempMax: 0 },
        { date: "12/26", day: "周四", icon: "101", tempMin: 0, tempMax: 0 },
        { date: "12/27", day: "周五", icon: "100", tempMin: 0, tempMax: 0 },
      ],
    weatherData: [
        { time: "现在", icon: "100", temp: 0 },
        { time: "21:00", icon: "100", temp: 0 },
        { time: "23:00", icon: "100", temp: 0 },
        { time: "01:00", icon: "100", temp: 0 },
        { time: "03:00", icon: "100", temp: 0 },
        { time: "05:00", icon: "100", temp: 0 },
        { time: "07:00", icon: "100", temp: 0 },
        { time: "09:00", icon: "100", temp: 0 },
        { time: "11:00", icon: "100", temp: 0 },
        { time: "13:00", icon: "100", temp: 0 },
        { time: "15:00", icon: "100", temp: 0 },
        { time: "17:00", icon: "100", temp: 0 }
      ],
    search:'',
    name:'',
    city_all:''
  },
Input(e){
    console.log(e);
    let that=this
    let m=e.detail.value
    if(m)
    {that.setData({search:true})}
    else
    {that.setData({search:false})}
    const key='YourKey'
    wx.request({
      url:`https://geoapi.qweather.com/v2/city/lookup?location=${m}&key=${key}`,
      success(res){
          console.log('获取搜索城市');
          console.log(res);
          if(res.data.code!=200)
          {
              console.log('获取失败');
              that.setData({search:false})
          }
          that.setData({city_all:res.data.location})
      }
    })
    },
searchCity(e){
    let that=this
    let index=e.currentTarget.dataset.id
    console.log(e);
    let city=that.data.city_all
    that.setData({
        search:false,
        inputValue:'',
        name: city[index].name
    })
    that.sendDataToServer()
},

sendDataToServer() {
    let that=this
    const name = this.data.name; // 获取用户输入的数据
    if (!name) {
      wx.showToast({
        title: '请填写完整信息',
        icon: 'none'
      });
      return;
    }
    wx.request({
      url: 'http://172.20.10.3:5000/weather', // 替换为您的后端地址
      method: 'POST',
      data: {name},
      header: {
        'content-type': 'application/json' // 设置请求头
      },
      success: (res) => {
        console.log('后端返回数据:', res); // 打印后端返回的数据
        console.log('后端返回数据:', res.data.data.forecastData);
        console.log('后端返回数据:', res.data.data.weatherData);
        wx.showToast({
          title: '数据发送成功！',
          icon: 'success'
        });
        that.setData({
            forecastData: res.data.data.forecastData,
            weatherData: res.data.data.weatherData
        })
      },
      fail: (err) => {
        console.error('请求失败:', err);
        wx.showToast({
          title: '发送失败，请检查网络',
          icon: 'none'
        });
      }
    });
},

onLoad(options) {
    this.setData({
        name: '北京'
    })
    this.sendDataToServer()
  },
onShow: function() {
    this.setData({
        name: '北京'
    })
    this.sendDataToServer()
},
onPullDownRefresh: function() {
    this.sendDataToServer()
    wx.stopPullDownRefresh()
}
})