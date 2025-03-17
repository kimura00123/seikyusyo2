# LIPS LDS Service API 仕様書 (v1.3.0.3601)

**OpenAPI 仕様書ダウンロード:** [openapi.json](https://localhost:8080/openapi.json)

**LIPS サポート:**

*   メール: info@lips-hci.com
*   URL: https://www.lips-hci.com/
*   ライセンス: ©2024 by LIPS Corporation. All rights reserved.

## 概要

このドキュメントは、LIPS LDS (Logistics Dimensioning System) サービスのAPI仕様について記述します。

### カメラストリーミング

カメラは、MJPEG形式で `localhost:7777/camera` にてストリーミングされています。

### 計測写真

*   `/v1/measure` APIを呼び出すと、計測写真が保存されます。
*   写真は、同じサーバーの `/images/` 以下に、`[timestamp].jpg` というファイル名で保存されます。
*   例：`/v1/measure` APIのレスポンスが `{..., "timestamp": "1708569469"}` の場合、写真は `http://localhost:8080/images/1708569469.jpg` で取得できます。

### APIレスポンス

#### 一般的なAPIレスポンス形式

```json
{
    "code": 200,
    "info": "Response message",
    "data": {...}
}
```

*   `code`: HTTPステータスコード
*   `info`: レスポンスメッセージ
*   `data`: レスポンスデータ (APIによって異なる)

#### API レスポンスコード

| Code | Status                                  |
| ---- | --------------------------------------- |
| 200  | OK                                      |
| 400  | Service is not initialized               |
| 403  | Calibration function is not allowed     |
| 411  | Calibration failed                      |
| 412  | Wrong calibration result                 |
| 413  | Measure failed                          |
| 414  | Trail license expired                     |
| 415  | Measured object is not within ROI       |
| 416  | Invalid license                          |
| 418  | Calibration data is not found or corrupted |
| 500  | Service internal error                   |
| 501  | API server is not available             |

## API エンドポイント

### 1. measure

#### `POST /v1/calibrate`

カメラをキャリブレーションします。

**レスポンス (200 OK):**

```json
{
    "code": 200,
    "data": {
        "height": 0, // カメラと地面の間の距離 (cm)。実測値との誤差は1cm未満であること。
        "success": true
    },
    "info": "string"
}
```

#### `POST /v1/measure`

オブジェクトを測定し、寸法を取得します。

**レスポンス (200 OK):**

```json
{
  "code": 200,
  "data": {
    "height": 0,
    "length": 0,
    "px1": 0,
    "px2": 0,
    "px3": 0,
    "px4": 0,
    "px5": 0,
    "px6": 0,
    "px7": 0,
    "px8": 0,
    "py1": 0,
    "py2": 0,
    "py3": 0,
    "py4": 0,
    "py5": 0,
    "py6": 0,
    "py7": 0,
    "py8": 0,
    "sn": "string",
    "success": true,
    "temperature": 0,
    "timestamp": 0,
    "weight": 0,
    "width": 0
  },
  "info": "string"
}
```

*   `pxN`, `pyN`: オブジェクトのバウンディングボックスの8つの座標点 (N=1~8, 1~4は上部、5~8は下部)
    * バウンディングボックスの描画例：`/doc-images/measure_result.png`を参照

#### `GET /v1/system_info`
システムの情報を取得します.

**レスポンス (200 OK):**

```json
{
    "code": 200,
    "data":{
        "apiVersion": "string",
        "cameraHeight": 0,
        "cameraName": "string",
        "cameraSerial": "string",
        "cameraWidth": 0,
        "isScaleEnabled": true,
        "product": "string",
        "rulerDebug": true,
        "scalePort": "string",
        "scaleType": "string"
    },
    "info": "string"
}
```

### 2. Peripheral

#### `POST /v1/peripheral/print_label`

測定情報を含むラベルを印刷します。

**リクエストボディ:**

```json
{
  "height": 0,
  "length": 0,
  "template": "LDS_Template_cm_en.lbx",  // サポートされているテンプレート: ['LDS_Template_cm_en.lbx']
  "weight": 0,
  "width": 0
}
```
* `template`: 必須。

**レスポンス (200 OK):**

```json
{
    "code": 200,
    "data": {
        "success": true
    },
    "info": "string"
}
```

### 3. record

#### `DELETE /v1/record/`

IDでレコードを削除します。

**リクエストボディ:**

```json
{
  "idList": [0]
}
```

*   `idList`: 削除するレコードIDのリスト（必須）

**レスポンス (200 OK):**
(仕様書に記載なし。一般的な成功レスポンスを想定)
```json
{
  "code": 200,
  "info": "Records deleted successfully",
  "data": {}
}
```

#### `GET /v1/record/`

測定レコードをクエリします。

**クエリパラメータ:**

| Parameter   | Type    | Description                                 | Default |
| ----------- | ------- | ------------------------------------------- | ------- |
| sn          | string  | シリアルナンバー                             |         |
| num         | number  | クエリするレコード数                         | 10      |
| start       | number  | クエリ開始時間 (ミリ秒)                      |         |
| end         | integer | クエリ終了時間 (ミリ秒)                      |         |
| widthGt     | number  | 幅が指定値より大きいレコードをクエリ       |         |
| widthLt     | number  | 幅が指定値より小さいレコードをクエリ       |         |
| heightGt    | number  | 高さが指定値より大きいレコードをクエリ       |         |
| heightLt    | number  | 高さが指定値より小さいレコードをクエリ      |         |
| lengthGt    | number  | 長さが指定値より大きいレコードをクエリ      |         |
| lengthLt    | number  | 長さが指定値より小さいレコードをクエリ      |         |
| weightGt    | number  | 重量が指定値より大きいレコードをクエリ      |         |
| weightLt    | number  | 重量が指定値より小さいレコードをクエリ      |         |
| convertNull | boolean | `true`の場合、nullの重量を0に変換           | false   |
| orderDesc   | boolean | レコード作成時間で降順にソート             | true    |

**レスポンス (200 OK):**

```json
{
  "code": 200,
  "data": {
    "recordList": [
      {
        "createdAt": 0,
        "height": 0,
        "id": 0,
        "length": 0,
        "sn": "string",
        "temperature": 0,
        "weight": 0,
        "width": 0
      }
    ]
  },
  "info": "string"
}
```
#### `GET /v1/record/count`
データベース内のレコード数を取得します。
**レスポンス (200 OK):**

```json
{
    "code": 200,
    "data":{
        "count": 0
    },
    "info": "string"
}
```
### 4. setting

#### `PUT /v1/set_draw_roi`

フレーム内にROIを表示するかどうかを設定します。

**リクエストボディ:**

```json
{
  "enable": true,
  "type": "measure" // "measure" or "calibrate"
}
```
* `type`: 必須. 許容値は`"measure"`または`"calibrate"`.

**レスポンス (200 OK):**

```json
{
    "code": 200,
    "data": {
        "success": true,
        "type": "string"
    },
    "info": "string"
}
```

#### `PUT /v1/set_roi`

キャリブレーションまたは測定のROIを設定します。

**リクエストボディ:**

```json
{
  "height": 1, // [0..1]
  "type": "measure", // "measure" or "calibrate"
  "width": 1 // [0..1]
}
```

*   `width`:  ROIの幅の比率 (画像全体の幅に対する比率)
*   `height`: ROIの高さの比率 (画像全体の高さに対する比率)
*    `type`: 必須。`"measure"` または `"calibrate"`

**レスポンス (200 OK):**

```json
{
  "code": 200,
  "data": {
    "height": 0,
    "success": true,
    "type": "string",
    "width": 0
  },
  "info": "string"
}
```

---
```

**補足:**

*   このマークダウン形式の仕様書は、元のHTMLドキュメントから情報を抽出して再構成したものです。
*   元のドキュメントに存在しない情報（例えば、`DELETE /v1/record/`の成功時レスポンスの具体的な内容など）は、一般的なREST APIの慣習に基づいて補完しています。
*   `openapi.json`をダウンロードして、より詳細な定義を確認できます。
*   RedoclyによるドキュメントのURL (`https://redocly.com/redoc/`) へのリンクは削除しました。これは、外部サイトへのリンクであり、必須ではないためです。
*   画像への参照 (例: `/doc-images/measure_result.png`) は、相対パスで記述されています。仕様書と画像の配置場所によって適宜変更してください。
*   コードブロックは、可読性を高めるために言語指定 (e.g., ```json) を追加しました。
*   リクエスト、レスポンスのスキーマ定義は主要部分を抜粋しました。　`openapi.json`で完全な定義を確認してください。
*  エンドポイントのURLは`https://localhost:8080`となっていますが、適宜変更してください。

このマークダウン形式の仕様書が、APIの理解と利用に役立つことを願っています。
