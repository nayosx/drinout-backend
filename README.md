# drinout-backend
API for simple in &amp; out movement 


Linux environment

(solo se ejecuta una vez cuando se clona)
python3 -m venv venv

(se ejecuta cada vez que se abre una nueva terminal)
source venv/bin/activate

pip install -r requirements.txt



actualizar el contenedor

docker-compose down

git pull origin main


docker-compose up -d --build




#Cuándo SÍ necesitás --build

Usalo cuando cambiaste algo que afecta la imagen, por ejemplo:

Dockerfile

requirements.txt

versión de Python

librerías (pip install)

variables de entorno definidas en Dockerfile

comandos RUN, COPY, etc.




#Cuándo NO hace falta --build

No lo necesitás cuando solo cambiaste:

archivos .py

lógica Flask

HTML / JSON

configuraciones que entran por env_file

cualquier cosa cubierta por:



docker compose -p drinout-prod -f docker-compose.prod.yml up -d
docker compose -p drinout-dev  -f docker-compose.dev.yml  up -d --build


docker compose -p drinout-dev -f docker-compose.dev.yml down
docker compose -p drinout-prod -f docker-compose.prod.yml down

