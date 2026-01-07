import time
import json
import yaml
import random
import string
import os

# import library ภายนอก
import orjson
import matplotlib.pyplot as plt
import numpy as np
from yaml import CLoader, CDumper

BENCHMARK_RESULTS = {}  # { "Format Name": [ (write_time, read_time, file_size), ... ] }


def generate_data(num_items=5000):
    data = []
    for i in range(num_items):
        data.append({
            "id": i,
            "name": ''.join(random.choices(string.ascii_letters, k=15)),
            "scores": [random.random() for _ in range(10)],
            "metadata": {
                "active": True,
                "tags": ["python", "benchmark", "test"],
                "extra": None
            }
        })
    return data


def run_file_benchmark(label, filename, write_func, read_func, data):
    # 1. ทดสอบการเขียนลงไฟล์ (Write to Disk)
    start_time = time.perf_counter()
    write_func(filename, data)
    dump_time = time.perf_counter() - start_time

    # 2. ทดสอบการอ่านจากไฟล์ (Read from Disk)
    start_time = time.perf_counter()
    _ = read_func(filename)
    load_time = time.perf_counter() - start_time

    # คำนวณขนาดไฟล์
    file_size_mb = os.path.getsize(filename) / (1024 * 1024)

    # แสดงผลทาง Console
    print(f"{label: <25} | Write: {dump_time:.4f} s | Read: {load_time:.4f} s | Size: {file_size_mb:.2f} MB")

    # เก็บผลลัพธ์ลง Global Dict เพื่อนำไปพลอตกราฟ
    if label not in BENCHMARK_RESULTS:
        BENCHMARK_RESULTS[label] = []
    BENCHMARK_RESULTS[label].append((dump_time, load_time, file_size_mb))

    # ลบไฟล์ทิ้งเมื่อเสร็จ
    if os.path.exists(filename):
        os.remove(filename)


def json_std_write(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f)


def json_std_read(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)


def yaml_pure_write(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        yaml.dump(data, f)


def yaml_pure_read(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def yaml_c_write(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, Dumper=CDumper)


def yaml_c_read(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return yaml.load(f, Loader=CLoader)


def orjson_write(filename, data):
    with open(filename, 'wb') as f:
        f.write(orjson.dumps(data))


def orjson_read(filename):
    with open(filename, 'rb') as f:
        return orjson.loads(f.read())


def benchmark():
    print("Creating dummy data...")
    DATA = generate_data(10000)
    print(f"Data size: {len(DATA)} records\n")

    print("-" * 85)
    print(f"{'Format': <25} | {'Write (File)': <15} | {'Read (File)': <15} | {'File Size'}")
    print("-" * 85)

    # 1. Standard JSON
    run_file_benchmark("JSON (Standard)", "test_std.json",
                       json_std_write, json_std_read, DATA)

    # 2. YAML (Pure Python)
    run_file_benchmark("YAML (Pure Python)", "test_pure.yaml",
                       yaml_pure_write, yaml_pure_read, DATA)

    # 3. YAML (C Extension)
    run_file_benchmark("YAML (C Extension)", "test_c.yaml",
                       yaml_c_write, yaml_c_read, DATA)

    # 4. ORJSON (Rust)
    run_file_benchmark("JSON (orjson)", "test_or.json",
                       orjson_write, orjson_read, DATA)

    print("-" * 85)
    print("\n")


def show_graph():
    if not BENCHMARK_RESULTS:
        print("No data to plot.")
        return

    # เตรียมข้อมูล (หาค่าเฉลี่ยจากการรันหลายรอบ)
    labels = list(BENCHMARK_RESULTS.keys())
    avg_write = []
    avg_read = []
    avg_size = []

    for label in labels:
        runs = BENCHMARK_RESULTS[label]
        # หาค่าเฉลี่ยของแต่ละ column (0=write, 1=read, 2=size)
        mean_w = sum(r[0] for r in runs) / len(runs)
        mean_r = sum(r[1] for r in runs) / len(runs)
        mean_s = sum(r[2] for r in runs) / len(runs)

        avg_write.append(mean_w)
        avg_read.append(mean_r)
        avg_size.append(mean_s)

    # ตั้งค่ากราฟ
    x = np.arange(len(labels))
    width = 0.6

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('JSON vs YAML Performance (Lower is Better)', fontsize=16, weight='bold')

    # สี
    colors_time = ['#3498db', '#e74c3c', '#f39c12', '#2ecc71']  # ฟ้า, แดง, ส้ม, เขียว
    colors_size = ['#95a5a6', '#95a5a6', '#95a5a6', '#34495e']

    # Plot 1: Write
    rects1 = ax1.bar(x, avg_write, width, color=colors_time)
    ax1.set_title('Write Speed (Seconds)', fontsize=12, weight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=15, ha='right')
    ax1.grid(axis='y', linestyle='--', alpha=0.5)
    ax1.bar_label(rects1, fmt='%.4fs', padding=3)

    # Plot 2: Read
    rects2 = ax2.bar(x, avg_read, width, color=colors_time)
    ax2.set_title('Read Speed (Seconds)', fontsize=12, weight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=15, ha='right')
    ax2.grid(axis='y', linestyle='--', alpha=0.5)
    ax2.bar_label(rects2, fmt='%.4fs', padding=3)

    # Plot 3: Size
    rects3 = ax3.bar(x, avg_size, width, color=colors_size)
    ax3.set_title('File Size (MB)', fontsize=12, weight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(labels, rotation=15, ha='right')
    ax3.set_ylim(0, max(avg_size) * 1.2)
    ax3.grid(axis='y', linestyle='--', alpha=0.5)
    ax3.bar_label(rects3, fmt='%.2f MB', padding=3)

    plt.tight_layout()
    plt.subplots_adjust(top=0.88)
    print("Displaying Graph...")
    plt.show()


if __name__ == "__main__":
    benchmark()
    benchmark()
    benchmark()
    show_graph()
