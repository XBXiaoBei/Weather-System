const base = require('../../utils/language.js')
const _ = base._

Page({
  data: {
    name:'',
    latitude: '',
    longitude: '',
    lang:'',
    _t: '',
    inputValue:'',
    city_all:'',    
    search: false,
    shi:'未知',
    qu:'wz',
    time:'2024-01-01',
    temp:'00',
    tianqi:'wz',
    fengxiang:'zw',
    dengji:'2',
    humi:'23',
    icon:'999',
    jiangshui:'wz',
    AQI:'wz',
    jiance:'zz',
    pa:'1211',
    PM:'333',
    see:'234'
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
    let lon=city[index].lon
    let lat=city[index].lat
    let name=city[index].name
    console.log(lon)
    console.log(lat)
    console.log(name)
    that.setData({
        search:false,
        inputValue:'',
        longitude: city[index].lon,
        latitude: city[index].lat
    })
    that.getWeather(name,lon,lat)
  },
  //获取天气
  getnowweather() {
      this.getUserLocation()
      this.getWeather()
  },
  getWeather(name,lon,lat){
    let that=this
    const l = that.data.lang
    if (name) {
        const m = name
        const key='YourKey'
        console.log(m)
        const latitude = lat
        const longitude = lon
        wx.request({
        url:`https://geoapi.qweather.com/v2/city/lookup?location=${m}&key=${key}&lang=${l}`,
        success(res){
            console.log(res)
            console.log(res.data.location[0].adm1);//市
            console.log(res.data.location[0].name);//qu
            that.setData({
                shi:res.data.location[0].adm1,
                qu:res.data.location[0].name
            })
            wx.request({
                url: `https://devapi.qweather.com/v7/weather/now?location=${longitude},${latitude}&key=${key}&lang=${l}`,
                success(res){
                    console.log(res.data.now);
                    that.setData({
                        AQI:res.data.now.feelsLike,
                        jiance:res.data.now.vis,

                        icon:res.data.now.icon,
                        tianqi:res.data.now.text,
                        temp:res.data.now.temp,
                        fengxiang:res.data.now.windDir,//fengxiang 
                        dengji:res.data.now.windScale,
                        humi:res.data.now.humidity,
                        pa:res.data.now.pressure,
                        jiangshui:res.data.now.precip,
                        time:res.data.updateTime.slice(11,16)                         
                    })
                    wx.request({
                        url:`https://devapi.qweather.com/v7/air/now?location=${longitude},${latitude}&key=${key}&lang=${l}`,
                    success(res){
                        console.log(res);
                        that.setData({
                            see:res.data.now.category,

                            PM:res.data.now.pm2p5,
                            })
                    }
                    })
                }
            })
        }
        
        })
    } else {
        const latitude = that.data.latitude
        const longitude = that.data.longitude
        // console.log(latitude)
        const key='YourKey'
        wx.request({
            url:`https://geoapi.qweather.com/v2/city/lookup?location=${longitude},${latitude}&key=${key}&lang=${l}`,
            success(res){
                console.log(res)
                console.log(res.data.location[0].adm1);//市
                console.log(res.data.location[0].name);//qu
                that.setData({
                    shi:res.data.location[0].adm1,
                    qu:res.data.location[0].name
                })
                wx.request({
                    url: `https://devapi.qweather.com/v7/weather/now?location=${longitude},${latitude}&key=${key}&lang=${l}`,
                    success(res){
                        console.log(res.data);
                        that.setData({
                        AQI:res.data.now.feelsLike,
                        jiance:res.data.now.vis,

                        icon:res.data.now.icon,
                        tianqi:res.data.now.text,
                        temp:res.data.now.temp,
                        fengxiang:res.data.now.windDir,//fengxiang 
                        dengji:res.data.now.windScale,
                        humi:res.data.now.humidity,
                        pa:res.data.now.pressure,
                        jiangshui:res.data.now.precip,
                        time:res.data.updateTime.slice(11,16)                         
                        })
                        wx.request({
                        url:`https://devapi.qweather.com/v7/air/now?location=${longitude},${latitude}&key=${key}&lang=${l}`,
                        success(res){
                            console.log(res.data.now);
                            that.setData({
                                see:res.data.now.category,

                                PM:res.data.now.pm2p5,
                                })
                        }
                        })
                    }
                })
            }
            
            })
    }
    
  },
  getUserLocation() {
    const that = this;
    wx.getLocation({
      type: 'wgs84',
      success(res) {
        console.log('获取位置成功:', res);
        that.setData({
          latitude: res.latitude.toString(),
          longitude: res.longitude.toString()
        });
      },
      fail(err) {
        console.error('获取位置失败:', err);
      }
    });
  },
  onLoad: function (options) {
    this.mixinFn()
    wx.setNavigationBarTitle({
      title: _('天气系统')
    })
    this.getUserLocation();

    this.interval = setInterval(() => {
        this.getWeather()
      }, 10000000);
  },
  reflesh() {
    this.mixinFn()
    wx.setNavigationBarTitle({
      title: _('天气系统')
    })
    this.getWeather()
  },
  mixinFn() {
    this.setData({
      _t: base._t(),
      lang: base._t()['语言']
    })
  },
  onShow: function () {
    this.getWeather()
  },
  onUnload: function () {
    clearInterval(this.interval);
  },
  onPullDownRefresh: function () {
    this.getWeather()
    wx.stopPullDownRefresh()
  }
})