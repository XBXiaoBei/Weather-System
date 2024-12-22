function getLanguage() {
  //  获取本次存储的语言版本，默认中文
  return wx.getStorageSync('language') || 'zh_CN'
}
function translate() {
  //  返回翻译对照映射表
  return require('../i18n/' + getLanguage() + '.js').languageMap
}
function translateText(desc) {
  //  翻译
  return translate()[desc] || desc
}

module.exports = {
  getLanguage: getLanguage,
  _t: translate, // JSON映射表
  _: translateText // 翻译函数
}
