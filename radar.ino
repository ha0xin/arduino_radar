#include <Servo.h>
#include <NewPing.h>
#include <FastLED.h>

#define BAUD_RATE 9600   // 串口通信波特率

#define SERVO_PIN 9      // 舵机控制引脚
#define TRIGGER_PIN 6    // 超声波传感器触发引脚
#define ECHO_PIN 7       // 超声波传感器回波引脚
#define MAX_DISTANCE 200 // 最大距离（单位：厘米）

#define LED_PIN 8        // LED灯环控制引脚
#define NUM_LEDS 12      // LED灯环的数量
#define BRIGHTNESS 32    // LED亮度
#define LED_TYPE WS2812B // LED类型
#define COLOR_ORDER GRB  // LED颜色顺序

Servo myServo;                                      // 创建舵机对象
NewPing sonar(TRIGGER_PIN, ECHO_PIN, MAX_DISTANCE); // 创建超声波传感器对象
CRGB leds[NUM_LEDS];                                // 创建灯环对象

int currentAngle = 90;  // 舵机角度，初始为 90 度
bool isRunning = false; // 是否正在进行连续转动
bool isLightOn = false;  // 是否点亮灯环

uint8_t dist[181] = {0}; // 存储每个角度对应的距离

void setup()
{
  Serial.begin(BAUD_RATE);     // 初始化串口通信
  myServo.attach(SERVO_PIN);   // 连接舵机到指定引脚
  myServo.write(currentAngle); // 设置舵机到初始角度
  delay(1000);                 // 确保舵机已到位

  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS); // 初始化灯环
  FastLED.setBrightness(BRIGHTNESS);                               // 设置灯环亮度
}

void loop()
{
  // 检查串口是否有数据
  if (Serial.available() > 0)
  {
    String command = Serial.readStringUntil('\n'); // 读取命令

    // 处理不同的命令
    if (command.startsWith("A"))
    {
      int angle = command.substring(1).toInt(); // 提取角度值
      if (angle >= 15 && angle <= 165)
      {
        currentAngle = angle;
        myServo.write(currentAngle); // 调整舵机到指定角度
        Serial.print("Angle set to: ");
        Serial.println(currentAngle);
      }
    }
    else if (command == "ONCE")
    {
      moveServoOnce();
    }
    else if (command == "START")
    {
      isRunning = true;
      Serial.println("Continuous movement started.");
    }
    else if (command == "STOP")
    {
      isRunning = false;
      currentAngle = 90;
      myServo.write(currentAngle); // 中立位置
      Serial.println("Movement stopped.");
    }
    else if (command == "LON")
    {
      isLightOn = true;
    }
    else if (command == "LOFF")
    {
      isLightOn = false;
      FastLED.clear();
      FastLED.show();
    }
  }

  // 如果处于“START”模式，舵机会持续来回转动
  if (isRunning)
  {
    moveServoBackAndForth();
  }

  // 对每个角度范围进行平均距离计算，并控制灯环颜色
  if (isLightOn)
  {
    controlLEDsBasedOnDistance();
  }

  delay(100); // 稍微延时，避免过于频繁的串口输出
}

// 控制舵机来回转动一次
void moveServoOnce()
{
  for (int pos = 15; pos <= 165; pos++)
  {
    myServo.write(pos);
    currentAngle = pos; // 更新当前角度
    controlLEDsBasedOnDistance();
    delay(15);
    reportCurrentStatus(); // 每次调整角度后报告状态
  }
  for (int pos = 165; pos >= 15; pos--)
  {
    myServo.write(pos);
    currentAngle = pos; // 更新当前角度
    controlLEDsBasedOnDistance();
    delay(15);
    reportCurrentStatus(); // 每次调整角度后报告状态
  }
  currentAngle = 90;
  myServo.write(currentAngle);
  Serial.println("Completed once movement.");
}

// 控制舵机持续来回转动
void moveServoBackAndForth()
{
  static bool movingForward = true;

  if (movingForward)
  {
    for (int pos = currentAngle; pos <= 165; pos++)
    {
      myServo.write(pos);
      currentAngle = pos;
      controlLEDsBasedOnDistance();
      delay(15);
      reportCurrentStatus();
    }
    movingForward = false;
  }
  else
  {
    for (int pos = 165; pos >= 15; pos--)
    {
      myServo.write(pos);
      currentAngle = pos;
      controlLEDsBasedOnDistance();
      delay(15);
      reportCurrentStatus();
    }
    movingForward = true;
  }
}

// 报告当前角度和距离
void reportCurrentStatus()
{
  unsigned int distance = sonar.ping_cm();
  dist[currentAngle] = distance;
  if (distance > 0)
  {
    Serial.print("(");
    Serial.print(currentAngle);
    Serial.print(",");
    Serial.print(distance);
    Serial.println(")");
  }
}

// 根据距离控制灯环颜色
void controlLEDsBasedOnDistance()
{
  // 每个灯环对应的角度范围
  int angleRanges[5][2] = {
      {135, 165}, {105, 135}, {75, 105}, {45, 75}, {15, 45} // 分别对应灯5到灯9
  };

  for (int i = 0; i < 5; i++)
  {
    int startAngle = angleRanges[i][0];
    int endAngle = angleRanges[i][1];
    float avgDistance = getAverageDistance(startAngle, endAngle);
    int ledIndex = i + 4; // 对应灯环5-9号

    // 如果平均距离小于1米，点亮红灯；否则，点亮绿灯
    if (avgDistance < 100)
    {
      leds[ledIndex] = CRGB::Red; // 红色代表距离小于1米
    }
    else
    {
      leds[ledIndex] = CRGB::Green; // 绿色代表距离大于1米
    }
  }
  FastLED.show(); // 更新灯环状态
}

// 计算角度范围内的平均距离
float getAverageDistance(int startAngle, int endAngle)
{
  long totalDistance = 0;
  int count = 0;

  for (int i = startAngle; i <= endAngle; i++)
  {
    if (dist[i] > 0)
    {
      totalDistance += dist[i];
      count++;
    }
  }

  int avg = totalDistance / count;
  return avg;
}
