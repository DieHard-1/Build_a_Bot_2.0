#include <Wire.h>
#include <Adafruit_VL53L0X.h>
#include <AccelStepper.h>

// Define I2C Pins for ESP32
#define SDA_PIN 21
#define SCL_PIN 22

// Stepper Motor Pins
#define motorPin1 18
#define motorPin2 19
#define motorPin3 23
#define motorPin4 5

// Stepper Motor Setup
AccelStepper stepper(AccelStepper::FULL4WIRE, motorPin1, motorPin3, motorPin2, motorPin4);
const int stepsPerRevolution = 2048;  // 360-degree rotation (make sure this is correct for your motor)
int targetPosition = 0;  // Initial target position (start at 0)


// VL53L0X Sensor
Adafruit_VL53L0X lox = Adafruit_VL53L0X();

void setup() {
    Serial.begin(115200);
    Wire.begin(SDA_PIN, SCL_PIN);  // Initialize I2C for ESP32

    Serial.println("VL53L0X Lidar + Stepper Motor");

    if (!lox.begin()) {
        Serial.println("Failed to initialize VL53L0X sensor!");
        while (1);
    }

    // Increase the speed and acceleration for faster rotation
    stepper.setMaxSpeed(5000);         // Max speed (steps per second) - Increased for faster motion
    stepper.setAcceleration(5000);     // Acceleration (steps per second^2) - Increased for faster ramp-up
    stepper.moveTo(targetPosition);    // Set the initial target position
}

void loop() {
    VL53L0X_RangingMeasurementData_t measure;

    // Move the stepper motor towards the target position
    stepper.run();

    // Read distance from the VL53L0X sensor
    lox.rangingTest(&measure, false);

    // Calculate the angle based on current position of the stepper motor
    float angle = (360.0 / stepsPerRevolution) * stepper.currentPosition();
    Serial.print(angle);  // Output angle
    Serial.print(",");
    if (measure.RangeStatus != 4) {  // If reading is valid
        Serial.println(measure.RangeMilliMeter);  // Output distance in mm
    } else {
        Serial.println(",-1");  // Send -1 for invalid readings
    }

    // Check if the motor has reached the target position
    if (stepper.distanceToGo() == 0) {
        // Reverse direction when we reach 0 or 360 degrees
        if (targetPosition == 0) {
            targetPosition = stepsPerRevolution - 1;  // Move to 360 degrees
            Serial.println("Moving to 360 degrees");
        } else if (targetPosition == stepsPerRevolution - 1) {
            targetPosition = 0;  // Move to 0 degrees
            Serial.println("Moving to 0 degrees");
        }

        // Set the new target position only after reaching the previous target
        stepper.moveTo(targetPosition);
    }

    delay(10);  // Small delay for stability
}
