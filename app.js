App({
    globalData: {
        latitude: null, // 全局纬度
        longitude: null // 全局经度
      },
    
  /**
   * 当小程序初始化完成时，会触发 onLaunch（全局只触发一次）
   */
//   onLaunch: function () {
//     const that = this;
//     wx.getLocation({
//       type: 'wgs84',
//       success(res) {
//         console.log('全局位置获取成功:', res);
//         that.globalData.latitude = res.latitude;
//         that.globalData.longitude = res.longitude;
//       },
//       fail(err) {
//         console.error('获取全局位置失败:', err);
//       }
//     });

    
//   },

  /**
   * 当小程序启动，或从后台进入前台显示，会触发 onShow
   */
  onShow: function (options) {
    
  },

  /**
   * 当小程序从前台进入后台，会触发 onHide
   */
  onHide: function () {
    
  },

  /**
   * 当小程序发生脚本错误，或者 api 调用失败时，会触发 onError 并带上错误信息
   */
  onError: function (msg) {
    
  }
})
