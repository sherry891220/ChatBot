# About function
## 超音波
* Function：distance()
* 用途：偵測user與裝置的距離，當距離小於40公分時，停止偵測並開始播放語音。
## 馬達
* Function：motor()
* 用途：當裝置詢問user有沒有問題要詢問時，開始轉動馬達3秒。
## OLED
* Function：Display_text()
* 用途：將想要顯示的內容顯示在OLED上。
## 語音對話
* Function：
   * process()、 askForService():語音轉文字
   * process_res()、askForService_res():文字轉語音
   * main()、record():錄音
* 用途：裝置進行對話，讓裝置辨識user的問題並回覆。
