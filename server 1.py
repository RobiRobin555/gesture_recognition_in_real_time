from flask import Flask, request
import csv
import os

app = Flask(__name__)
CSV_FILE = "gesture_data.csv"

# Nếu file CSV chưa tồn tại, tạo file và ghi header
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Time", "AccelX", "AccelY", "AccelZ", "GyroX", "GyroY", "GyroZ", "Temp", "Marker"])

@app.route("/save_data", methods=["GET"])
def save_data():
    """
    Nhận dữ liệu GET từ ESP8266.
    Các tham số truyền vào:
      - t: thời gian (mili giây)
      - ax, ay, az: giá trị gia tốc theo 3 trục
      - gx, gy, gz: giá trị con quay theo 3 trục
      - temp: nhiệt độ
      - marker: (tuỳ chọn) đánh dấu 'START' hay 'END' cho cử chỉ động
    """
    t = request.args.get("t", "")
    ax = request.args.get("ax", "")
    ay = request.args.get("ay", "")
    az = request.args.get("az", "")
    gx = request.args.get("gx", "")
    gy = request.args.get("gy", "")
    gz = request.args.get("gz", "")
    temp = request.args.get("temp", "")
    marker = request.args.get("marker", "")  # Dùng để đánh dấu 'START' hay 'END'

    # Ghi dữ liệu vào file CSV
    with open(CSV_FILE, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([t, ax, ay, az, gx, gy, gz, temp, marker])

    return "OK", 200

if __name__ == "__main__":
    # Chạy server trên host '0.0.0.0' để cho ESP8266 truy cập, port 80
    app.run(host="0.0.0.0", port=80)
