import math
import time
import tkinter
from collections import defaultdict
from queue import Queue
from threading import Thread

from serial import *


PORT = "COM4"
BAUDRATE = 9600
ser = Serial(PORT, BAUDRATE, timeout=0)

point_data = defaultdict(list)  # {angle: [(x, y, size, timestamp), ...]}
FADE_DURATION = 5.0  # Points take 5 seconds to fade completely
MIN_POINT_SIZE = 1
MAX_POINT_SIZE = 8
MAX_DISTANCE = 200

running = True

time.sleep(1)

def read_serial_worker(data_queue):
    while running:
        try:
            line = ser.readline()
            if line:
                data_str = line.decode('utf-8').strip()
                if data_str.startswith('('):
                    try:
                        tuple_obj = eval(data_str)
                        angle = int(tuple_obj[0])
                        distance = int(tuple_obj[1])
                        print(f"Angle: {angle}, Distance: {distance}")
                        data_queue.put((angle, distance))
                    except (ValueError, SyntaxError):
                        print(f"Invalid tuple format: {data_str}")
                else:
                    print(f"Debug message: {data_str}")
        except:
            print("Serial read error")
        time.sleep(0.01)

width = 500
height = 350
# 初始化一个tk
t = tkinter.Tk()
t.title("Radar演示程序")  # 窗口标题名

# 创建一个LabelFrame组件作为方框
frame = tkinter.LabelFrame(t, text="Angle & Distance", padx=5, pady=5)
frame.pack(fill="both", expand=True)  # 在窗口中放置方框并设置外部填充

# 创建标签用于显示角度
angle_label = tkinter.Label(frame, text="Current Angle: ", font=("Helvetica", 16))
angle_label.pack()

# 创建标签用于显示距离
distance_label = tkinter.Label(frame, text="Distance: ", font=("Helvetica", 16)) 
distance_label.pack()

# 创建一个LabelFrame组件作为方框
frame1 = tkinter.LabelFrame(t, text="Lights & Servo", padx=5, pady=5)
frame1.pack(side="left", fill="both", expand=True)  # 在窗口中放置方框

def lighton():
    ser.write(b'LON\n')
def lightoff():
    ser.write(b'LOFF\n')
def start_scan():
    ser.write(b'START\n')
def stop_scan():
    ser.write(b'STOP\n')
def on_slider_move(val):
    angle = int(float(val))
    command = f"A{angle}\n".encode()
    ser.write(command)


# 控制灯的按钮
button1 = tkinter.Button(frame1, text="lights on", font=("Helvetica", 16), command=lighton)
button2 = tkinter.Button(frame1, text="lights off", font=("Helvetica", 16), command=lightoff)
button3 = tkinter.Button(frame1, text="start", font=("Helvetica", 16), command=start_scan)
button4 = tkinter.Button(frame1, text="stop", font=("Helvetica", 16), command=stop_scan)
button1.pack()
button2.pack()
button3.pack()
button4.pack()
# 控制舵机的滑块
slider = tkinter.Scale(frame1, from_=0, to=180, orient=tkinter.HORIZONTAL, command=on_slider_move)
slider.pack()
# 更新标签文本的函数
def update_labels(an, dis):
    current_angle = an
    current_distance = dis
    angle_label.config(text=f"Current Angle: {current_angle}°")
    distance_label.config(text=f"Distance: {current_distance} cm")
    


# 定义一个画布，大小，背景颜色
canvas = tkinter.Canvas(width=width, height=height, bg='black')
canvas.pack()  # 居中挂起
x = int(width / 2)
y = int(3 * height / 4)
r = 50
point_stack =[]
running = True  # 控制扫描的标志

# 画布，圆点坐标，半径r，线条颜色
def circle(canvas, x, y, r, outline):
    canvas.create_arc(x - r, y - r, x + r, y + r, start=0, extent=180, style='arc', outline=outline)
# 渲染逐渐熄灭的亮点
def fade_light():
    global point_stack
    res = []
    while point_stack:
        pos, cur = point_stack.pop()
        grey_value = int(255 * (cur / 8))
        new_outline = f'#{grey_value:02x}{grey_value:02x}{grey_value:02x}'
        #绘制亮点
        l = 1
        canvas.create_oval(pos[0] - l*cur, pos[1] - l*cur, pos[0] + l*cur, pos[1] + l*cur, outline=new_outline, fill=new_outline)
        if cur >= 2:
            res.append((pos, cur-1))
    point_stack = res

# 扇形初始化角度
delta = 15

def Draw():
    global running, point_data
    
    while running:
        current_time = time.time()
        canvas.delete('all')
        
        # Draw static elements
        for i in range(0, 4):
            circle(canvas, x, y, r * (i + 1), outline='green')
        canvas.create_line(x, y - 200, x, y, width=1, fill='white')
        canvas.create_line(x - 200, y, x + 200, y, width=1, fill='white')
        
        # Process any new data
        try:
            while not data_queue.empty():
                cur_angle, distance = data_queue.get_nowait()
                update_labels(cur_angle, distance)
                if 1 <= distance <= MAX_DISTANCE:
                    d = distance/MAX_DISTANCE * 200
                    canvas.create_arc(x + 200, y + 200, x - 200, y - 200, 
                                   start=int(cur_angle-delta/2), extent=delta, fill="green")
                    angle_rad = math.radians(cur_angle)
                    x1 = x + int(d * math.cos(angle_rad))
                    y1 = y - int(d * math.sin(angle_rad))
                    
                    # Remove old points at this angle
                    angle_key = int(cur_angle)
                    point_data[angle_key] = [(x1, y1, MAX_POINT_SIZE, current_time)]
        except:
            pass
            
        # Render all stored points with fading
        for angle in list(point_data.keys()):
            updated_points = []
            for px, py, size, timestamp in point_data[angle]:
                age = current_time - timestamp
                if age < FADE_DURATION:
                    # Calculate fade
                    fade_factor = 1 - (age / FADE_DURATION)
                    current_size = max(MIN_POINT_SIZE, size * fade_factor)
                    grey_value = int(255 * fade_factor)
                    color = f'#{grey_value:02x}{grey_value:02x}{grey_value:02x}'
                    
                    # Draw point
                    canvas.create_oval(
                        px - current_size, 
                        py - current_size,
                        px + current_size, 
                        py + current_size,
                        outline=color,
                        fill=color
                    )
                    updated_points.append((px, py, size, timestamp))
            
            if updated_points:
                point_data[angle] = updated_points
            else:
                del point_data[angle]
        
        # Draw labels
        canvas.create_text(x + 220, y, text='E', fill='red', font=('Arial', 20))
        canvas.create_text(x - 220, y, text='W', fill='red', font=('Arial', 20))
        canvas.create_text(x, y - 220, text='N', fill='red', font=('Arial', 20))
        canvas.create_text(x + 210, y + 20, text=f'{MAX_DISTANCE}cm', fill='white', font=('Arial', 15))
        canvas.create_text(x + 100, y + 20, text=f'{MAX_DISTANCE//2}cm', fill='white', font=('Arial', 15))
        canvas.create_text(x, y + 40, text="雷达图", fill="white", font=('微软雅黑', 20))
        
        canvas.update()
        time.sleep(0.05)

def on_closing():
    global running
    running = False
    t.destroy()


# Modify the main section
if __name__ == '__main__':
    # Create a queue for thread communication
    data_queue = Queue()
    
    # Start the serial reader thread
    serial_thread = Thread(target=read_serial_worker, args=(data_queue,), daemon=True)
    serial_thread.start()
    
    # Setup window closing handler
    t.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start drawing in the main thread
    Draw()
    
    # Start the main loop
    t.mainloop()