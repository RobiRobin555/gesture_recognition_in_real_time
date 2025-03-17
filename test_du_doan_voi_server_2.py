from flask import Flask, request, jsonify
import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.models import load_model
import time

app = Flask(__name__)

# Đảm bảo sử dụng backend tương tác (nếu chưa set, comment lệnh matplotlib.use('Agg'))
# import matplotlib
# matplotlib.use('TkAgg')

MAX_LEN = 100  # phải khớp với huấn luyện

model = load_model("gesture_model.keras")
current_sequence = []

@app.route('/predict', methods=['GET'])
def predict():
    global current_sequence
    marker = request.args.get("marker", "").upper()
    
    if marker == "START":
        current_sequence = []
        return jsonify({"status": "Gesture started"})
    
    elif marker == "DATA":
        try:
            ax = float(request.args.get("ax", 0))
            ay = float(request.args.get("ay", 0))
            az = float(request.args.get("az", 0))
            gx = float(request.args.get("gx", 0))
            gy = float(request.args.get("gy", 0))
            gz = float(request.args.get("gz", 0))
        except Exception as e:
            return jsonify({"error": "Invalid sensor data", "details": str(e)}), 400

        current_sequence.append([ax, ay, az, gx, gy, gz])
        return jsonify({"status": "Data received"})
    
    elif marker == "END":
        # Đợi thêm một chút để đảm bảo dữ liệu đã gửi xong
        time.sleep(0.1)
        
        if not current_sequence:
            return jsonify({"error": "No data collected"}), 400

        seq = np.array(current_sequence, dtype=np.float32)
        if seq.shape[0] < MAX_LEN:
            pad_len = MAX_LEN - seq.shape[0]
            pad_array = np.zeros((pad_len, seq.shape[1]))
            seq = np.concatenate([seq, pad_array], axis=0)
        else:
            seq = seq[:MAX_LEN, :]
        seq_expanded = np.expand_dims(seq, axis=0)
        pred = model.predict(seq_expanded)
        predicted_label = int(np.argmax(pred, axis=1)[0])
        print("Predicted Label:", predicted_label)
        
        # Hiển thị biểu đồ trực tiếp trên màn hình
        create_and_show_plot(seq, predicted_label)
        
        # Reset dữ liệu
        current_sequence = []
        return jsonify({"predicted_label": predicted_label})
    
    else:
        return jsonify({"error": "Invalid marker"}), 400

def create_and_show_plot(seq, predicted_label):
    t = np.arange(seq.shape[0])
    fig, axs = plt.subplots(2, 1, figsize=(10, 8))
    
    axs[0].plot(t, seq[:, 0], label='AccelX')
    axs[0].plot(t, seq[:, 1], label='AccelY')
    axs[0].plot(t, seq[:, 2], label='AccelZ')
    axs[0].set_title("Accelerometer Data")
    axs[0].legend()
    
    axs[1].plot(t, seq[:, 3], label='GyroX')
    axs[1].plot(t, seq[:, 4], label='GyroY')
    axs[1].plot(t, seq[:, 5], label='GyroZ')
    axs[1].set_title("Gyroscope Data")
    axs[1].legend()
    
    fig.suptitle(f"Predicted Gesture: {predicted_label}")
    
    plt.ion()      # Chế độ tương tác
    plt.show()
    plt.pause(3)   # Hiển thị 3 giây
    plt.close(fig)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
