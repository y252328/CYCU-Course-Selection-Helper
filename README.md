# CYCU-Course-Selection-Helper

此腳本僅供研究使用，請勿用於其他用途。

## 環境需求/Requires

1. Python 3.5+
2. requests 2.18.4+

## 執行/Run

* 使用pip安裝
    ``` bash
    $ pip install cycuCourse
    $ selection_helper
    ```

* 直接run selection_helper.py source script
    ``` bash
    $ python <selection_helper.py>
    ```

## 說明/Help

``` bash
login  : 登入選課系統
l      : 快速登入(使用預設帳號)
set time : 設定開始選課時間
show time : 顯示開始選課時間
check  : 確認是否有登入
list   : 列出已選到課程
del course : 退選已選上的課(不可逆操作，請謹慎使用)
del append : 取消遞補(不可逆操作，請謹慎使用)
summory: 列出欲加選課程清單
add    : 增加欲加選課程
del    : 刪除所有欲選課程
run    : 執行自動加選
cancel : 取消自動加選
logout : 登出選課系統
exit   : 離開程式
```

## API

cycuCourse.py裡CycuCourse類別提人性化的高階選課操作，支援登入、加退選及追蹤等功能。

## License

本專案使用[MIT License](https://github.com/y252328/CYCU-Course-Selection-Helper/blob/master/LICENSE)授權。
