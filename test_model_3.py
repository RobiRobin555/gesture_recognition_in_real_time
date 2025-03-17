import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from tensorflow.keras import layers, models
from scikeras.wrappers import KerasClassifier  # Sử dụng scikeras
import tensorflow as tf

# -------------------------------
# Bước 1: Đọc và tách chuỗi dữ liệu từ file CSV
# -------------------------------
def load_sequences_from_csv(csv_path):
    df = pd.read_csv(csv_path)
    
    sequences = []
    labels = []
    current_seq = []
    current_label = None
    
    for idx, row in df.iterrows():
        marker = str(row['Marker']).strip().upper()
        label = row['Label']
        
        if marker == 'START':
            if pd.isna(label):
                print(f"Cảnh báo: Thiếu nhãn ở dòng {idx}. Bỏ qua chuỗi này.")
                current_seq = []
                current_label = None
                continue
            current_seq = []
            current_label = label
        elif marker == 'DATA':
            sample = [
                row['AccelX'],
                row['AccelY'],
                row['AccelZ'],
                row['GyroX'],
                row['GyroY'],
                row['GyroZ']
            ]
            current_seq.append(sample)
        elif marker == 'END':
            if len(current_seq) > 0 and current_label is not None:
                sequences.append(current_seq)
                labels.append(current_label)
            current_seq = []
            current_label = None
    return sequences, labels

csv_path = 'gesture_data.csv'
sequences, labels = load_sequences_from_csv(csv_path)
print("Số chuỗi thu được:", len(sequences))

# -------------------------------
# Bước 2: Padding các chuỗi về độ dài cố định
# -------------------------------
def pad_sequences_custom(sequences, max_len):
    padded = []
    for seq in sequences:
        seq = np.array(seq)
        if len(seq) < max_len:
            pad_len = max_len - len(seq)
            pad_array = np.zeros((pad_len, seq.shape[1]))
            seq = np.concatenate([seq, pad_array], axis=0)
        else:
            seq = seq[:max_len, :]
        padded.append(seq)
    return np.array(padded, dtype=np.float32)

MAX_LEN = 100  # Ví dụ: 100 mẫu cho mỗi chuỗi
X = pad_sequences_custom(sequences, MAX_LEN)
labels = [int(l) for l in labels]
y = np.array(labels, dtype=int)

print("X shape:", X.shape)  # (num_sequences, MAX_LEN, 6)
print("y shape:", y.shape)

# -------------------------------
# Bước 3: Chia dữ liệu thành tập huấn luyện và kiểm tra (cho huấn luyện ban đầu)
# -------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# -------------------------------
# Bước 4: Hàm tạo mô hình LSTM (sử dụng sparse_categorical_crossentropy)
# -------------------------------
num_classes = 10

def create_model():
    model = models.Sequential()
    model.add(layers.Masking(mask_value=0., input_shape=(MAX_LEN, 6)))
    model.add(layers.LSTM(64))
    model.add(layers.Dense(32, activation='relu'))
    model.add(layers.Dense(num_classes, activation='softmax'))
    
    model.compile(optimizer='adam',
                  loss='sparse_categorical_crossentropy',  # Sử dụng loss này cho nhãn dạng int
                  metrics=['accuracy'])
    return model

# Xây dựng và huấn luyện mô hình ban đầu
model = create_model()
model.summary()

history = model.fit(
    X_train, y_train,
    validation_split=0.2,
    epochs=20,
    batch_size=32
)

y_pred_prob = model.predict(X_test)
y_pred = np.argmax(y_pred_prob, axis=1)

print("Test Accuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:\n", classification_report(y_test, y_pred))
print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))




model.save("gesture_model.keras")
