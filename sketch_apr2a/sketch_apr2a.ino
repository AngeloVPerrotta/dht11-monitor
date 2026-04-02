#include <DHT.h>
#include <LiquidCrystal_I2C.h>

#define DHTPIN 2
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);
LiquidCrystal_I2C lcd(0x27, 16, 2);

void setup() {
  Serial.begin(9600);
  dht.begin();
  
  lcd.init();
  lcd.backlight();
  
  lcd.setCursor(0, 0);
  lcd.print("  Sensor DHT11  ");
  lcd.setCursor(0, 1);
  lcd.print("  Iniciando...  ");
  delay(2000);
  lcd.clear();
}

void loop() {
  delay(2000);

  float h = dht.readHumidity();
  float t = dht.readTemperature();

  if (isnan(h) || isnan(t)) {
    lcd.setCursor(0, 0);
    lcd.print("  Error sensor  ");
    Serial.println("ERROR");
    return;
  }

  // Mostrar en LCD
  lcd.setCursor(0, 0);
  lcd.print("Temp: ");
  lcd.print(t, 1);
  lcd.print((char)223); // símbolo °
  lcd.print("C   ");

  lcd.setCursor(0, 1);
  lcd.print("Hum:  ");
  lcd.print(h, 1);
  lcd.print("%   ");

  // Mandar al Serial para Python
  Serial.print(t);
  Serial.print(";");
  Serial.println(h);
}