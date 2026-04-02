# Monitor Ambiental DHT11

Un sistema completo de monitoreo de temperatura y humedad en tiempo real, construido con un sensor físico conectado a un Arduino y una interfaz web que muestra los datos en vivo, predice tendencias y detecta anomalías usando inteligencia artificial.

Clock en la imagen para ver la demo en YouTube 🡻🡻🡻
[![Ver demo en YouTube](https://img.youtube.com/vi/uRBfHxHXQX0/maxresdefault.jpg)](https://www.youtube.com/watch?v=uRBfHxHXQX0)

---

## ¿Cómo funciona?

El sistema arranca desde el mundo físico: un sensor DHT11 mide continuamente la temperatura y la humedad del ambiente. Ese sensor está conectado a una placa Arduino, que lee los valores cada dos segundos y los envía por cable USB a la computadora, como si estuviera "hablando" a través del puerto serial.

En la computadora hay un script de Python escuchando ese cable. Cada vez que llegan nuevos datos, los valida, los guarda en una base de datos local y también los registra en un archivo de respaldo en formato CSV. Al mismo tiempo, compara los valores contra umbrales configurables: si la temperatura supera los 35 °C o la humedad cae por debajo del 30%, genera una alerta y la guarda también en la base de datos.

Una vez que los datos están guardados, dos servidores web los ponen a disposición a través de una API REST. El primero es un servidor ligero en Flask que alimenta al dashboard con el historial de las últimas 24 horas. El segundo es un servidor más completo en FastAPI que ofrece endpoints adicionales, incluyendo predicción de temperatura con machine learning y detección de anomalías estadísticas.

Finalmente, el dashboard, que es una página web que se abre directo en el navegador, consulta esos servidores cada pocos segundos y actualiza los gráficos, las métricas y los indicadores en tiempo real, sin necesidad de recargar la página.

---

## ¿Qué muestra el dashboard?

**Métricas superiores fijas:** Cuatro tarjetas que siempre están visibles aunque hagas scroll. Muestran la temperatura actual, la humedad actual, el promedio histórico de temperatura y el total de lecturas acumuladas en la base de datos. Se actualizan cada cinco segundos.

**Gráfico de temperatura (últimas 24 horas):** Una línea naranja que traza cómo fue variando la temperatura a lo largo del día. El eje vertical siempre va de 0 a 50 °C para que sea fácil comparar lecturas entre distintos momentos.

**Gráfico de humedad (últimas 24 horas):** Lo mismo pero para la humedad, con el eje vertical fijo entre 0 y 100%.

**Gráfico de predicción:** Muestra dos líneas sobre el mismo eje. La naranja sólida representa los últimos 20 valores reales medidos por el sensor. La línea blanca punteada proyecta cómo seguiría la temperatura en los próximos 10 puntos según el modelo de inteligencia artificial. Se actualiza cada 30 segundos.

**Gráfico de anomalías:** Muestra la curva de temperatura con los puntos normales en naranja. Los puntos que el sistema considera anómalos aparecen marcados con un círculo rojo más grande. Debajo del título se lee en texto el promedio, el desvío estándar y el rango dentro del cual un valor se considera normal.

**Tabla de alertas:** Lista las últimas alertas registradas con hora, tipo, valor medido y umbral superado. Las alertas de temperatura tienen fondo rojo suave y las de humedad fondo amarillo suave. Si no hay alertas, muestra un mensaje indicándolo.

**Panel de estado del sistema:** Cinco tarjetas resumen al pie del dashboard. Indican si el sensor está conectado o sin señal (basándose en cuándo fue la última lectura), la temperatura más alta del día, la humedad más alta del día, cuántas lecturas se tomaron en las últimas 24 horas y cuántas alertas hay registradas en total.

---

## Inteligencia artificial

**Predicción de temperatura:** El sistema toma los últimos 100 registros de temperatura y aplica una regresión lineal, que es una técnica que busca la tendencia general de los datos trazando la línea recta que mejor los representa. Con esa línea, extrapola los próximos 10 puntos futuros. No predice el futuro con certeza absoluta, pero sí da una idea muy útil de hacia dónde va la temperatura si las condiciones se mantienen similares.

**Detección de anomalías:** El sistema calcula el promedio y el desvío estándar de los últimos 200 registros. El desvío estándar mide qué tan dispersos están los valores respecto al promedio. Si un valor está a más del doble de ese desvío por encima o por debajo del promedio, se considera anómalo. Por ejemplo, si el promedio es 27 °C y el desvío es 1 °C, cualquier lectura menor a 25 °C o mayor a 29 °C queda marcada como anomalía. Esto permite detectar automáticamente picos o caídas inusuales sin configurar umbrales manuales.

---

## Tecnologías utilizadas

**Arduino:** La placa microcontroladora que lee el sensor físico DHT11 y envía los datos en crudo a la computadora por USB.

**Python:** El lenguaje central del proyecto. Se usa para recibir los datos del Arduino, procesarlos, guardarlos y correr los dos servidores de la API.

**SQLite:** La base de datos embebida donde se almacenan todas las lecturas y alertas. No requiere instalación separada ni servidor de base de datos.

**Flask:** El servidor web ligero que expone los datos históricos al dashboard. Maneja las rutas de datos del día y las estadísticas generales.

**FastAPI:** El servidor web más completo que ofrece todos los endpoints avanzados, incluyendo historial paginado, predicción con machine learning y detección de anomalías. Genera documentación interactiva de la API de forma automática.

**scikit-learn y NumPy:** Las librerías de Python usadas para el machine learning. NumPy maneja los arrays numéricos y scikit-learn ejecuta el modelo de regresión lineal para las predicciones.

**Chart.js:** La librería de JavaScript que dibuja todos los gráficos del dashboard directamente en el navegador, sin necesidad de imágenes ni software externo.

**HTML, CSS y JavaScript:** El frontend completo del dashboard. Todo en un único archivo, sin frameworks ni herramientas de compilación.

---

## Requisitos para correrlo

Necesitás tener instalado Python en tu computadora. Las librerías necesarias son Flask, FastAPI, Uvicorn, pyserial, NumPy y scikit-learn, todas instalables desde la terminal con el gestor de paquetes de Python.

Para la parte del hardware necesitás una placa Arduino (Uno o compatible), un sensor DHT11 y un cable USB para conectar el Arduino a la computadora. El Arduino tiene que tener cargado el sketch correspondiente que lee el sensor y envía los datos por serial, y hay que asegurarse de que el número de puerto COM configurado en el script de Python coincide con el que usa el Arduino en tu sistema.

El dashboard no requiere instalación de ningún servidor web: se abre directamente en cualquier navegador moderno como archivo local, siempre que los dos servidores de Python estén corriendo.

---

## Autor

**Angelo Perrotta** — [github.com/AngeloVPerrotta](https://github.com/AngeloVPerrotta)
