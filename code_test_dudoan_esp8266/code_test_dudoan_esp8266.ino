#include <ESP8266WiFi.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

// Cấu hình WiFi
const char* ssid = "Chip";         // Thay bằng tên WiFi của bạn
const char* password = "123456789a@"; // Thay bằng mật khẩu WiFi của bạn

// Cấu hình Server (địa chỉ IP của máy chạy Python Flask server) và Port
const char* serverHost = " 192.168.1.14";  // Thay bằng địa chỉ IP server của bạn
const uint16_t serverPort = 80;

// Cấu hình nút bấm (để đánh dấu bắt đầu/kết thúc cử chỉ động)
const int buttonPin = 14; // Chọn chân phù hợp với board của bạn
bool collecting = false;  // Cờ báo hiệu có đang thu thập cử chỉ động hay không
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 200; // Thời gian debounce (ms)

// Khai báo cảm biến MPU6050
Adafruit_MPU6050 mpu;

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  // Cấu hình chân nút bấm với nội suy
  pinMode(buttonPin, INPUT_PULLUP);

  // Kết nối WiFi
  Serial.print("Đang kết nối tới WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi đã kết nối!");
  Serial.print("Địa chỉ IP: ");
  Serial.println(WiFi.localIP());
  
  // Khởi tạo MPU6050
  if (!mpu.begin()) {
    Serial.println("Không tìm thấy MPU6050!");
    while (1) {
      delay(10);
    }
  }
  Serial.println("MPU6050 đã khởi động.");
  // Cấu hình tùy chọn (có thể điều chỉnh theo nhu cầu)
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
}

void loop() {
  // Kiểm tra nút bấm để chuyển đổi trạng thái thu thập dữ liệu cử chỉ động
  if (digitalRead(buttonPin) == LOW && (millis() - lastDebounceTime) > debounceDelay) {
    lastDebounceTime = millis();
    collecting = !collecting;
    // Gửi marker "START" hoặc "END" tới server để đánh dấu bắt đầu/kết thúc
    String marker = collecting ? "START" : "END";
    Serial.println(marker);
    // Gửi dữ liệu với marker; giá trị các trường khác không quan trọng ở marker này (gửi 0 làm placeholder)
    sendData(millis(), 0, 0, 0, 0, 0, 0, 0, marker);
    // Chờ cho đến khi nút được thả
    while (digitalRead(buttonPin) == LOW);
  }
  
  // Đọc dữ liệu từ MPU6050
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  // Nếu đang thu thập, gửi dữ liệu cảm biến cùng với marker "DATA"
  if (collecting) {
    sendData(millis(), 
             a.acceleration.x, a.acceleration.y, a.acceleration.z,
             g.gyro.x, g.gyro.y, g.gyro.z,
             temp.temperature, "DATA");
  }
  
  delay(50); // Tốc độ lấy mẫu: 50ms
}

// Hàm gửi dữ liệu đến server qua HTTP GET
void sendData(unsigned long time, float ax, float ay, float az,
              float gx, float gy, float gz, float tempVal, String marker) {
  WiFiClient client;
  if (client.connect(serverHost, serverPort)) {
    // Tạo URL với các tham số truyền theo dạng key-value
    String url = "/predict?";
    url += "t=" + String(time);
    url += "&ax=" + String(ax);
    url += "&ay=" + String(ay);
    url += "&az=" + String(az);
    url += "&gx=" + String(gx);
    url += "&gy=" + String(gy);
    url += "&gz=" + String(gz);
    url += "&temp=" + String(tempVal);
    url += "&marker=" + marker;

    // Xây dựng HTTP GET request
    client.print(String("GET ") + url + " HTTP/1.1\r\n" +
                 "Host: " + serverHost + "\r\n" +
                 "Connection: close\r\n\r\n");
    // Sử dụng ép kiểu chuỗi cho "Đã gửi: " để tránh lỗi
    Serial.println(String("Đã gửi: ") + url);
    
    // Đọc phản hồi từ server (tùy chọn)
    while (client.connected()) {
      if (client.available()){
        String line = client.readStringUntil('\n');
        Serial.println(line);
      }
    }
    client.stop();
  } else {
    Serial.println("Kết nối tới server thất bại.");
  }
}
